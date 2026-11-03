
import { useEffect, useState } from 'react';
import {
    getJobs,
    createJob,
    updateJob,
    deleteJob,
    getEligibleStudents,
    sendEligibleJobNotification,
} from '../services/jobService';
import { getPlacementDrives } from '../services/placementDriveService';
import { getCourses } from '../services/studentService';
import './Jobs.css';

const initialForm = {
    placement_drive: '',
    title: '',
    description: '',
    job_type: '',
    location: '',
    salary: '',
    vacancies: '1',
    minimum_age: '',
    minimum_marks: '',
    minimum_attendance: '',
    required_course: '',
    required_skills: [],
    maximum_backlogs: '0',
    is_active: true,
};

function Jobs() {
    const role = (localStorage.getItem('role') || '').trim().toLowerCase();

    const [jobs, setJobs] = useState([]);
    const [drives, setDrives] = useState([]);
    const [courses, setCourses] = useState([]);

    const [form, setForm] = useState(initialForm);
    const [editingId, setEditingId] = useState(null);
    const [skillInput, setSkillInput] = useState('');

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [eligibleData, setEligibleData] = useState(null);
    const [eligibleLoading, setEligibleLoading] = useState(false);
    const [eligibleLoadingJobId, setEligibleLoadingJobId] = useState(null);
    const [eligibleError, setEligibleError] = useState('');

    const [selectedStudentIds, setSelectedStudentIds] = useState([]);
    const [sendingNotification, setSendingNotification] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    function getErrorMessage(err) {
        const data = err.response?.data;

        if (!data) {
            return 'Unable to complete the request. Check your connection and API.';
        }

        if (typeof data === 'string') {
            return data;
        }

        if (Array.isArray(data)) {
            return data.join(', ');
        }

        return Object.entries(data)
            .map(([field, messages]) => {
                const message = Array.isArray(messages)
                    ? messages.join(', ')
                    : typeof messages === 'object' && messages !== null
                        ? JSON.stringify(messages)
                        : messages;

                return `${field}: ${message}`;
            })
            .join(' | ');
    }

    function getList(data) {
        if (Array.isArray(data)) {
            return data;
        }

        if (Array.isArray(data?.results)) {
            return data.results;
        }

        return [];
    }

    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const [jobData, driveData, courseData] = await Promise.all([
                getJobs(),
                getPlacementDrives(),
                getCourses(),
            ]);

            setJobs(getList(jobData));
            setDrives(getList(driveData));
            setCourses(getList(courseData));
            return true;
        } catch (err) {
            setError(getErrorMessage(err));
            return false;
        } finally {
            setLoading(false);
        }
    }

    async function handleViewEligibleStudents(jobId) {
        setEligibleData(null);
        setEligibleError('');
        setSelectedStudentIds([]);
        setNotificationMessage('');
        setEligibleLoadingJobId(jobId);
        setEligibleLoading(true);

        try {
            const data = await getEligibleStudents(jobId);
            setEligibleData(data);
        } catch (err) {
            setEligibleError(getErrorMessage(err));
        } finally {
            setEligibleLoading(false);
            setEligibleLoadingJobId(null);
        }
    }

    // Normalize IDs so that 5 and "5" are treated as the same ID.
    function handleStudentSelection(studentId, checked) {
        const numericId = Number(studentId);

        if (
            !Number.isFinite(numericId) ||
            studentId === '' ||
            studentId === null ||
            studentId === undefined
        ) {
            return;
        }

        setSelectedStudentIds((previous) => {
            const normalizedPrevious = previous.map(Number);

            if (checked) {
                return normalizedPrevious.includes(numericId)
                    ? normalizedPrevious
                    : [...normalizedPrevious, numericId];
            }

            return normalizedPrevious.filter((id) => id !== numericId);
        });

        setNotificationMessage('');
    }

    // Get valid numeric IDs from the eligible-student response.
    const eligibleStudents = eligibleData?.eligible_students || [];

    const eligibleStudentIds = eligibleStudents
        .map((student) => student.student_id)
        .filter((id) => id !== null && id !== undefined && id !== '')
        .map(Number)
        .filter(Number.isFinite);

    function handleSelectAllEligible(checked) {
        setSelectedStudentIds(
            checked
                ? [...new Set(eligibleStudentIds)]
                : []
        );

        setNotificationMessage('');
    }

    async function handleSendNotifications() {
        if (!eligibleData?.job_id || selectedStudentIds.length === 0) {
            setNotificationMessage('Select at least one eligible student.');
            return;
        }

        setSendingNotification(true);
        setNotificationMessage('');
        setEligibleError('');

        try {
            const response = await sendEligibleJobNotification(
                eligibleData.job_id,
                selectedStudentIds
            );

            const sentCount =
                response?.notifications_sent ??
                response?.sent_count ??
                response?.count;

            setNotificationMessage(
                typeof sentCount === 'number'
                    ? `Job notification sent to ${sentCount} student(s).`
                    : response?.message || 'Job notifications sent successfully.'
            );
        } catch (err) {
            setEligibleError(getErrorMessage(err));
        } finally {
            setSendingNotification(false);
        }
    }

    function handleChange(event) {
        const { name, value, type, checked } = event.target;
        setForm((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    }

    function handleAddSkill() {
        const skillName = skillInput.trim();
        if (!skillName) return;

        if (form.required_skills.includes(skillName)) {
            setSkillInput('');
            return;
        }

        setForm((previous) => ({
            ...previous,
            required_skills: [...previous.required_skills, skillName],
        }));

        setSkillInput('');
        setError('');
    }

    // Remove a skill from the selected list.
    function handleRemoveSkill(skillName) {
        setForm((previous) => ({
            ...previous,
            required_skills: previous.required_skills.filter(
                (skill) => skill !== skillName
            ),
        }));
    }

    // Allow Enter key to add a skill.
    function handleSkillInputKeyDown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            handleAddSkill();
        }
    }

    function resetForm() {
        setForm(initialForm);
        setSkillInput('');
        setEditingId(null);
        setError('');
        setSuccess('');
    }

    function startEdit(job) {
        setForm({
            placement_drive: String(
                job.placement_drive?.id ?? job.placement_drive ?? ''
            ),
            title: job.title || '',
            description: job.description || '',
            job_type: job.job_type || '',
            location: job.location || '',
            salary: String(job.salary ?? ''),
            vacancies: String(job.vacancies ?? 1),
            minimum_age: job.minimum_age ?? '',
            minimum_marks: job.minimum_marks ?? '',
            minimum_attendance: job.minimum_attendance ?? '',
            required_course: job.required_course
                ? String(job.required_course?.id ?? job.required_course)
                : '',
            required_skills: (job.required_skills_details || []).map(
                (skill) => skill.name
            ),
            maximum_backlogs: String(job.maximum_backlogs ?? 0),
            is_active: job.is_active,
        });

        setSkillInput('');
        setEditingId(job.id);
        setError('');
        setSuccess('');

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function validateForm() {
        if (form.salary === '' || Number(form.salary) <= 0) {
            return 'Salary must be greater than 0.';
        }

        if (
            !Number.isInteger(Number(form.vacancies)) ||
            Number(form.vacancies) <= 0
        ) {
            return 'Vacancies must be a positive whole number.';
        }

        if (
            form.minimum_age !== '' &&
            (!Number.isInteger(Number(form.minimum_age)) ||
                Number(form.minimum_age) <= 0)
        ) {
            return 'Minimum age must be a positive whole number.';
        }

        return '';
    }

    function courseName(id) {
        if (!id) return 'Any course';

        const courseId = id?.id ?? id;

        const course = courses.find(
            (item) => String(item.id) === String(courseId)
        );

        return course
            ? course.name || course.course_name || 'Unknown Course'
            : 'Any course';
    }

    // Get the placement drive name using its ID.
    function driveName(id) {
        if (!id) return 'No placement drive';

        const driveId = id?.id ?? id;

        const drive = drives.find(
            (item) => String(item.id) === String(driveId)
        );

        return drive
            ? drive.name || drive.title || drive.company_name || 'Unknown Drive'
            : 'No placement drive';
    }

    function skillNames(skillDetails = []) {
        if (!skillDetails.length) {
            return 'Any skill';
        }

        return skillDetails
            .map((skill) => skill.name)
            .filter(Boolean)
            .join(', ') || 'Any skill';
    }

    async function handleSubmit(event) {
        event.preventDefault();

        const validationMessage = validateForm();

        if (validationMessage) {
            setError(validationMessage);
            setSuccess('');
            return;
        }

        setSaving(true);
        setError('');
        setSuccess('');

        const wasEditing = editingId !== null;

        try {
            const payload = {
                ...form,
                placement_drive: form.placement_drive
                    ? Number(form.placement_drive)
                    : null,
                salary: Number(form.salary),
                vacancies: Number(form.vacancies),
                minimum_age: form.minimum_age === ''
                    ? null
                    : Number(form.minimum_age),
                minimum_marks: form.minimum_marks === ''
                    ? null
                    : Number(form.minimum_marks),
                minimum_attendance: form.minimum_attendance === ''
                    ? null
                    : Number(form.minimum_attendance),
                required_course: form.required_course
                    ? Number(form.required_course)
                    : null,
                required_skills: form.required_skills,
                maximum_backlogs: Number(form.maximum_backlogs),
            };

            if (wasEditing) {
                await updateJob(editingId, payload);
            } else {
                await createJob(payload);
            }

            const refreshed = await loadData();

            resetForm();
            if (refreshed) {
                setSuccess(
                    wasEditing
                        ? 'Job updated successfully.'
                        : 'Job added successfully.'
                );
            } else {
                setSuccess(
                    'Job saved successfully, but the job list could not be refreshed.'
                );
            }
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(job) {
        if (!window.confirm(`Delete job "${job.title}"?`)) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            await deleteJob(job.id);

            const refreshed = await loadData();

            if (refreshed) {
                setSuccess('Job deleted successfully.');
            } else {
                setSuccess(
                    'Job was deleted successfully, but the job list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            setError(getErrorMessage(err));
        }
    }

    const visibleJobs =
        role === 'student'
            ? jobs.filter((job) => job.is_active)
            : jobs;

    const allEligibleSelected =
        eligibleStudentIds.length > 0 &&
        eligibleStudentIds.every((id) =>
            selectedStudentIds.includes(id)
        );

    return (
        <div className="jobs-page">
            {role === 'admin' && (
                <section className="management-card job-form-card">
                    <div className="card-heading">
                        <h3>
                            {editingId !== null ? 'Edit Job' : 'Add New Job'}
                        </h3>
                    </div>

                    <form onSubmit={handleSubmit} className="job-form">
                        {error && (
                            <div className="alert alert-error">{error}</div>
                        )}

                        {success && (
                            <div className="alert alert-success">{success}</div>
                        )}

                        <div className="job-fields-grid">
                            <div className="form-field">
                                <label htmlFor="title">Job Title</label>
                                <input
                                    id="title"
                                    name="title"
                                    type="text"
                                    value={form.title}
                                    onChange={handleChange}
                                    required
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="placement_drive">
                                    Placement Drive
                                </label>
                                <select
                                    id="placement_drive"
                                    name="placement_drive"
                                    value={form.placement_drive}
                                    onChange={handleChange}
                                >
                                    <option value="">Select drive</option>
                                    {drives.map((drive) => (
                                        <option key={drive.id} value={drive.id}>
                                            {drive.name ||
                                                drive.title ||
                                                drive.company_name ||
                                                'Drive'}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div className="field-group">
                                <label htmlFor="job_type">Job Type</label>
                                <select
                                    id="job_type"
                                    name="job_type"
                                    value={form.job_type}
                                    onChange={handleChange}
                                >
                                    <option value="">Select type</option>
                                    <option value="Full Time">Full Time</option>
                                    <option value="Part Time">Part Time</option>
                                    <option value="Internship">Internship</option>
                                    <option value="Contract">Contract</option>
                                </select>
                            </div>

                            <div className="field-group">
                                <label htmlFor="location">Location</label>
                                <input
                                    id="location"
                                    name="location"
                                    type="text"
                                    value={form.location}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="salary">Salary</label>
                                <input
                                    id="salary"
                                    name="salary"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={form.salary}
                                    onChange={handleChange}
                                    required
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="vacancies">Vacancies</label>
                                <input
                                    id="vacancies"
                                    name="vacancies"
                                    type="number"
                                    min="1"
                                    step="1"
                                    value={form.vacancies}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="minimum_age">Minimum Age</label>
                                <input
                                    id="minimum_age"
                                    name="minimum_age"
                                    type="number"
                                    min="1"
                                    step="1"
                                    value={form.minimum_age}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="minimum_marks">
                                    Minimum Marks
                                </label>
                                <input
                                    id="minimum_marks"
                                    name="minimum_marks"
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="1"
                                    value={form.minimum_marks}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="minimum_attendance">
                                    Minimum Attendance
                                </label>
                                <input
                                    id="minimum_attendance"
                                    name="minimum_attendance"
                                    type="number"
                                    min="0"
                                    max="100"
                                    step="1"
                                    value={form.minimum_attendance}
                                    onChange={handleChange}
                                />
                            </div>

                            <div className="field-group">
                                <label htmlFor="required_course">
                                    Required Course
                                </label>
                                <select
                                    id="required_course"
                                    name="required_course"
                                    value={form.required_course}
                                    onChange={handleChange}
                                >
                                    <option value="">Any course</option>
                                    {courses.map((course) => (
                                        <option
                                            key={course.id}
                                            value={course.id}
                                        >
                                            {course.name ||
                                                course.course_name ||
                                                'Course'}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {editingId !== null && (
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={resetForm}
                                    disabled={saving}
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>
                </section>
            )}

            <section className="management-card job-list-card">
                <div className="card-heading">
                    <h3>Jobs</h3>
                </div>

                {error && role !== 'admin' && (
                    <div className="alert alert-error">{error}</div>
                )}

                {success && role !== 'admin' && (
                    <div className="alert alert-success">{success}</div>
                )}

                {loading ? (
                    <p className="jobs-message">Loading jobs...</p>
                ) : visibleJobs.length === 0 ? (
                    <div className="empty-state">No jobs found.</div>
                ) : (
                    <div className="job-cards-list">
                        {visibleJobs.map((job) => (
                            <article className="job-item-card" key={job.id}>
                                <div className="job-item-top">
                                    <div className="job-item-title">
                                        <h4>{job.title}</h4>

                                        <span
                                            className={
                                                job.is_active
                                                    ? 'company-status active'
                                                    : 'company-status inactive'
                                            }
                                        >
                                            {job.is_active
                                                ? 'Active'
                                                : 'Inactive'}
                                        </span>
                                    </div>

                                    <span className="job-item-type">
                                        {job.job_type || '—'}
                                    </span>
                                </div>

                                <p className="job-item-drive">
                                    {driveName(job.placement_drive)}
                                </p>

                                <div className="job-item-details">
                                    <span>
                                        <strong>Location:</strong>{' '}
                                        {job.location || '—'}
                                    </span>

                                    <span>
                                        <strong>Salary:</strong>{' '}
                                        {Number(job.salary).toLocaleString(
                                            'en-IN',
                                            {
                                                minimumFractionDigits: 2,
                                                maximumFractionDigits: 2,
                                            }
                                        )}
                                    </span>

                                    <span>
                                        <strong>Vacancies:</strong>{' '}
                                        {job.vacancies}
                                    </span>

                                    <span>
                                        <strong>Course:</strong>{' '}
                                        {courseName(job.required_course)}
                                    </span>
                                </div>

                                <div className="job-item-actions">
                                    {role === 'admin' && (
                                        <>
                                            <button
                                                type="button"
                                                className="btn btn-edit"
                                                onClick={() => startEdit(job)}
                                            >
                                                Edit
                                            </button>

                                            <button
                                                type="button"
                                                className="btn btn-delete"
                                                onClick={() => handleDelete(job)}
                                            >
                                                Delete
                                            </button>
                                        </>
                                    )}

                                    {role === 'teacher' && (
                                        <button
                                            type="button"
                                            className="btn btn-primary"
                                            onClick={() =>
                                                handleViewEligibleStudents(job.id)
                                            }
                                            disabled={eligibleLoading}
                                        >
                                            {eligibleLoading &&
                                            String(eligibleLoadingJobId) ===
                                                String(job.id)
                                                ? 'Loading...'
                                                : 'View Eligible Students'}
                                        </button>
                                    )}
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </section>

            {role === 'teacher' &&
                (eligibleLoading || eligibleError || eligibleData) && (
                    <section className="management-card">
                        <div className="card-heading">
                            <h3>Eligible Students Who Haven't Applied</h3>

                            {eligibleData && (
                                <p>
                                    {eligibleData.job_title}
                                    {' — '}
                                    {eligibleData.total_eligible_students ??
                                        eligibleStudents.length}
                                    {' eligible student(s)'}
                                </p>
                            )}
                        </div>

                        {eligibleLoading && (
                            <p>Loading eligible students...</p>
                        )}

                        {eligibleError && (
                            <div className="alert alert-error">
                                {eligibleError}
                            </div>
                        )}

                        {notificationMessage && (
                            <div className="alert alert-success">
                                {notificationMessage}
                            </div>
                        )}

                        {!eligibleLoading && eligibleData && (
                            eligibleStudents.length === 0 ? (
                                <div className="empty-state">
                                    No eligible students who haven't applied were found.
                                </div>
                            ) : (
                                <>
                                    <div className="form-actions">
                                        <button
                                            type="button"
                                            className="btn btn-secondary"
                                            onClick={() =>
                                                handleSelectAllEligible(
                                                    !allEligibleSelected
                                                )
                                            }
                                        >
                                            {allEligibleSelected
                                                ? 'Deselect All'
                                                : 'Select All'}
                                        </button>

                                        <button
                                            type="button"
                                            className="btn btn-primary"
                                            onClick={handleSendNotifications}
                                            disabled={
                                                sendingNotification ||
                                                selectedStudentIds.length === 0
                                            }
                                        >
                                            {sendingNotification
                                                ? 'Sending...'
                                                : `Send Job Details (${selectedStudentIds.length})`}
                                        </button>
                                    </div>

                                    <div className="table-container">
                                        <table className="management-table">
                                            <thead>
                                                <tr>
                                                    <th>
                                                        <input
                                                            type="checkbox"
                                                            aria-label="Select all eligible students"
                                                            checked={allEligibleSelected}
                                                            onChange={(event) =>
                                                                handleSelectAllEligible(
                                                                    event.target.checked
                                                                )
                                                            }
                                                        />
                                                    </th>
                                                    <th>Student ID</th>
                                                    <th>Student Name</th>
                                                    <th>Email</th>
                                                    <th>Course</th>
                                                    <th>Eligibility Reason</th>
                                                </tr>
                                            </thead>

                                            <tbody>
                                                {eligibleStudents.map(
                                                    (student) => {
                                                        const studentId = Number(
                                                            student.student_id
                                                        );

                                                        return (
                                                            <tr
                                                                key={student.student_id}
                                                            >
                                                                <td>
                                                                    <input
                                                                        type="checkbox"
                                                                        aria-label={`Select ${student.student_name}`}
                                                                        checked={
                                                                            Number.isFinite(
                                                                                studentId
                                                                            ) &&
                                                                            selectedStudentIds.includes(
                                                                                studentId
                                                                            )
                                                                        }
                                                                        onChange={(
                                                                            event
                                                                        ) =>
                                                                            handleStudentSelection(
                                                                                student.student_id,
                                                                                event.target.checked
                                                                            )
                                                                        }
                                                                    />
                                                                </td>
                                                                <td>
                                                                    {student.student_id}
                                                                </td>
                                                                <td>
                                                                    {student.student_name}
                                                                </td>
                                                                <td>
                                                                    {student.email}
                                                                </td>
                                                                <td>
                                                                    {student.course}
                                                                </td>
                                                                <td>
                                                                    {student.reason ||
                                                                        'Meets the job eligibility criteria.'}
                                                                </td>
                                                            </tr>
                                                        );
                                                    }
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )
                        )}
                    </section>
                )}
        </div>
    );
}

export default Jobs;
