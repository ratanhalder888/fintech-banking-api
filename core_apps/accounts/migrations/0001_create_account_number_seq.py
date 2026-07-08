from django.db import migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="CREATE SEQUENCE IF NOT EXISTS account_number_seq START WITH 1;",
            reverse_sql="DROP SEQUENCE IF EXISTS account_number_seq;",
        ),
    ]
