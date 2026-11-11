
import { useEffect, useState } from 'react';
import {
    getInterviews,
    createInterview,
    updateInterview,
    deleteInterview,
    uploadInterviewShortlist,
    extractInterviewShortlist,
    sendInterviewNotifications,
    getInterviewShortlistUploads,
} from '../services/interviewService';
import { getApplications } from '../services/applicationService';
import { getStudents } from '../services/studentService';
import { getJobs } from '../services/jobService';
import '../App.css';

const emptyForm = {
    application: '',
    interview_date: '',
    interview_time: '',
    interview_type: 'online',
    location: '',
    meeting_link: '',
    status: 'scheduled',
    feedback: '',
};

function getList(data, key) {
    if (Array.isArray(data)) return data;
    return data?.results || data?.[key] || data?.data || [];
}

function Interviews() {
    // Role-based UI permissions
    const role = localStorage.getItem('role')?.trim().toLowerCase();

    const canManageInterviews = role === 'admin';
    const isRegistrationOfficer = role === 'registration officer';
    const isStudent = role === 'student';

    const [interviews, setInterviews] = useState([]);
    const [applications, setApplications] = useState([]);
    const [students, setStudents] = useState([]);
    const [jobs, setJobs] = useState([]);

    const [form, setForm] = useState(emptyForm);
    const [editingId, setEditingId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Interview shortlist states
    const [shortlistUploads, setShortlistUploads] = useState([]);
    const [selectedFile, setSelectedFile] = useState(null);
    const [selectedJob, setSelectedJob] = useState('');
    const [uploading, setUploading] = useState(false);
    const [extractingUploadId, setExtractingUploadId] = useState(null);
    const [sendingUploadId, setSendingUploadId] = useState(null);
    const [selectedInterviewIds, setSelectedInterviewIds] = useState({});

    // Load interviews and related data
    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const [
                interviewData,
                applicationData,
                studentData,
                jobData,
                uploadData,
            ] = await Promise.all([
                getInterviews(),
                getApplications(),

                // Students must not fetch the complete student list.
                isStudent
                    ? Promise.resolve([])
                    : getStudents(),

                getJobs(),

                canManageInterviews || isRegistrationOfficer
                    ? getInterviewShortlistUploads()
                    : Promise.resolve([]),
            ]);

            setInterviews(getList(interviewData, 'interviews'));
            setApplications(getList(applicationData, 'applications'));
            setStudents(getList(studentData, 'students'));
            setJobs(getList(jobData, 'jobs'));
            setShortlistUploads(getList(uploadData, 'uploads'));

            return true;

        } catch (err) {
            console.error(
                'Interview loading error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Could not load interview data. Check your backend and login.'
            );

            return false;

        } finally {
            setLoading(false);
        }
    }

    async function handleShortlistUpload(event) {
        event.preventDefault();

        if (!selectedFile || !selectedJob) {
            setError('Please select a job and an Excel file.');
            return;
        }

        setError('');
        setSuccess('');
        setUploading(true);

        try {
            const formData = new FormData();

            formData.append('file', selectedFile);
            formData.append('job', selectedJob);

            await uploadInterviewShortlist(formData);

            setSelectedFile(null);
            setSelectedJob('');

            // Clear the actual file input.
            event.target.reset();

            await loadData();

            setSuccess(
                'Interview shortlist uploaded successfully. No notifications have been sent yet.'
            );
        } catch (err) {
            console.error(
                'Shortlist upload error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.error ||
                'Could not upload the interview shortlist.'
            );
        } finally {
            setUploading(false);
        }
    }

    // Extract all applications from an uploaded shortlist.
    async function handleExtractShortlist(uploadId) {
        setError('');
        setSuccess('');
        setExtractingUploadId(uploadId);

        try {
            const response = await extractInterviewShortlist(uploadId);

            await loadData();

            setSuccess(
                `Shortlist extracted successfully. ${
                    response.shortlisted_count || 0
                } students shortlisted. ${
                    response.rejected_count || 0
                } applications rejected.`
            );
        } catch (err) {
            console.error(
                'Shortlist extraction error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.error ||
                'Could not extract the interview shortlist.'
            );
        } finally {
            setExtractingUploadId(null);
        }
    }

    // Send interview notifications to selected students.
    async function handleSendNotifications(uploadId) {
        const selectedIds = selectedInterviewIds[uploadId] || [];

        if (selectedIds.length === 0) {
            setError('Please select at least one student.');
            return;
        }

        setError('');
        setSuccess('');
        setSendingUploadId(uploadId);

        try {
            const response = await sendInterviewNotifications(
                uploadId,
                selectedIds
            );

            setSuccess(
                `Notifications processed. Sent: ${response.created_count || 0}. ` +
                `Already notified: ${response.duplicate_count || 0}. ` +
                `Skipped: ${response.skipped_count || 0}.`
            );

            setSelectedInterviewIds((previous) => ({
                ...previous,
                [uploadId]: [],
            }));

            await loadData();
        } catch (err) {
            console.error(
                'Send notification error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.error ||
                'Could not send interview notifications.'
            );
        } finally {
            setSendingUploadId(null);
        }
    }

    // Keep selected interview IDs separate for each uploaded Excel file.
    function handleInterviewSelection(uploadId, interviewId, checked) {
        setSelectedInterviewIds((previous) => {
            const currentIds = previous[uploadId] || [];

            return {
                ...previous,
                [uploadId]: checked
                    ? [...currentIds, interviewId]
                    : currentIds.filter((id) => id !== interviewId),
            };
        });
    }

    useEffect(() => {
        loadData();
    }, []);

    function handleChange(event) {
        const { name, value } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: value,
            ...(name === 'interview_type'
                ? {
                    location:
                        value === 'online' ? '' : previous.location,
                    meeting_link:
                        value === 'offline' ? '' : previous.meeting_link,
                }
                : {}),
        }));
    }

    function resetForm() {
        setForm(emptyForm);
        setEditingId(null);
    }

    function getErrorMessage(err) {
        const data = err.response?.data;

        if (!data) {
            return 'Could not save the interview. Please try again.';
        }

        if (typeof data === 'string') {
            return data;
        }

        return Object.entries(data)
            .map(([field, messages]) => {
                const message = Array.isArray(messages)
                    ? messages.join(', ')
                    : typeof messages === 'object'
                        ? JSON.stringify(messages)
                        : String(messages);

                return `${field}: ${message}`;
            })
            .join(' | ') || 'Could not save the interview. Please try again.';
    }

    async function handleSubmit(event) {
        event.preventDefault();

        // Only Admin can create or update interviews.
        if (!canManageInterviews) {
            setError('You do not have permission to manage interviews.');
            return;
        }

        setError('');
        setSuccess('');

        if (form.interview_type === 'online' && !form.meeting_link.trim()) {
            setError('Meeting link is required for an online interview.');
            return;
        }

        if (form.interview_type === 'offline' && !form.location.trim()) {
            setError('Location is required for an offline interview.');
            return;
        }

        const payload = {
            application: Number(form.application),
            interview_date: form.interview_date,
            interview_time: form.interview_time,
            interview_type: form.interview_type,
            location: form.location.trim() || null,
            meeting_link: form.meeting_link.trim() || null,
            status: form.status,
            feedback: form.feedback.trim() || null,
        };

        setSaving(true);

        try {
            const wasEditing = editingId !== null;

            // First, save the interview.
            if (wasEditing) {
                await updateInterview(editingId, payload);
            } else {
                await createInterview(payload);
            }

            // The save request succeeded.
            resetForm();

            // Refresh the interview data separately.
            const refreshed = await loadData();

            if (refreshed) {
                setSuccess(
                    wasEditing
                        ? 'Interview updated successfully.'
                        : 'Interview scheduled successfully.'
                );
            } else {
                setSuccess(
                    wasEditing
                        ? 'Interview was updated successfully, but the interview list could not be refreshed. Please refresh the page.'
                        : 'Interview was scheduled successfully, but the interview list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            console.error(
                'Interview save error:',
                err.response?.data || err
            );

            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    function startEdit(interview) {
        if (!canManageInterviews) return;

        setEditingId(interview.id);

        setForm({
            application: String(interview.application ?? ''),
            interview_date: interview.interview_date || '',
            interview_time: interview.interview_time?.slice(0, 5) || '',
            interview_type: interview.interview_type || 'online',
            location: interview.location || '',
            meeting_link: interview.meeting_link || '',
            status: interview.status || 'scheduled',
            feedback: interview.feedback || '',
        });

        setError('');
        setSuccess('');

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function handleDelete(id) {
        if (!canManageInterviews) return;

        if (!window.confirm('Are you sure you want to delete this interview?')) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            // First, delete the interview.
            await deleteInterview(id);

            if (editingId === id) {
                resetForm();
            }

            // Refresh separately so a refresh failure does not
            // make a successful delete look unsuccessful.
            const refreshed = await loadData();

            if (refreshed) {
                setSuccess('Interview deleted successfully.');
            } else {
                setSuccess(
                    'Interview was deleted successfully, but the interview list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Could not delete this interview.'
            );
        }
    }

    // Display the correct application label based on the logged-in role.
    function getApplicationLabel(application) {
        const job = jobs.find(
            (item) => String(item.id) === String(application.job)
        );

        const jobTitle = job?.title || `Job #${application.job}`;

        // Student only needs to see their own application details.
        if (isStudent) {
            return `Your Application — ${jobTitle} (Application #${application.id})`;
        }

        const student = students.find(
            (item) => String(item.id) === String(application.student)
        );

        const studentName =
            student?.Name ||
            student?.name ||
            `Student #${application.student}`;

        return `${studentName} — ${jobTitle} (Application #${application.id})`;
    }

    function getApplicationDetails(applicationId) {
        const application = applications.find(
            (item) => String(item.id) === String(applicationId)
        );

        return application
            ? getApplicationLabel(application)
            : `Application #${applicationId}`;
    }

    function statusClass(status) {
        return `interview-status interview-status-${String(
            status || ''
        ).toLowerCase()}`;
    }

    return (
        <div className="interviews-page">
            <div className="interviews-header">
                <div>
                    <h2>Interview Management</h2>
                    <p>
                        {canManageInterviews
                            ? 'Schedule interviews and track their progress.'
                            : 'View your permitted interview schedules and details.'}
                    </p>
                </div>

                <div className="interviews-count">
                    <span>Total interviews</span>
                    <strong>{interviews.length}</strong>
                </div>
            </div>

            {error && (
                <div
                    className="interviews-alert interviews-alert-error"
                    role="alert"
                >
                    {error}
                </div>
            )}

            {success && (
                <div
                    className="interviews-alert interviews-alert-success"
                    role="status"
                >
                    {success}
                </div>
            )}

            {/* Only Admin can upload interview shortlist Excel files. */}
            {canManageInterviews && (
                <section className="interviews-card">
                    <h3>Upload Interview Shortlist</h3>

                    <form
                        className="interviews-form"
                        onSubmit={handleShortlistUpload}
                    >
                        <div className="interviews-field interviews-field-wide">
                            <label htmlFor="shortlist-job">
                                Select Job
                            </label>

                            <select
                                id="shortlist-job"
                                value={selectedJob}
                                onChange={(event) => setSelectedJob(event.target.value)}
                                required
                            >
                                <option value="">Select a job</option>

                                {jobs.map((job) => (
                                    <option key={job.id} value={job.id}>
                                        {job.title}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="interviews-field interviews-field-wide">
                            <label htmlFor="shortlist-file">
                                Excel File (.xlsx or .xls)
                            </label>

                            <input
                                id="shortlist-file"
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={(event) =>
                                    setSelectedFile(event.target.files?.[0] || null)
                                }
                                required
                            />
                        </div>

                        <div className="interviews-actions interviews-field-wide">
                            <button
                                type="submit"
                                disabled={uploading || !selectedFile || !selectedJob}
                            >
                                {uploading ? 'Uploading...' : 'Upload Shortlist'}
                            </button>
                        </div>
                    </form>
                </section>
            )}

            {/* Uploaded interview shortlist files */}
            {(canManageInterviews || isRegistrationOfficer) && (
                <section className="interviews-card">
                    <h3>Uploaded Interview Shortlists</h3>

                    {shortlistUploads.length === 0 ? (
                        <p className="interviews-empty">
                            No interview shortlist files uploaded yet.
                        </p>
                    ) : (
                        <div className="interviews-table-wrapper">
                            <table className="interviews-table">
                                <thead>
                                    <tr>
                                        <th>Upload ID</th>
                                        <th>File</th>
                                        <th>Job</th>
                                        <th>Status</th>
                                        {isRegistrationOfficer && <th>Action</th>}
                                    </tr>
                                </thead>

                                <tbody>
                                    {shortlistUploads.map((upload) => {
                                        const job = jobs.find(
                                            (item) =>
                                                String(item.id) === String(upload.job)
                                        );

                                        return (
                                            <tr key={upload.id}>
                                                <td>#{upload.id}</td>

                                                <td>
                                                    {upload.file
                                                        ? upload.file.split('/').pop()
                                                        : 'Excel file'}
                                                </td>

                                                <td>
                                                    {job?.title || `Job #${upload.job}`}
                                                </td>

                                                <td>{upload.status}</td>

                                                {isRegistrationOfficer && (
                                                    <td>
                                                        <button
                                                            type="button"
                                                            onClick={() =>
                                                                handleExtractShortlist(upload.id)
                                                            }
                                                            disabled={
                                                                upload.status !== 'uploaded' ||
                                                                extractingUploadId !== null
                                                            }
                                                        >
                                                            {extractingUploadId === upload.id
                                                                ? 'Extracting...'
                                                                : 'Extract All'}
                                                        </button>
                                                    </td>
                                                )}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Display extracted students for each uploaded Excel file. */}
                    {isRegistrationOfficer && shortlistUploads.map((upload) => {
                        const extractedRows =
                            upload.processing_summary?.extracted_interviews || [];

                        if (extractedRows.length === 0) {
                            return null;
                        }

                        const selectedIds = selectedInterviewIds[upload.id] || [];

                        return (
                            <div
                                key={`extracted-${upload.id}`}
                                className="interviews-card"
                            >
                                <h3>Extracted Students — Upload #{upload.id}</h3>

                                <div className="interviews-table-wrapper">
                                    <table className="interviews-table">
                                        <thead>
                                            <tr>
                                                <th>Select</th>
                                                <th>Student</th>
                                                <th>Email</th>
                                                <th>Interview Date</th>
                                                <th>Time</th>
                                                <th>Type</th>
                                            </tr>
                                        </thead>

                                        <tbody>
                                            {extractedRows.map((row) => (
                                                <tr key={row.interview_id}>
                                                    <td>
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedIds.includes(row.interview_id)}
                                                            onChange={(event) =>
                                                                handleInterviewSelection(
                                                                    upload.id,
                                                                    row.interview_id,
                                                                    event.target.checked
                                                                )
                                                            }
                                                        />
                                                    </td>

                                                    <td>{row.student_name}</td>
                                                    <td>{row.student_email}</td>
                                                    <td>{row.interview_date}</td>
                                                    <td>{row.interview_time}</td>
                                                    <td>{row.interview_type}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                <p>
                                    Selected students: {selectedIds.length}
                                </p>

                                <button
                                    type="button"
                                    onClick={() => handleSendNotifications(upload.id)}
                                    disabled={
                                        selectedIds.length === 0 ||
                                        sendingUploadId !== null
                                    }
                                >
                                    {sendingUploadId === upload.id
                                        ? 'Sending...'
                                        : 'Send Notifications'}
                                </button>
                            </div>
                        );
                    })}
                </section>
            )}

            {/* Only Admin can schedule or edit interviews. */}
            {canManageInterviews && (
                <section className="interviews-card">
                    <h3>
                        {editingId
                            ? 'Update Interview'
                            : 'Schedule an Interview'}
                    </h3>

                    <form
                        className="interviews-form"
                        onSubmit={handleSubmit}
                    >
                        <div className="interviews-field interviews-field-wide">
                            <label htmlFor="interview-application">
                                Application
                            </label>

                            <select
                                id="interview-application"
                                name="application"
                                value={form.application}
                                onChange={handleChange}
                                required
                            >
                                <option value="">
                                    Select an application
                                </option>

                                {applications.map((application) => (
                                    <option
                                        key={application.id}
                                        value={application.id}
                                    >
                                        {getApplicationLabel(application)}
                                    </option>
                                ))}
                            </select>

                            {applications.length === 0 && (
                                <small>
                                    Create an application before scheduling
                                    an interview.
                                </small>
                            )}
                        </div>

                        <div className="interviews-field">
                            <label htmlFor="interview-date">
                                Interview date
                            </label>

                            <input
                                id="interview-date"
                                name="interview_date"
                                type="date"
                                value={form.interview_date}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="interviews-field">
                            <label htmlFor="interview-time">
                                Interview time
                            </label>

                            <input
                                id="interview-time"
                                name="interview_time"
                                type="time"
                                value={form.interview_time}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="interviews-field">
                            <label htmlFor="interview-type">
                                Interview type
                            </label>

                            <select
                                id="interview-type"
                                name="interview_type"
                                value={form.interview_type}
                                onChange={handleChange}
                                required
                            >
                                <option value="online">Online</option>
                                <option value="offline">Offline</option>
                            </select>
                        </div>

                        {form.interview_type === 'online' ? (
                            <div className="interviews-field interviews-field-wide">
                                <label htmlFor="meeting-link">
                                    Meeting link
                                </label>

                                <input
                                    id="meeting-link"
                                    name="meeting_link"
                                    type="url"
                                    placeholder="https://meet.example.com/..."
                                    value={form.meeting_link}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        ) : (
                            <div className="interviews-field interviews-field-wide">
                                <label htmlFor="interview-location">
                                    Interview location
                                </label>

                                <input
                                    id="interview-location"
                                    name="location"
                                    type="text"
                                    placeholder="Enter office address"
                                    value={form.location}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        )}

                        <div className="interviews-field">
                            <label htmlFor="interview-status">
                                Status
                            </label>

                            <select
                                id="interview-status"
                                name="status"
                                value={form.status}
                                onChange={handleChange}
                                required
                            >
                                <option value="scheduled">Scheduled</option>
                                <option value="completed">Completed</option>
                                <option value="cancelled">Cancelled</option>
                                <option value="rescheduled">Rescheduled</option>
                            </select>
                        </div>

                        <div className="interviews-field interviews-field-wide">
                            <label htmlFor="interview-feedback">
                                Feedback (optional)
                            </label>

                            <textarea
                                id="interview-feedback"
                                name="feedback"
                                rows="3"
                                placeholder="Add interview feedback or notes"
                                value={form.feedback}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="interviews-actions interviews-field-wide">
                            <button
                                type="submit"
                                disabled={saving || applications.length === 0}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingId
                                        ? 'Update Interview'
                                        : 'Schedule Interview'}
                            </button>

                            {editingId && (
                                <button
                                    type="button"
                                    className="interviews-secondary-button"
                                    onClick={resetForm}
                                    disabled={saving}
                                >
                                    Cancel Edit
                                </button>
                            )}
                        </div>
                    </form>
                </section>
            )}

            <section className="interviews-card">
                <div className="interviews-list-header">
                    <h3>Interview Schedule</h3>

                    <button
                        type="button"
                        className="interviews-secondary-button"
                        onClick={loadData}
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>

                {loading ? (
                    <p className="interviews-empty">
                        Loading interviews...
                    </p>
                ) : interviews.length === 0 ? (
                    <p className="interviews-empty">
                        No interviews scheduled yet.
                    </p>
                ) : (
                    <div className="interviews-table-wrapper">
                        <table className="interviews-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Type</th>
                                    <th>Details</th>
                                    <th>Status</th>

                                    {canManageInterviews && (
                                        <th>Actions</th>
                                    )}
                                </tr>
                            </thead>

                            <tbody>
                                {interviews.map((interview) => (
                                    <tr key={interview.id}>
                                        <td>
                                            {getApplicationDetails(
                                                interview.application
                                            )}
                                        </td>

                                        <td>{interview.interview_date}</td>

                                        <td>
                                            {interview.interview_time?.slice(0, 5)}
                                        </td>

                                        <td>{interview.interview_type}</td>

                                        <td>
                                            {interview.interview_type === 'online' &&
                                            interview.meeting_link ? (
                                                <a
                                                    href={interview.meeting_link}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                >
                                                    Join link
                                                </a>
                                            ) : (
                                                interview.location || '—'
                                            )}
                                        </td>

                                        <td>
                                            <span
                                                className={statusClass(
                                                    interview.status
                                                )}
                                            >
                                                {interview.status}
                                            </span>
                                        </td>

                                        {canManageInterviews && (
                                            <td>
                                                <div className="interviews-row-actions">
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            startEdit(interview)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="interviews-delete-button"
                                                        onClick={() =>
                                                            handleDelete(interview.id)
                                                        }
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}

export default Interviews;
