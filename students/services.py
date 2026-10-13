from .models import Skill


def check_student_eligibility(student, job):

    reasons = []

    # AGE
    if job.minimum_age is not None:
        if student.Age < job.minimum_age:
            reasons.append(
                f"Minimum age required is {job.minimum_age}."
            )

    # ACADEMIC RECORDS
    academic_records = student.academic_records.all()

    # MARKS
    if job.minimum_marks is not None:

        if not academic_records.exists():
            reasons.append("No academic records found.")

        else:
            average_marks = (
                sum(record.marks for record in academic_records)
                / academic_records.count()
            )

            if average_marks < job.minimum_marks:
                reasons.append(
                    f"Minimum marks required are {job.minimum_marks}. "
                    f"Student average is {average_marks:.2f}."
                )

    # ATTENDANCE
    if job.minimum_attendance is not None:

        if not academic_records.exists():

            if "No academic records found." not in reasons:
                reasons.append("No academic records found.")

        else:
            average_attendance = (
                sum(record.attendance for record in academic_records)
                / academic_records.count()
            )

            if average_attendance < job.minimum_attendance:
                reasons.append(
                    f"Minimum attendance required is "
                    f"{job.minimum_attendance}. "
                    f"Student average is {average_attendance:.2f}."
                )

    # COURSE
    if job.required_course is not None:

        if student.Course_id != job.required_course_id:
            reasons.append(
                f"Required course is {job.required_course.name}."
            )

    # SKILLS
    required_skills = job.required_skills.all()

    if required_skills.exists():

        student_skill_ids = set(
            student.skills.values_list("id", flat=True)
        )

        required_skill_ids = set(
            required_skills.values_list("id", flat=True)
        )

        missing_skill_ids = required_skill_ids - student_skill_ids

        if missing_skill_ids:

            missing_skills = Skill.objects.filter(
                id__in=missing_skill_ids
            )

            missing_skill_names = ", ".join(
                skill.name for skill in missing_skills
            )

            reasons.append(
                f"Missing required skills: {missing_skill_names}."
            )

    # BACKLOG
    if job.maximum_backlogs is not None:

        backlog_count = academic_records.filter(backlog=True).count()

        if backlog_count > job.maximum_backlogs:
            reasons.append(
                f"Maximum allowed backlogs are "
                f"{job.maximum_backlogs}. "
                f"Student has {backlog_count}."
            )

    # FINAL RESULT
    if reasons:
        return {
            "is_eligible": False,
            "reason": " ".join(reasons)
        }

    return {
        "is_eligible": True,
        "reason": "Student satisfies all eligibility requirements."
    }
