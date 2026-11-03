
import { useEffect, useState } from 'react';
import {
    Link,
    useNavigate,
    useParams,
} from 'react-router-dom';

import {
    getStudentById,
    deleteStudent,
    getAcademicRecords,
} from '../services/studentService';

import useApi from '../hooks/useApi';

function StudentDetails() {
    const { studentId } = useParams();
    const navigate = useNavigate();

    const [student, setStudent] = useState(null);
    const [deleting, setDeleting] = useState(false);
    const [deleteError, setDeleteError] = useState('');

    const [academicRecords, setAcademicRecords] = useState([]);
    const [academicLoading, setAcademicLoading] = useState(true);
    const [academicError, setAcademicError] = useState('');

    const {
        loading,
        error,
        execute,
    } = useApi();

    // Check whether the logged-in user is an Admin.
    const isAdmin =
        localStorage.getItem('role')?.trim() === 'Admin';

    // Load student details.
    useEffect(() => {
        async function loadStudent() {
            try {
                const data = await execute(
                    () => getStudentById(studentId)
                );

                setStudent(data);
            } catch {
                // The reusable hook stores the error message.
            }
        }

        loadStudent();
    }, [studentId, execute]);

    // Load academic records for this student.
    useEffect(() => {
        let cancelled = false;

        async function loadAcademicRecords() {
            setAcademicLoading(true);
            setAcademicError('');

            try {
                const data = await getAcademicRecords();

                // Currently retrieves records from the first page only.
                const records = Array.isArray(data)
                    ? data
                    : data.results ?? [];

                const filteredRecords = records.filter(
                    (record) =>
                        Number(
                            typeof record.student === 'object'
                                ? record.student.id
                                : record.student
                        ) === Number(studentId)
                );

                if (!cancelled) {
                    setAcademicRecords(filteredRecords);
                }
            } catch (err) {
                if (!cancelled) {
                    setAcademicError(
                        err.response?.data?.detail ||
                        'Unable to load academic records.'
                    );
                }
            } finally {
                if (!cancelled) {
                    setAcademicLoading(false);
                }
            }
        }

        loadAcademicRecords();

        return () => {
            cancelled = true;
        };
    }, [studentId]);

    // Delete student.
    async function handleDelete() {
        const confirmed = window.confirm(
            `Are you sure you want to delete ${student.Name}?`
        );

        if (!confirmed) return;

        try {
            setDeleting(true);
            setDeleteError('');

            await deleteStudent(student.id);

            alert('Student deleted successfully.');
            navigate('/students');
        } catch (err) {
            const data = err.response?.data;

            setDeleteError(
                data?.detail ||
                data?.error ||
                'Unable to delete student. Please try again.'
            );
        } finally {
            setDeleting(false);
        }
    }

    // Resolve subject ID to a name when available.
    function getSubjectName(subjectId) {
        const subject = student?.subject_details?.find(
            (item) => Number(item.id) === Number(subjectId)
        );

        return subject?.name || `Subject ID: ${subjectId}`;
    }

    if (loading) {
        return <p>Loading student details...</p>;
    }

    if (error && !student) {
        return (
            <div>
                <p role="alert">{error}</p>

                <Link to="/students">
                    Back to Students
                </Link>
            </div>
        );
    }

    if (!student) {
        return <p>Student not found.</p>;
    }

    return (
        <div>
            <h2>Student Details</h2>

            {/* Edit and Delete buttons are visible only to Admin. */}
            <div className="student-actions">
                {isAdmin && (
                    <>
                        <Link
                            to={`/students/${student.id}/edit`}
                            className="as-button as-button-primary"
                        >
                            Edit Student
                        </Link>

                        <button
                            type="button"
                            className="as-button as-button-danger"
                            onClick={handleDelete}
                            disabled={deleting}
                        >
                            {deleting
                                ? 'Deleting...'
                                : 'Delete Student'}
                        </button>
                    </>
                )}
            </div>

            {deleteError && (
                <p className="student-error" role="alert">
                    {deleteError}
                </p>
            )}

            {/* Student information */}
            <div className="table-container">
                <table>
                    <tbody>
                        <tr>
                            <th>ID</th>
                            <td>{student.id}</td>
                        </tr>

                        <tr>
                            <th>Name</th>
                            <td>{student.Name || '—'}</td>
                        </tr>

                        <tr>
                            <th>Email</th>
                            <td>{student.Email || '—'}</td>
                        </tr>

                        <tr>
                            <th>Age</th>
                            <td>{student.Age ?? '—'}</td>
                        </tr>

                        <tr>
                            <th>Phone</th>
                            <td>{student.Phone || '—'}</td>
                        </tr>

                        <tr>
                            <th>Course ID</th>
                            <td>{student.Course ?? '—'}</td>
                        </tr>

                        <tr>
                            <th>Status</th>
                            <td>
                                {student.status_display ||
                                    student.status ||
                                    '—'}
                            </td>
                        </tr>

                        <tr>
                            <th>Subjects</th>
                            <td>
                                {student.subject_details?.length
                                    ? student.subject_details
                                        .map((subject) => subject.name)
                                        .join(', ')
                                    : 'No subjects'}
                            </td>
                        </tr>

                        <tr>
                            <th>Certifications</th>
                            <td>
                                {student.certifications?.length
                                    ? student.certifications
                                        .map((cert) => cert.name)
                                        .join(', ')
                                    : 'No certifications'}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            {/* Academic records */}
            <section className="student-academic-records">
                <h2>Academic Records</h2>

                <p>
                    Academic performance for {student.Name || 'this student'}.
                </p>

                {academicLoading && (
                    <p>Loading academic records...</p>
                )}

                {academicError && (
                    <p role="alert">{academicError}</p>
                )}

                {!academicLoading &&
                    !academicError &&
                    academicRecords.length === 0 && (
                        <p>
                            No academic records found for this student.
                        </p>
                    )}

                {!academicLoading &&
                    !academicError &&
                    academicRecords.length > 0 && (
                        <div className="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        <th>Semester</th>
                                        <th>Subject</th>
                                        <th>Marks</th>
                                        <th>Attendance</th>
                                        <th>Backlog</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {academicRecords.map((record) => (
                                        <tr key={record.id}>
                                            <td>{record.semester}</td>

                                            <td>
                                                {getSubjectName(
                                                    typeof record.subject === 'object'
                                                        ? record.subject.id
                                                        : record.subject
                                                )}
                                            </td>

                                            <td>{record.marks}/100</td>

                                            <td>{record.attendance}%</td>

                                            <td>
                                                {record.backlog ? 'Yes' : 'No'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                <p>
                    <Link to="/academic-records">
                        View All Academic Records
                    </Link>
                </p>
            </section>

            <p>
                <Link to="/students">
                    ← Back to Students
                </Link>
            </p>
        </div>
    );
}

export default StudentDetails;
