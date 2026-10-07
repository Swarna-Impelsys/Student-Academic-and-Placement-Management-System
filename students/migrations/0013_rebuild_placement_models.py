from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0012_job_maximum_backlogs_job_required_course_and_more"),
    ]

    operations = [

        # ---------------------------------------------------------
        # 1. Rebuild the actual database tables
        # ---------------------------------------------------------

        migrations.SeparateDatabaseAndState(

            database_operations=[

                # Delete old tables.
                # They contain zero records, so no placement data is lost.
                migrations.RunSQL(
                    sql=[
                        "DROP TABLE IF EXISTS students_eligibilitycheck;",
                        "DROP TABLE IF EXISTS students_job_required_skills;",
                        "DROP TABLE IF EXISTS students_job;",
                        "DROP TABLE IF EXISTS students_placementdrive;",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),

                # -------------------------------------------------
                # PlacementDrive
                # -------------------------------------------------

                migrations.CreateModel(
                    name="PlacementDrive",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "title",
                            models.CharField(max_length=150),
                        ),
                        (
                            "description",
                            models.TextField(
                                blank=True,
                                null=True,
                            ),
                        ),
                        (
                            "drive_date",
                            models.DateField(),
                        ),
                        (
                            "application_start_date",
                            models.DateField(),
                        ),
                        (
                            "application_end_date",
                            models.DateField(),
                        ),
                        (
                            "location",
                            models.CharField(max_length=200),
                        ),
                        (
                            "is_active",
                            models.BooleanField(default=True),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "company",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="placement_drives",
                                to="students.company",
                            ),
                        ),
                    ],
                ),

                # -------------------------------------------------
                # Job
                # -------------------------------------------------

                migrations.CreateModel(
                    name="Job",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "title",
                            models.CharField(max_length=150),
                        ),
                        (
                            "description",
                            models.TextField(
                                blank=True,
                                null=True,
                            ),
                        ),
                        (
                            "job_type",
                            models.CharField(max_length=50),
                        ),
                        (
                            "location",
                            models.CharField(max_length=200),
                        ),
                        (
                            "salary",
                            models.DecimalField(
                                max_digits=10,
                                decimal_places=2,
                            ),
                        ),
                        (
                            "vacancies",
                            models.PositiveIntegerField(default=1),
                        ),
                        (
                            "minimum_age",
                            models.PositiveIntegerField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "minimum_marks",
                            models.FloatField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "minimum_attendance",
                            models.FloatField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "is_active",
                            models.BooleanField(default=True),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "maximum_backlogs",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "placement_drive",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="jobs",
                                to="students.placementdrive",
                            ),
                        ),
                        (
                            "required_course",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="jobs",
                                null=True,
                                blank=True,
                                to="students.course",
                            ),
                        ),
                    ],
                ),

                # -------------------------------------------------
                # Job <-> Skill ManyToMany table
                # -------------------------------------------------

                migrations.AddField(
                    model_name="job",
                    name="required_skills",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="jobs",
                        to="students.skill",
                    ),
                ),

                # -------------------------------------------------
                # EligibilityCheck
                # -------------------------------------------------

                migrations.CreateModel(
                    name="EligibilityCheck",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "is_eligible",
                            models.BooleanField(),
                        ),
                        (
                            "reason",
                            models.TextField(),
                        ),
                        (
                            "checked_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "student",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="eligibility_checks",
                                to="students.student",
                            ),
                        ),
                        (
                            "job",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="eligibility_checks",
                                to="students.job",
                            ),
                        ),
                    ],
                ),
            ],

            # ---------------------------------------------------------
            # 2. Make Django's migration STATE match models.py
            # ---------------------------------------------------------

            state_operations=[

                # Remove the old Job definition from migration state.
                migrations.DeleteModel(
                    name="Job",
                ),

                # Remove the old EligibilityCheck definition.
                migrations.DeleteModel(
                    name="EligibilityCheck",
                ),

                # PlacementDrive did not exist in current migration state,
                # so we create its correct state directly.
                migrations.CreateModel(
                    name="PlacementDrive",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "title",
                            models.CharField(max_length=150),
                        ),
                        (
                            "description",
                            models.TextField(
                                blank=True,
                                null=True,
                            ),
                        ),
                        (
                            "drive_date",
                            models.DateField(),
                        ),
                        (
                            "application_start_date",
                            models.DateField(),
                        ),
                        (
                            "application_end_date",
                            models.DateField(),
                        ),
                        (
                            "location",
                            models.CharField(max_length=200),
                        ),
                        (
                            "is_active",
                            models.BooleanField(default=True),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "company",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="placement_drives",
                                to="students.company",
                            ),
                        ),
                    ],
                ),

                # Correct Job state.
                migrations.CreateModel(
                    name="Job",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "title",
                            models.CharField(max_length=150),
                        ),
                        (
                            "description",
                            models.TextField(
                                blank=True,
                                null=True,
                            ),
                        ),
                        (
                            "job_type",
                            models.CharField(max_length=50),
                        ),
                        (
                            "location",
                            models.CharField(max_length=200),
                        ),
                        (
                            "salary",
                            models.DecimalField(
                                max_digits=10,
                                decimal_places=2,
                            ),
                        ),
                        (
                            "vacancies",
                            models.PositiveIntegerField(default=1),
                        ),
                        (
                            "minimum_age",
                            models.PositiveIntegerField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "minimum_marks",
                            models.FloatField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "minimum_attendance",
                            models.FloatField(
                                null=True,
                                blank=True,
                            ),
                        ),
                        (
                            "is_active",
                            models.BooleanField(default=True),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "maximum_backlogs",
                            models.PositiveIntegerField(default=0),
                        ),
                        (
                            "placement_drive",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="jobs",
                                to="students.placementdrive",
                            ),
                        ),
                        (
                            "required_course",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name="jobs",
                                null=True,
                                blank=True,
                                to="students.course",
                            ),
                        ),
                    ],
                ),

                migrations.AddField(
                    model_name="job",
                    name="required_skills",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="jobs",
                        to="students.skill",
                    ),
                ),

                # Correct EligibilityCheck state.
                migrations.CreateModel(
                    name="EligibilityCheck",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "is_eligible",
                            models.BooleanField(),
                        ),
                        (
                            "reason",
                            models.TextField(),
                        ),
                        (
                            "checked_at",
                            models.DateTimeField(auto_now_add=True),
                        ),
                        (
                            "student",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="eligibility_checks",
                                to="students.student",
                            ),
                        ),
                        (
                            "job",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="eligibility_checks",
                                to="students.job",
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ]