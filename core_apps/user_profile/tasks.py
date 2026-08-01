from uuid import UUID

import cloudinary.exceptions
import cloudinary.uploader
from celery import shared_task
from celery.exceptions import Retry
from django.apps import apps
from django.core.files.storage import default_storage
from loguru import logger

from core_apps.accounts.utils import maybe_create_bank_account


@shared_task(
    name="upload_photos_to_cloudinary",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
)
def upload_photos_to_cloudinary(self, profile_id: UUID, photos: dict) -> None:
    profile_model = apps.get_model("user_profile", "Profile")
    profile = profile_model.objects.get(id=profile_id)
    try:
        for field_name, photo_data in photos.items():
            with default_storage.open(photo_data["name"], "rb") as image_file:
                try:
                    response = cloudinary.uploader.upload(image_file)
                except cloudinary.exceptions.Error as exc:
                    # keep all temp files for retry — delete only after full success
                    self.retry(exc=exc)
            setattr(profile, field_name, response["public_id"])
            setattr(profile, f"{field_name}_url", response["url"])
        profile.save()

        # all uploaded — now safe to delete temp files
        for photo_data in photos.values():
            try:
                default_storage.delete(photo_data["name"])
            except Exception:
                pass

        logger.info(f"Photos for  {profile.user.email}'s uploaded successfully")

        message = maybe_create_bank_account(profile)
        logger.info(f"Account creation for {profile.user.email}: {message}")

    except Retry:
        raise
    except Exception as e:
        logger.error(f"Failed to upload photos for profile {profile_id}: {str(e)} ")

        # final failure — delete any remaining temp files
        for photo_data in photos.values():
            try:
                if default_storage.exists(photo_data["name"]):
                    default_storage.delete(photo_data["name"])
            except Exception:
                pass


@shared_task(name="cleanup_stale_temp_files")
def cleanup_stale_temp_files(max_age_hours: int = 24) -> int:
    """Sweep temp/ for orphaned files older than max_age_hours (rollback orphans)."""
    from datetime import timedelta

    from django.utils import timezone

    cutoff = timezone.now() - timedelta(hours=max_age_hours)
    deleted = 0

    def walk(path: str) -> None:
        nonlocal deleted
        dirs, files = default_storage.listdir(path)
        for f in files:
            name = path + f
            try:
                if default_storage.get_modified_time(name) < cutoff:
                    default_storage.delete(name)
                    deleted += 1
            except Exception:
                pass
        for d in dirs:
            walk(path + d + "/")

    try:
        walk("temp/")
    except Exception:
        pass
    logger.info(f"Cleaned {deleted} stale temp files")
    return deleted
