
import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
    getAcademicRecords,
    updateAcademicRecord,
    deleteAcademicRecord,
} from '../services/studentService';

import useApi from '../hooks/useApi';
import './AcademicRecords.css';

function AcademicRecords() {
    const role = localStorage.getItem('role')?.trim();

    const isAdmin = role === 'Admin';
    const isTeacher = role === 'Teacher';
    const isStudent = role === 'Student';

    const canManageRecords = isAdmin || isTeacher;

    const [records, setRecords] = useState([]);
    const [editingId, setEditingId] = useState(null);

    const [form, setForm] = useState({
        semester: '',
        marks: '',
        attendance: '',
        backlog: false,
    });

    const { loading, error, setError, execute } = useApi();

    // Load academic records.
    const loadRecords = useCallback(async () => {
        try {
            const data = await execute(() => getAcademicRecords());

            // Support normal arrays and paginated responses.
            setRecords(
                Array.isArray(data)
                    ? data
                    : data.results ?? []
            );
        } catch {
            // The useApi hook stores the error message.
        }
    }, [execute]);

    useEffect(() => {
        loadRecords();
    }, [loadRecords]);

    // Start editing an academic record.
    function startEdit(record) {
        setEditingId(record.id);

        setForm({
            semester: record.semester,
            marks: record.marks,
            attendance: record.attendance,
            backlog: record.backlog,
        });

        setError('');
    }

    // Handle form input changes.
    function handleChange(event) {
        const { name, value, checked, type } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    }

    // Update an academic record.
    // Teacher can update only attendance.
    // Admin can update all editable fields.
    async function handleUpdate(event) {
        event.preventDefault();
        setError('');

        const updateData = isTeacher
            ? {
                attendance: Number(form.attendance),
            }
            : {
                semester: Number(form.semester),
                marks: Number(form.marks),
                attendance: Number(form.attendance),
                backlog: form.backlog,
            };

        try {
            const updated = await execute(() =>
                updateAcademicRecord(editingId, updateData)
            );

            setRecords((previous) =>
                previous.map((record) =>
                    record.id === editingId
                        ? { ...record, ...updated }
                        : record
                )
            );

            setEditingId(null);
        } catch {
            // The useApi hook displays the API error.
        }
    }

    // Delete an academic record. Admin-only action.
    async function handleDelete(id) {
        if (!isAdmin) return;

        const confirmed = window.confirm(
            'Are you sure you want to delete this academic record?'
        );

        if (!confirmed) return;

        setError('');

        try {
            await execute(() => deleteAcademicRecord(id));

            setRecords((previous) =>
                previous.filter((record) => record.id !== id)
            );

            if (editingId === id) {
                setEditingId(null);
            }
        } catch {
            // The useApi hook displays the API error.
        }
    }

    return (
        <div className="academic-records-page">
            <h2>Academic Records</h2>

            <p>
                Manage student marks, attendance, semesters and backlogs.
            </p>

            {/* Only Admin can add academic records. */}
            {isAdmin && (
                <Link
                    to="/academic-records/add"
                    className="btn btn-primary"
                >
                    Add Academic Record
                </Link>
            )}

            {error && <p role="alert">{error}</p>}

            {loading && <p>Loading academic records...</p>}

            {!loading && !error && records.length === 0 && (
                <p>No academic records found.</p>
            )}

            {records.length > 0 && (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Record ID</th>

                                {/* Staff can see student and course names. */}
                                {!isStudent && (
                                    <>
                                        <th>Student Name</th>
                                        <th>Course Name</th>
                                    </>
                                )}

                                <th>Semester</th>
                                <th>Subject Name</th>
                                <th>Marks</th>
                                <th>Attendance</th>
                                <th>Backlog</th>

                                {canManageRecords && <th>Actions</th>}
                            </tr>
                        </thead>

                        <tbody>
                            {records.map((record) => (
                                <tr key={record.id}>
                                    <td>{record.id}</td>

                                    {!isStudent && (
                                        <>
                                            <td>{record.student_name}</td>
                                            <td>{record.course_name}</td>
                                        </>
                                    )}

                                    <td>{record.semester}</td>
                                    <td>{record.subject_name}</td>
                                    <td>{record.marks}/100</td>
                                    <td>{record.attendance}%</td>
                                    <td>{record.backlog ? 'Yes' : 'No'}</td>

                                    {canManageRecords && (
                                        <td>
                                            <button
                                                type="button"
                                                onClick={() => startEdit(record)}
                                                disabled={loading}
                                            >
                                                Edit
                                            </button>

                                            {isAdmin && (
                                                <button
                                                    type="button"
                                                    onClick={() => handleDelete(record.id)}
                                                    disabled={loading}
                                                >
                                                    Delete
                                                </button>
                                            )}
                                        </td>
                                    )}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Edit academic record form. */}
            {editingId !== null && canManageRecords && (
                <div className="edit-record-panel">
                    <h3>Edit Record #{editingId}</h3>

                    <form onSubmit={handleUpdate}>

                        {/* Admin can edit all fields. */}
                        {isAdmin && (
                            <>
                                <label>
                                    Semester
                                    <input
                                        type="number"
                                        name="semester"
                                        min="1"
                                        value={form.semester}
                                        onChange={handleChange}
                                        required
                                    />
                                </label>

                                <label>
                                    Marks (0–100)
                                    <input
                                        type="number"
                                        name="marks"
                                        min="0"
                                        max="100"
                                        step="any"
                                        value={form.marks}
                                        onChange={handleChange}
                                        required
                                    />
                                </label>

                                <label className="backlog-label">
                                    <input
                                        type="checkbox"
                                        name="backlog"
                                        checked={form.backlog}
                                        onChange={handleChange}
                                    />
                                    Has backlog
                                </label>
                            </>
                        )}

                        {/* Admin and Teacher can edit attendance. */}
                        <label>
                            Attendance (0–100%)
                            <input
                                type="number"
                                name="attendance"
                                min="0"
                                max="100"
                                step="any"
                                value={form.attendance}
                                onChange={handleChange}
                                required
                            />
                        </label>

                        <button type="submit" disabled={loading}>
                            {loading ? 'Saving...' : 'Save Changes'}
                        </button>

                        <button
                            type="button"
                            onClick={() => setEditingId(null)}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
}

export default AcademicRecords;
