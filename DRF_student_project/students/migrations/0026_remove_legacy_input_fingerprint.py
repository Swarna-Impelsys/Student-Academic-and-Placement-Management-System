
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0025_eligibilitycheck_checked_by_and_more"),
    ]

    operations = [
        # Preserve old fingerprint values in the current model field.
        migrations.RunSQL(
            sql="""
                UPDATE students_eligibilitycheck
                SET source_fingerprint = input_fingerprint
                WHERE source_fingerprint = ''
                  AND input_fingerprint <> '';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # Remove the obsolete database column.
        migrations.RunSQL(
            sql="""
                ALTER TABLE students_eligibilitycheck
                DROP COLUMN input_fingerprint;
            """,
            reverse_sql="""
                ALTER TABLE students_eligibilitycheck
                ADD COLUMN input_fingerprint varchar(64) NOT NULL DEFAULT '';

                UPDATE students_eligibilitycheck
                SET input_fingerprint = source_fingerprint;
            """,
        ),
    ]
