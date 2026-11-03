
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import {
    getApplications,
    createApplication,
    updateApplicationStatus,
} from '../services/applicationService';
import { getStudents } from '../services/studentService';
import { getJobs } from '../services/jobService';
import api from '../services/api';
import '../App.css';

function getList(data) {
    if (Array.isArray(data)) return data;

    return (
        data?.results ||
        data?.applications ||
        data?.students ||
        data?.jobs ||
        data?.data ||
        []
    );
}

function getErrorMessage(err, fallback) {
    const data = err.response?.data;

    const message =
        data?.detail ||
        data?.error ||
        data?.reason ||
        data?.non_field_errors?.[0];

    if (typeof message === 'string') return message;
    if (message) return JSON.stringify(message);

    return fallback;
}

function Applications() {
    // Read and update URL query parameters
    const [searchParams, setSearchParams] = useSearchParams();

    const role = (
        localStorage.getItem('role') || ''
    ).trim().toLowerCase();

    // Explicit role definitions.
    const isStudent = role === 'student';
    const isAdmin = role === 'admin';
    const isTeacher = role === 'teacher';
    const isRegistrationOfficer = role === 'registration officer';

    // Explicit permissions for this page.
    // Explicit permissions for this page.
    const canSubmitApplication = isStudent;
    const canNotifyEligibleStudents = isTeacher;
    const canManageStatus = false;

    const [applications, setApplications] = useState([]);
    const [students, setStudents] = useState([]);
    const [jobs, setJobs] = useState([]);

    const [studentId, setStudentId] = useState('');
    const [jobId, setJobId] = useState('');

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [updatingId, setUpdatingId] = useState(null);

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Teacher-only eligible-student notification state.
    const [eligibleJobId, setEligibleJobId] = useState('');
    const [eligibleStudents, setEligibleStudents] = useState([]);
    const [selectedStudentIds, setSelectedStudentIds] = useState([]);
    const [eligibleLoading, setEligibleLoading] = useState(false);
    const [sendingNotifications, setSendingNotifications] = useState(false);
    const [eligibleError, setEligibleError] = useState('');
    const [eligibleSuccess, setEligibleSuccess] = useState('');

    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const requests = [
                getApplications(),
                getJobs(),
            ];

            // Only Admin needs the student list for the application form.
            if (isAdmin) {
                requests.push(getStudents());
            }

            const results = await Promise.all(requests);

            setApplications(getList(results[0]));
            setJobs(getList(results[1]));

            if (isAdmin) {
                setStudents(getList(results[2]));
            } else {
                setStudents([]);
            }

            return true;
        } catch (err) {
            console.error(
                'Applications API error:',
                err.response?.status,
                err.response?.data
            );

            setError(
                getErrorMessage(
                    err,
                    'Unable to load applications. Please check the backend and your login.'
                )
            );

            return false;
        } finally {
            setLoading(false);
        }
    }

    // Load page data when the component mounts.
    useEffect(() => {
        loadData();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Automatically select the job received from the notification Accept action.
    useEffect(() => {
        const requestedJobId = searchParams.get('job');

        if (!requestedJobId || jobs.length === 0) {
            return;
        }

        const matchingJob = jobs.find(
            (job) => String(job.id) === String(requestedJobId)
        );

        if (matchingJob) {
            setJobId(String(matchingJob.id));

            // Remove the query parameter after selecting the job.
            // This prevents selecting it again after a later data refresh.
            const updatedParams = new URLSearchParams(searchParams);
            updatedParams.delete('job');

            setSearchParams(updatedParams, { replace: true });
        } else {
            setError('The job from your notification could not be found.');
        }
    }, [jobs, searchParams, setSearchParams]);

    // Admin and Students can submit applications.
    async function handleSubmit(event) {
        event.preventDefault();

        setError('');
        setSuccess('');

        if (!canSubmitApplication) {
            setError('You do not have permission to submit applications.');
            return;
        }

        if (!jobId || (isAdmin && !studentId)) {
            setError(
                isStudent
                    ? 'Please select a job.'
                    : 'Please select a student and a job.'
            );
            return;
        }

        setSubmitting(true);

        try {
            await createApplication(
                isStudent ? null : studentId,
                jobId
            );

            setStudentId('');
            setJobId('');

            const refreshed = await loadData();

            if (refreshed) {
                setSuccess('Application submitted successfully.');
            } else {
                setSuccess(
                    'Application was submitted successfully, but the application list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            console.error(
                'Application submission error:',
                err.response?.status,
                err.response?.data
            );

            setError(
                getErrorMessage(
                    err,
                    'Unable to submit the application. Please try again.'
                )
            );
        } finally {
            setSubmitting(false);
        }
    }

    // Only Admin can update application statuses.
    async function handleStatusChange(applicationId, newStatus) {
        if (!canManageStatus) {
            setError('Only Admin can update application statuses.');
            return;
        }

        setError('');
        setSuccess('');
        setUpdatingId(applicationId);

        try {
            const updatedApplication = await updateApplicationStatus(
                applicationId,
                newStatus
            );

            setApplications((previousApplications) =>
                previousApplications.map((application) =>
                    String(application.id) === String(applicationId)
                        ? {
                            ...application,
                            ...updatedApplication,
                        }
                        : application
                )
            );

            setSuccess(
                `Application #${applicationId} status updated to ${newStatus}.`
            );
        } catch (err) {
            console.error(
                'Application status update error:',
                err.response?.status,
                err.response?.data
            );

            setError(
                getErrorMessage(
                    err,
                    'Unable to update application status.'
                )
            );
        } finally {
            setUpdatingId(null);
        }
    }

    function getStudentName(student) {
        if (student && typeof student === 'object') {
            return (
                student.Name ||
                student.name ||
                student.full_name ||
                student.student_name ||
                student.user?.username ||
                `Student #${student.id ?? '—'}`
            );
        }

        const found = students.find(
            (item) => String(item.id) === String(student)
        );

        return found
            ? getStudentName(found)
            : `Student #${student ?? '—'}`;
    }

    function getJobTitle(jobValue) {
        if (jobValue && typeof jobValue === 'object') {
            return jobValue.title || `Job #${jobValue.id}`;
        }

        const job = jobs.find(
            (item) => String(item.id) === String(jobValue)
        );

        return job
            ? job.title || `Job #${job.id}`
            : `Job #${jobValue ?? '—'}`;
    }

    function getStatusClass(status) {
        const value = String(status || 'pending').toLowerCase();

        if (
            value.includes('accept') ||
            value.includes('select') ||
            value.includes('shortlist')
        ) {
            return 'application-status application-status-success';
        }

        if (value.includes('reject')) {
            return 'application-status application-status-danger';
        }

        if (value.includes('pending') || value.includes('review')) {
            return 'application-status application-status-pending';
        }

        return 'application-status';
    }

    // Load eligible students for the job selected by a Teacher.
    async function handleEligibleJobChange(event) {
        const selectedJob = event.target.value;

        setEligibleJobId(selectedJob);
        setEligibleStudents([]);
        setSelectedStudentIds([]);
        setEligibleError('');
        setEligibleSuccess('');

        if (!selectedJob) return;

        setEligibleLoading(true);

        try {
            const response = await api.get(
                `eligible-students/?job=${selectedJob}`
            );

            setEligibleStudents(
                response.data?.eligible_students || []
            );
        } catch (err) {
            console.error(
                'Eligible students API error:',
                err.response?.status,
                err.response?.data
            );

            setEligibleError(
                getErrorMessage(
                    err,
                    'Unable to load eligible students.'
                )
            );
        } finally {
            setEligibleLoading(false);
        }
    }

    function handleStudentSelection(studentIdValue, checked) {
        setSelectedStudentIds((previousIds) => {
            if (checked) {
                if (
                    previousIds.some(
                        (id) => String(id) === String(studentIdValue)
                    )
                ) {
                    return previousIds;
                }

                return [...previousIds, studentIdValue];
            }

            return previousIds.filter(
                (id) => String(id) !== String(studentIdValue)
            );
        });
    }

    const allEligibleSelected =
        eligibleStudents.length > 0 &&
        eligibleStudents.every((student) =>
            selectedStudentIds.some(
                (id) => String(id) === String(student.student_id)
            )
        );

    function handleSelectAll(event) {
        if (event.target.checked) {
            setSelectedStudentIds(
                eligibleStudents.map((student) => student.student_id)
            );
        } else {
            setSelectedStudentIds([]);
        }
    }

    // Send notifications first, then refresh separately.
    async function handleSendNotifications() {
        setEligibleError('');
        setEligibleSuccess('');

        if (!canNotifyEligibleStudents) {
            setEligibleError(
                'Only Teachers can send eligible-student notifications.'
            );
            return;
        }

        if (!eligibleJobId) {
            setEligibleError('Please select a job first.');
            return;
        }

        if (selectedStudentIds.length === 0) {
            setEligibleError(
                'Please select at least one eligible student.'
            );
            return;
        }

        setSendingNotifications(true);

        try {
            // Step 1: Send the notifications.
            const response = await api.post(
                'notifications/send-eligible-job/',
                {
                    job: Number(eligibleJobId),
                    student_ids: selectedStudentIds.map(Number),
                }
            );

            const sentCount =
                response.data?.notifications_sent ??
                selectedStudentIds.length;

            // Sending succeeded. Show success before attempting refresh.
            setEligibleSuccess(
                `Job notification sent successfully to ${sentCount} student(s).`
            );

            setSelectedStudentIds([]);

        } catch (err) {
            console.error(
                'Job notification error:',
                err.response?.status,
                err.response?.data
            );

            setEligibleError(
                getErrorMessage(
                    err,
                    'Unable to send job notifications.'
                )
            );

            setSendingNotifications(false);
            return;
        }

        // Step 2: Refresh the eligible-student list separately.
        // A refresh failure must not be reported as a notification failure.
        try {
            const refreshedResponse = await api.get(
                `eligible-students/?job=${eligibleJobId}`
            );

            setEligibleStudents(
                refreshedResponse.data?.eligible_students || []
            );
        } catch (refreshError) {
            console.error(
                'Eligible students refresh error:',
                refreshError.response?.status,
                refreshError.response?.data
            );

            setEligibleError(
                'Notifications were sent successfully, but the eligible-student list could not be refreshed. Please refresh the list.'
            );
        } finally {
            setSendingNotifications(false);
        }
    }

    const visibleJobs = isStudent
        ? jobs.filter((job) => job.is_active === true)
        : jobs;

    return (
        <div className="applications-page">
            <div className="applications-header">
                <div>
                    <h2>Applications Management</h2>
                    <p>
                        {isStudent
                            ? 'Apply for jobs and track your applications.'
                            : isTeacher
                                ? 'Review applications for your assigned courses and notify eligible students.'
                                : isRegistrationOfficer
                                    ? 'View placement applications.'
                                    : 'View and manage placement applications.'}
                    </p>
                </div>

                <button
                    type="button"
                    className="applications-refresh"
                    onClick={loadData}
                    disabled={loading}
                >
                    {loading ? 'Loading...' : 'Refresh'}
                </button>
            </div>

            {error && (
                <div
                    className="applications-message applications-error"
                    role="alert"
                >
                    {error}
                </div>
            )}

            {success && (
                <div
                    className="applications-message applications-success"
                    role="status"
                >
                    {success}
                </div>
            )}

            {/* Application form: Admin and Student only. */}
            {canSubmitApplication && (
                <section className="applications-card">
                    <h3>Apply for a Job</h3>

                    <form
                        className="applications-form"
                        onSubmit={handleSubmit}
                    >
                        {isAdmin && (
                            <div className="applications-field">
                                <label htmlFor="application-student">
                                    Student
                                </label>

                                <select
                                    id="application-student"
                                    value={studentId}
                                    onChange={(event) =>
                                        setStudentId(event.target.value)
                                    }
                                    required
                                >
                                    <option value="">
                                        Select student
                                    </option>

                                    {students.map((student) => (
                                        <option
                                            key={student.id}
                                            value={student.id}
                                        >
                                            {getStudentName(student)}
                                            {' '}— ID: {student.id}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {isStudent && (
                            <p>
                                Your application will use your logged-in
                                student profile automatically.
                            </p>
                        )}

                        <div className="applications-field">
                            <label htmlFor="application-job">
                                Job
                            </label>

                            <select
                                id="application-job"
                                value={jobId}
                                onChange={(event) =>
                                    setJobId(event.target.value)
                                }
                                required
                            >
                                <option value="">Select job</option>

                                {visibleJobs.map((job) => (
                                    <option
                                        key={job.id}
                                        value={job.id}
                                    >
                                        {job.title || `Job #${job.id}`}
                                        {' '}— ID: {job.id}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <button
                            type="submit"
                            className="applications-submit"
                            disabled={submitting || loading}
                        >
                            {submitting
                                ? 'Submitting...'
                                : 'Submit Application'}
                        </button>
                    </form>
                </section>
            )}

            {/* Teacher-only eligible-student notification feature. */}
            {canNotifyEligibleStudents && (
                <section className="applications-card">
                    <h3>Eligible Students — Job Notifications</h3>

                    <p>
                        Select a job to find eligible students from your
                        assigned courses who have not applied yet.
                    </p>

                    <div className="applications-field">
                        <label htmlFor="eligible-job">
                            Select Job
                        </label>

                        <select
                            id="eligible-job"
                            value={eligibleJobId}
                            onChange={handleEligibleJobChange}
                            disabled={eligibleLoading || sendingNotifications}
                        >
                            <option value="">Select a job</option>

                            {jobs
                                .filter((job) => job.is_active === true)
                                .map((job) => (
                                    <option
                                        key={job.id}
                                        value={job.id}
                                    >
                                        {job.title || `Job #${job.id}`}
                                        {' '}— ID: {job.id}
                                    </option>
                                ))}
                        </select>
                    </div>

                    {eligibleError && (
                        <div
                            className="applications-message applications-error"
                            role="alert"
                        >
                            {eligibleError}
                        </div>
                    )}

                    {eligibleSuccess && (
                        <div
                            className="applications-message applications-success"
                            role="status"
                        >
                            {eligibleSuccess}
                        </div>
                    )}

                    {eligibleLoading && (
                        <p className="applications-empty">
                            Loading eligible students...
                        </p>
                    )}

                    {eligibleJobId &&
                        !eligibleLoading &&
                        !eligibleError && (
                            <>
                                {eligibleStudents.length === 0 ? (
                                    <p className="applications-empty">
                                        No eligible students who have not
                                        applied were found for this job.
                                    </p>
                                ) : (
                                    <>
                                        <p>
                                            Eligible students found:{' '}
                                            {eligibleStudents.length}
                                        </p>

                                        <div className="applications-table-wrapper">
                                            <table className="applications-table">
                                                <thead>
                                                    <tr>
                                                        <th>
                                                            <input
                                                                type="checkbox"
                                                                aria-label="Select all eligible students"
                                                                checked={allEligibleSelected}
                                                                onChange={handleSelectAll}
                                                            />
                                                        </th>
                                                        <th>Student</th>
                                                        <th>Email</th>
                                                        <th>Course</th>
                                                        <th>Eligibility Reason</th>
                                                    </tr>
                                                </thead>

                                                <tbody>
                                                    {eligibleStudents.map(
                                                        (student) => (
                                                            <tr
                                                                key={student.student_id}
                                                            >
                                                                <td>
                                                                    <input
                                                                        type="checkbox"
                                                                        aria-label={`Select ${student.student_name}`}
                                                                        checked={selectedStudentIds.some(
                                                                            (id) =>
                                                                                String(id) ===
                                                                                String(student.student_id)
                                                                        )}
                                                                        onChange={(event) =>
                                                                            handleStudentSelection(
                                                                                student.student_id,
                                                                                event.target.checked
                                                                            )
                                                                        }
                                                                    />
                                                                </td>

                                                                <td>
                                                                    {student.student_name}
                                                                </td>

                                                                <td>
                                                                    {student.email || '—'}
                                                                </td>

                                                                <td>
                                                                    {student.course || '—'}
                                                                </td>

                                                                <td>
                                                                    {student.reason || 'Eligible'}
                                                                </td>
                                                            </tr>
                                                        )
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>

                                        <p>
                                            Selected students:{' '}
                                            {selectedStudentIds.length}
                                        </p>

                                        <button
                                            type="button"
                                            className="applications-submit"
                                            onClick={handleSendNotifications}
                                            disabled={
                                                sendingNotifications ||
                                                selectedStudentIds.length === 0
                                            }
                                        >
                                            {sendingNotifications
                                                ? 'Sending Notifications...'
                                                : `Send Job Notification (${selectedStudentIds.length})`}
                                        </button>
                                    </>
                                )}
                            </>
                        )}
                </section>
            )}

            {/* Applications list for all authorized roles. */}
            <section className="applications-card">
                <div className="applications-list-header">
                    <div>
                        <h3>Placement Applications</h3>
                        <p>
                            Total applications: {applications.length}
                        </p>
                    </div>
                </div>

                {loading ? (
                    <p className="applications-empty">
                        Loading applications...
                    </p>
                ) : applications.length === 0 ? (
                    <p className="applications-empty">
                        No applications found.
                    </p>
                ) : (
                    <div className="applications-table-wrapper">
                        <table className="applications-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Student</th>
                                    <th>Job</th>
                                    <th>Status</th>
                                    <th>Applied At</th>

                                    {canManageStatus && (
                                        <th>Update Status</th>
                                    )}
                                </tr>
                            </thead>

                            <tbody>
                                {applications.map((application) => (
                                    <tr key={application.id}>
                                        <td>#{application.id}</td>

                                        <td>
                                            {application.student_name || getStudentName(application.student)}
                                        </td>

                                        <td>
                                            {getJobTitle(application.job)}
                                        </td>

                                        <td>
                                            <span
                                                className={getStatusClass(
                                                    application.status
                                                )}
                                            >
                                                {application.status || 'Pending'}
                                            </span>
                                        </td>

                                        <td>
                                            {application.applied_at
                                                ? new Date(
                                                    application.applied_at
                                                ).toLocaleDateString()
                                                : '—'}
                                        </td>

                                        {canManageStatus && (
                                            <td>
                                                <select
                                                    aria-label={`Update status for application ${application.id}`}
                                                    value={String(
                                                        application.status || 'pending'
                                                    ).toLowerCase()}
                                                    disabled={
                                                        updatingId === application.id
                                                    }
                                                    onChange={(event) =>
                                                        handleStatusChange(
                                                            application.id,
                                                            event.target.value
                                                        )
                                                    }
                                                >
                                                    <option value="pending">
                                                        Pending
                                                    </option>
                                                    <option value="shortlisted">
                                                        Shortlisted
                                                    </option>
                                                    <option value="rejected">
                                                        Rejected
                                                    </option>
                                                    <option value="selected">
                                                        Selected
                                                    </option>
                                                </select>

                                                {updatingId === application.id && (
                                                    <small>Saving...</small>
                                                )}
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

export default Applications;
