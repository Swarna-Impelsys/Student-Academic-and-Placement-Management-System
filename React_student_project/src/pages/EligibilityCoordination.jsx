
import { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import './EligibilityCoordination.css';

function getList(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    return [];
}

function getErrorMessage(error) {
    const data = error.response?.data;

    if (typeof data?.error === 'string') return data.error;
    if (typeof data?.detail === 'string') return data.detail;

    return 'Something went wrong. Please try again.';
}

function EligibilityCoordination() {
    const [assignments, setAssignments] = useState([]);
    const [jobs, setJobs] = useState([]);

    const [selectedTeacher, setSelectedTeacher] = useState('');
    const [selectedJob, setSelectedJob] = useState('');

    const [pendingStudents, setPendingStudents] = useState([]);
    const [acceptedStudents, setAcceptedStudents] = useState([]);
    const [declinedStudents, setDeclinedStudents] = useState([]);
    const [appliedStudents, setAppliedStudents] = useState([]);
    const [ineligibleStudents, setIneligibleStudents] = useState([]);

    const [selectedStudents, setSelectedStudents] = useState([]);

    const [loadingDropdowns, setLoadingDropdowns] = useState(true);
    const [loadingResults, setLoadingResults] = useState(false);
    const [sending, setSending] = useState(false);

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Load teacher assignments and jobs.
    useEffect(() => {
        async function loadDropdownData() {
            try {
                setLoadingDropdowns(true);
                setError('');

                const [teacherResponse, jobResponse] = await Promise.all([
                    api.get('admin/teacher-course-assignments/'),
                    api.get('jobs/'),
                ]);

                setAssignments(getList(teacherResponse.data));
                setJobs(getList(jobResponse.data));
            } catch (err) {
                setError(getErrorMessage(err));
            } finally {
                setLoadingDropdowns(false);
            }
        }

        loadDropdownData();
    }, []);

    // Remove duplicate teachers from assignment records.
    const teachers = useMemo(() => {
        const uniqueTeachers = new Map();

        assignments.forEach((assignment) => {
            const teacherId = assignment.teacher;

            if (teacherId && !uniqueTeachers.has(String(teacherId))) {
                uniqueTeachers.set(String(teacherId), {
                    id: teacherId,
                    name: assignment.teacher_name,
                });
            }
        });

        return Array.from(uniqueTeachers.values());
    }, [assignments]);

    // Load eligibility coordination results.
    useEffect(() => {
        if (!selectedTeacher || !selectedJob) {
            setPendingStudents([]);
            setAcceptedStudents([]);
            setDeclinedStudents([]);
            setAppliedStudents([]);
            setIneligibleStudents([]);
            setSelectedStudents([]);
            return;
        }

        let cancelled = false;

        async function loadEligibilityResults() {
            try {
                setLoadingResults(true);
                setError('');
                setSuccess('');

                setPendingStudents([]);
                setAcceptedStudents([]);
                setDeclinedStudents([]);
                setAppliedStudents([]);
                setIneligibleStudents([]);
                setSelectedStudents([]);

                const response = await api.get('eligible-students/', {
                    params: {
                        teacher: selectedTeacher,
                        job: selectedJob,
                    },
                });

                if (cancelled) return;

                const data = response.data;

                setPendingStudents(
                    data.pending_students || []
                );

                setAcceptedStudents(
                    data.accepted_students || []
                );

                setDeclinedStudents(
                    data.declined_students || []
                );

                setAppliedStudents(
                    data.applied_students || []
                );

                setIneligibleStudents(
                    data.ineligible_students || []
                );
            } catch (err) {
                if (!cancelled) {
                    setError(getErrorMessage(err));
                }
            } finally {
                if (!cancelled) {
                    setLoadingResults(false);
                }
            }
        }

        loadEligibilityResults();

        return () => {
            cancelled = true;
        };
    }, [selectedTeacher, selectedJob]);

    function handleStudentSelection(studentId) {
        setSelectedStudents((previous) => {
            const alreadySelected = previous.some(
                (id) => String(id) === String(studentId)
            );

            if (alreadySelected) {
                return previous.filter(
                    (id) => String(id) !== String(studentId)
                );
            }

            return [...previous, studentId];
        });
    }

    const allSelected =
        pendingStudents.length > 0 &&
        pendingStudents.every((student) =>
            selectedStudents.some(
                (id) => String(id) === String(student.student_id)
            )
        );

    function handleSelectAll(event) {
        if (event.target.checked) {
            setSelectedStudents(
                pendingStudents.map((student) => student.student_id)
            );
        } else {
            setSelectedStudents([]);
        }
    }

    async function refreshEligibilityResults() {
        const response = await api.get('eligible-students/', {
            params: {
                teacher: selectedTeacher,
                job: selectedJob,
            },
        });

        const data = response.data;

        setPendingStudents(data.pending_students || []);
        setAcceptedStudents(data.accepted_students || []);
        setDeclinedStudents(data.declined_students || []);
        setAppliedStudents(data.applied_students || []);
        setIneligibleStudents(data.ineligible_students || []);
    }

    async function handleSendNotifications() {
        if (!selectedTeacher || !selectedJob || selectedStudents.length === 0) {
            setError('Please select at least one eligible student.');
            return;
        }

        const confirmed = window.confirm(
            `Send job notifications to ${selectedStudents.length} selected student(s)?`
        );

        if (!confirmed) return;

        setSending(true);
        setError('');
        setSuccess('');

        try {
            const response = await api.post(
                'notifications/send-eligible-job/',
                {
                    job: Number(selectedJob),
                    teacher: Number(selectedTeacher),
                    student_ids: selectedStudents.map(Number),
                }
            );

            setSuccess(
                `${response.data.message || 'Notifications processed successfully.'} ` +
                `Notifications sent: ${response.data.notifications_sent ?? 0}.`
            );

            setSelectedStudents([]);

        } catch (err) {
            setError(getErrorMessage(err));
            setSending(false);
            return;
        }

        try {
            await refreshEligibilityResults();
        } catch (err) {
            console.error('Eligibility refresh error:', err);

            setError(
                'Notifications were sent successfully, but the list could not be refreshed. Please refresh the page.'
            );
        } finally {
            setSending(false);
        }
    }

    function renderStudentTable(title, description, students, columns) {
        return (
            <section className="eligibility-table-card">
                <div className="eligibility-table-heading">
                    <div>
                        <h3>{title}</h3>
                        <p>{description}</p>
                    </div>
                </div>

                <div className="eligibility-table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                {columns.map((column) => (
                                    <th key={column.key}>{column.label}</th>
                                ))}
                            </tr>
                        </thead>

                        <tbody>
                            {students.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan={columns.length}
                                        className="eligibility-no-data"
                                    >
                                        No students found.
                                    </td>
                                </tr>
                            ) : (
                                students.map((student) => (
                                    <tr key={student.student_id}>
                                        {columns.map((column) => (
                                            <td key={column.key}>
                                                {column.render
                                                    ? column.render(student)
                                                    : student[column.key] || '—'}
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </section>
        );
    }

    if (loadingDropdowns) {
        return (
            <div className="eligibility-page">
                Loading teachers and jobs...
            </div>
        );
    }

    return (
        <div className="eligibility-page">
            <div className="eligibility-heading">
                <div>
                    <h2>Eligibility Coordination</h2>
                    <p>
                        Review eligibility results and send job opportunities
                        to eligible students.
                    </p>
                </div>
            </div>

            {error && (
                <div className="eligibility-alert error" role="alert">
                    {error}
                </div>
            )}

            {success && (
                <div className="eligibility-alert success" role="status">
                    {success}
                </div>
            )}

            <section className="eligibility-filter-card">
                <div className="eligibility-field">
                    <label htmlFor="teacher">Select Teacher</label>

                    <select
                        id="teacher"
                        value={selectedTeacher}
                        onChange={(event) => {
                            setSelectedTeacher(event.target.value);
                            setSelectedStudents([]);
                        }}
                    >
                        <option value="">Choose Teacher</option>

                        {teachers.map((teacher) => (
                            <option key={teacher.id} value={teacher.id}>
                                {teacher.name || `Teacher #${teacher.id}`}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="eligibility-field">
                    <label htmlFor="job">Select Job</label>

                    <select
                        id="job"
                        value={selectedJob}
                        onChange={(event) => {
                            setSelectedJob(event.target.value);
                            setSelectedStudents([]);
                        }}
                    >
                        <option value="">Choose Job</option>

                        {jobs.map((job) => (
                            <option key={job.id} value={job.id}>
                                {job.title || `Job #${job.id}`}
                            </option>
                        ))}
                    </select>
                </div>
            </section>

            {!selectedTeacher || !selectedJob ? (
                <div className="eligibility-empty">
                    Select a teacher and a job to view eligibility results.
                </div>
            ) : loadingResults ? (
                <div className="eligibility-empty">
                    Loading eligibility results...
                </div>
            ) : (
                <>
                    <div className="eligibility-summary">
                        <div className="eligibility-summary-card">
                            <span>Total Checked</span>
                            <strong>
                                {pendingStudents.length +
                                    acceptedStudents.length +
                                    declinedStudents.length +
                                    appliedStudents.length +
                                    ineligibleStudents.length}
                            </strong>
                        </div>

                        <div className="eligibility-summary-card">
                            <span>Pending Eligible</span>
                            <strong className="eligible-number">
                                {pendingStudents.length}
                            </strong>
                        </div>

                        <div className="eligibility-summary-card">
                            <span>Ineligible Students</span>
                            <strong className="ineligible-number">
                                {ineligibleStudents.length}
                            </strong>
                        </div>
                    </div>

                    {/* Pending eligible students */}
                    <section className="eligibility-table-card">
                        <div className="eligibility-table-heading">
                            <div>
                                <h3>Pending Eligible Students</h3>
                                <p>
                                    Students who have not received a notification
                                    or are waiting to respond.
                                </p>
                            </div>

                            <button
                                type="button"
                                className="eligibility-send-button"
                                onClick={handleSendNotifications}
                                disabled={
                                    sending || selectedStudents.length === 0
                                }
                            >
                                {sending
                                    ? 'Sending...'
                                    : `Send Notifications (${selectedStudents.length})`}
                            </button>
                        </div>

                        <div className="eligibility-table-wrapper">
                            <table>
                                <thead>
                                    <tr>
                                        <th>
                                            <input
                                                type="checkbox"
                                                checked={allSelected}
                                                onChange={handleSelectAll}
                                                disabled={pendingStudents.length === 0}
                                                aria-label="Select all pending students"
                                            />
                                        </th>
                                        <th>Student</th>
                                        <th>Course</th>
                                        <th>Email</th>
                                        <th>Phone</th>
                                        <th>Response</th>
                                        <th>Reason</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {pendingStudents.length === 0 ? (
                                        <tr>
                                            <td
                                                colSpan="7"
                                                className="eligibility-no-data"
                                            >
                                                No pending eligible students.
                                            </td>
                                        </tr>
                                    ) : (
                                        pendingStudents.map((student) => (
                                            <tr key={student.student_id}>
                                                <td>
                                                    <input
                                                        type="checkbox"
                                                        checked={selectedStudents.some(
                                                            (id) =>
                                                                String(id) ===
                                                                String(student.student_id)
                                                        )}
                                                        onChange={() =>
                                                            handleStudentSelection(
                                                                student.student_id
                                                            )
                                                        }
                                                        aria-label={`Select ${student.student_name}`}
                                                    />
                                                </td>

                                                <td>{student.student_name}</td>
                                                <td>{student.course}</td>
                                                <td>{student.email}</td>
                                                <td>{student.phone}</td>
                                                <td>
                                                    {student.interest_response === 'pending'
                                                        ? 'Awaiting response'
                                                        : 'Not notified'}
                                                </td>
                                                <td>{student.reason || 'Eligible'}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Accepted students */}
                    {renderStudentTable(
                        'Accepted Students',
                        'Students who accepted this job opportunity.',
                        acceptedStudents,
                        [
                            { key: 'student_name', label: 'Student' },
                            { key: 'course', label: 'Course' },
                            { key: 'email', label: 'Email' },
                            { key: 'phone', label: 'Phone' },
                            {
                                key: 'interest_response',
                                label: 'Response',
                                render: () => 'Accepted',
                            },
                        ]
                    )}

                    {/* Declined students */}
                    {renderStudentTable(
                        'Declined Students',
                        'Students who declined this opportunity and their reasons.',
                        declinedStudents,
                        [
                            { key: 'student_name', label: 'Student' },
                            { key: 'course', label: 'Course' },
                            { key: 'email', label: 'Email' },
                            {
                                key: 'decline_reason',
                                label: 'Decline Reason',
                            },
                        ]
                    )}

                    {/* Already applied students */}
                    {renderStudentTable(
                        'Already Applied Students',
                        'Students who have already submitted an application.',
                        appliedStudents,
                        [
                            { key: 'student_name', label: 'Student' },
                            { key: 'course', label: 'Course' },
                            { key: 'email', label: 'Email' },
                            { key: 'phone', label: 'Phone' },
                        ]
                    )}

                    {/* Ineligible students */}
                    {renderStudentTable(
                        'Ineligible Students',
                        'Students who did not meet the job requirements.',
                        ineligibleStudents,
                        [
                            { key: 'student_name', label: 'Student' },
                            { key: 'course', label: 'Course' },
                            { key: 'email', label: 'Email' },
                            { key: 'phone', label: 'Phone' },
                            { key: 'reason', label: 'Reason' },
                        ]
                    )}
                </>
            )}
        </div>
    );
}

export default EligibilityCoordination;
