
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getStudents } from '../services/studentService';
import useApi from '../hooks/useApi';
import "./Students.css";

function Students() {
    const [students, setStudents] = useState([]);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalStudents, setTotalStudents] = useState(0);
    const [nextPage, setNextPage] = useState(null);
    const [previousPage, setPreviousPage] = useState(null);

    const {
        loading,
        error,
        execute,
    } = useApi();

    // Load students with pagination
    const loadStudents = useCallback(async (page = 1) => {
        try {
            const query = page === 1 ? '' : `?page=${page}`;

            const data = await execute(() => getStudents(query));

            if (Array.isArray(data)) {
                setStudents(data);
                setTotalStudents(data.length);
                setNextPage(null);
                setPreviousPage(null);
            } else {
                setStudents(data.results ?? []);
                setTotalStudents(data.count ?? 0);
                setNextPage(data.next);
                setPreviousPage(data.previous);
            }

            setCurrentPage(page);
        } catch {
            // useApi handles and stores the error message.
        }
    }, [execute]);

    // Fetch students when the component loads
    useEffect(() => {
        loadStudents();
    }, [loadStudents]);

    if (loading) {
        return (
            <div>
                <h2>Students</h2>
                <p>Loading students...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div>
                <h2>Students</h2>

                <p className="login-error" role="alert">
                    {error}
                </p>

                <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => loadStudents()}
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="students-page">
            <h2>Students</h2>

            {/* Show Add Student button only to Admin */}
            {localStorage.getItem('role')?.trim() === 'Admin' && (
                <Link
                    to="/students/add"
                    className="btn btn-primary"
                >
                    + Add Student
                </Link>
            )}

            {students.length === 0 ? (
                <p>No students found.</p>
            ) : (
                <div className="table-container">
                    <table className="students-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Age</th>
                                <th>Phone</th>
                                <th>Status</th>
                            </tr>
                        </thead>

                        <tbody>
                            {students.map((student) => (
                                <tr key={student.id}>
                                    <td>{student.id}</td>

                                    <td>
                                        <Link
                                            to={`/students/${student.id}`}
                                        >
                                            {student.Name || '—'}
                                        </Link>
                                    </td>

                                    <td>{student.Email || '—'}</td>

                                    <td>{student.Age ?? '—'}</td>

                                    <td>{student.Phone || '—'}</td>

                                    <td>
                                        {student.status_display ||
                                            student.status ||
                                            '—'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Pagination */}
            <div className="pagination">
                <button
                    type="button"
                    disabled={!previousPage || loading}
                    onClick={() => loadStudents(currentPage - 1)}
                >
                    Previous
                </button>

                <span>
                    Page {currentPage} of{' '}
                    {Math.max(1, Math.ceil(totalStudents / 10))}
                </span>

                <button
                    type="button"
                    disabled={!nextPage || loading}
                    onClick={() => loadStudents(currentPage + 1)}
                >
                    Next
                </button>
            </div>
        </div>
    );
}

export default Students;
