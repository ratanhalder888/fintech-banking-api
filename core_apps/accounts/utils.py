import secrets
from os import getenv
from typing import Union, List
from django.db import transaction, IntegrityError
from .emails import send_account_creation_email
from .models import BankAccount
from django.db import connection


def get_next_sequence_value() -> int:
    with connection.cursor() as cursor:
        cursor.execute("SELECT NEXTVAL('account_number_seq');")
        return cursor.fetchone()[0]


def generate_account_number(currency: str) -> str:

    bank_code = getenv("BANK_CODE", "123")
    branch_code = getenv("BANK_BRANCH_CODE", "456")
    currency_codes = {
        "us_dollar": getenv("CURRENCY_CODE_USD", "01"),
        "pound": getenv("CURRENCY_CODE_GBP", "02"),
        "taka": getenv("CURRENCY_CODE_BDT", "03"),
    }
    currency_code = currency_codes.get(currency)

    if not currency_code:
        raise ValueError(f"Invalid currency: {currency}")
    
    prefix = f"{bank_code}{branch_code}{currency_code}"
    remaining_digits = 16 - len(prefix) - 1

    next_id = get_next_sequence_value()
    sequence_digits = str(next_id).zfill(remaining_digits)
    
    if len(sequence_digits) > remaining_digits:
        raise RuntimeError("Account number pool exhausted")
    
    partial_account_number = f"{prefix}{sequence_digits}"
    check_digit = calculate_luhn_check_digit(partial_account_number)
    
    return f"{partial_account_number}{check_digit}"


def calculate_luhn_check_digit(number: str) -> int:
    def split_into_digits(n: Union[str, int]) -> List[int]:
        return [int(digit) for digit in str(n)]

    digits = split_into_digits(number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)

    for d in even_digits:
        doubled = d * 2
        total += sum(split_into_digits(doubled))

    return (10 - (total % 10)) % 10


def create_bank_account(user, currency: str, account_type: str) -> BankAccount:
    """Create a BankAccount with a guaranteed-unique sequence-based account number."""

    with transaction.atomic():
        # NEXTVAL guarantees uniqueness — no collision check needed
        account_number = generate_account_number(currency)

        # select_for_update prevents race when two requests see no accounts
        bank_accounts_exist = (
            BankAccount.objects
            .filter(user=user)
            .select_for_update()
            .exists()
        )
        is_primary = not bank_accounts_exist

        bank_account = BankAccount.objects.create(
            user=user,
            account_number=account_number,
            currency=currency,
            account_type=account_type,
            is_primary=is_primary,
        )

    # Email OUTSIDE atomic block — SMTP failure won't roll back the account
    transaction.on_commit(
        lambda: send_account_creation_email(user, bank_account)
    )

    return bank_account


def maybe_create_bank_account(profile, photos_pending: bool = False) -> str:
    """Create bank account when profile is complete. Returns user-facing message."""
    if not profile.is_complete_with_next_of_kin():
        if photos_pending:
            return (
                "Profile updated. Photos are uploading — bank account will be "
                "created shortly."
            )
        return (
            "Profile updated successfully. Please complete all required "
            "fields and at least one next of kin to create a bank account."
        )

    if not profile.account_currency or not profile.account_type:
        return (
            "Profile updated successfully. Please choose an account currency "
            "and type to create a bank account."
        )

    existing = BankAccount.objects.filter(
        user=profile.user,
        currency=profile.account_currency,
        account_type=profile.account_type,
    ).exists()
    if existing:
        return (
            "Profile updated successfully. No new account created as one "
            "already exists for this currency and type."
        )

    try:
        create_bank_account(
            profile.user,
            currency=profile.account_currency,
            account_type=profile.account_type,
        )
    except IntegrityError:
        # concurrent create won the race — unique_together guard
        return (
            "Profile updated successfully. No new account created as one "
            "already exists for this currency and type."
        )

    return (
        "Profile updated and new bank account created successfully. An email "
        "has been sent to you with further instructions"
    )