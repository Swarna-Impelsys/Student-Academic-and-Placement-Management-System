
import { useEffect, useState } from 'react';
import api from '../services/api';
import './UserManagement.css';

function getList(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    return [];
}

function getErrorMessage(error, fallback) {
    const data = error.response?.data;

    if (typeof data === 'string') return data;

    return (
        data?.error ||
        data?.detail ||
        data?.non_field_errors?.[0] ||
        fallback
    );
}

function UserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [students, setStudents] = useState([]);

    const [archivedUsers, setArchivedUsers] = useState([]);
    const [archivedLoading, setArchivedLoading] = useState(false);
    const [showArchived, setShowArchived] = useState(false);

    const [actionLoading, setActionLoading] = useState(false);

    const [formData, setFormData] = useState({
        username: '',
        email: '',
        role: 'Teacher',
        student_id: '',
    });

    const [message, setMessage] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        let isActive = true;

        async function fetchUsers() {
            try {
                setLoading(true);
                setError('');

                const [usersResponse, studentResponse] =
                    await Promise.all([
                        api.get('admin/users/'),
                        api.get('students/'),
                    ]);

                if (!isActive) return;

                setUsers(getList(usersResponse.data));
                setStudents(getList(studentResponse.data));
            } catch (error) {
                if (!isActive) return;

                setError(
                    getErrorMessage(error, 'Failed to load user accounts.')
                );
            } finally {
                if (isActive) setLoading(false);
            }
        }

        fetchUsers();

        return () => {
            isActive = false;
        };
    }, []);

    async function fetchArchivedUsers() {
        try {
            setArchivedLoading(true);
            setError('');

            const response = await api.get('admin/users/archived/');
            setArchivedUsers(getList(response.data));
        } catch (error) {
            setError(
                getErrorMessage(error, 'Failed to load archived users.')
            );
        } finally {
            setArchivedLoading(false);
        }
    }

    async function refreshActiveUsers() {
        const response = await api.get('admin/users/');
        setUsers(getList(response.data));
    }

    async function handleArchive(userId) {
        if (actionLoading) return;

        const reason = window.prompt(
            'Enter the reason for archiving this user:'
        );

        if (reason === null) return;

        setActionLoading(true);
        setError('');
        setMessage('');

        try {
            const response = await api.post(
                `admin/users/${userId}/archive/`,
                { reason }
            );

            setMessage(
                response.data.message || 'User archived successfully.'
            );

            await refreshActiveUsers();

            if (showArchived) {
                await fetchArchivedUsers();
            }
        } catch (error) {
            setError(
                getErrorMessage(error, 'Failed to archive user.')
            );
        } finally {
            setActionLoading(false);
        }
    }

    async function handleRestore(userId) {
        if (actionLoading) return;

        setActionLoading(true);
        setError('');
        setMessage('');

        try {
            const response = await api.post(
                `admin/users/${userId}/restore/`
            );

            setMessage(
                response.data.message || 'User restored successfully.'
            );

            await refreshActiveUsers();
            await fetchArchivedUsers();
        } catch (error) {
            setError(
                getErrorMessage(error, 'Failed to restore user.')
            );
        } finally {
            setActionLoading(false);
        }
    }

    function handleInputChange(event) {
        const { name, value } = event.target;

        setFormData((previousData) => ({
            ...previousData,
            [name]: value,
        }));

        setError('');
        setMessage('');
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (submitting) return;

        setError('');
        setMessage('');
        setSubmitting(true);

        try {
            const payload = {
                username: formData.username.trim(),
                email: formData.email.trim(),
                role: formData.role,
                student_id:
                    formData.role === 'Student'
                        ? Number(formData.student_id)
                        : null,
            };

            const response = await api.post('admin/users/', payload);

            setMessage(
                response.data.message ||
                'Account created. Check the invitation email status.'
            );

            setFormData({
                username: '',
                email: '',
                role: 'Teacher',
                student_id: '',
            });

            await refreshActiveUsers();

            const studentsResponse = await api.get('students/');
            setStudents(getList(studentsResponse.data));
        } catch (error) {
            setError(
                getErrorMessage(
                    error,
                    'The request failed. Check the account and invitation status before trying again.'
                )
            );
        } finally {
            setSubmitting(false);
        }
    }

    async function handleShowArchived() {
        if (archivedLoading) return;

        setShowArchived(true);
        setError('');
        setMessage('');

        await fetchArchivedUsers();
    }

    function handleShowActive() {
        setShowArchived(false);
        setError('');
        setMessage('');
    }

    const unlinkedStudents = students.filter(
        (student) => !student.user
    );

    return (
        <div className="user-management">
            <h2>User Management</h2>
            <p>View and manage user accounts.</p>

            {message && <p role="status">{message}</p>}
            {error && <p role="alert">{error}</p>}

            {/* Create User Account - First Section */}
            <div className="create-user-section">
                <h3>Create User Account</h3>

                <p>
                    The user will receive an email invitation
                    to set their own password.
                </p>

                <form onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="username">Username</label>
                        <input
                            id="username"
                            name="username"
                            value={formData.username}
                            onChange={handleInputChange}
                            required
                            disabled={submitting}
                        />
                    </div>

                    <div>
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            required
                            disabled={submitting}
                        />
                    </div>

                    <div>
                        <label htmlFor="role">Role</label>
                        <select
                            id="role"
                            name="role"
                            value={formData.role}
                            onChange={handleInputChange}
                            disabled={submitting}
                        >
                            <option value="Teacher">Teacher</option>
                            <option value="Student">Student</option>
                            <option value="Registration Officer">
                                Registration Officer
                            </option>
                        </select>
                    </div>

                    {formData.role === 'Student' && (
                        <div>
                            <label htmlFor="student_id">
                                Select Student
                            </label>

                            <select
                                id="student_id"
                                name="student_id"
                                value={formData.student_id}
                                onChange={handleInputChange}
                                required
                                disabled={submitting}
                            >
                                <option value="">Select a student</option>

                                {unlinkedStudents.map((student) => (
                                    <option
                                        key={student.id}
                                        value={student.id}
                                    >
                                        {student.Name} — {student.Email}
                                    </option>
                                ))}
                            </select>

                            {unlinkedStudents.length === 0 && (
                                <p>No unlinked student records are available.</p>
                            )}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={
                            submitting ||
                            (formData.role === 'Student' &&
                                !formData.student_id)
                        }
                    >
                        {submitting
                            ? 'Creating Account...'
                            : 'Create Account & Send Invitation'}
                    </button>
                </form>
            </div>

            {/* Active / Archived User Tabs */}
            <div className="user-management-tabs">
                <button
                    type="button"
                    className={!showArchived ? 'active-tab' : ''}
                    onClick={handleShowActive}
                    disabled={actionLoading}
                >
                    Active Users
                </button>

                <button
                    type="button"
                    className={showArchived ? 'active-tab' : ''}
                    onClick={handleShowArchived}
                    disabled={archivedLoading}
                >
                    {archivedLoading ? 'Loading...' : 'Archived Users'}
                </button>
            </div>

            {/* Only the selected list is displayed */}
            <div className="user-management-list">
                {showArchived ? (
                    <>
                        <h3>Archived User Accounts</h3>

                        {archivedLoading ? (
                            <p role="status">Loading archived users...</p>
                        ) : archivedUsers.length === 0 ? (
                            <p>No archived users found.</p>
                        ) : (
                            <div className="user-table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Username</th>
                                            <th>Email</th>
                                            <th>Role</th>
                                            <th>Status</th>
                                            <th>Reason</th>
                                            <th>Archived At</th>
                                            <th>Archived By</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {archivedUsers.map((user) => (
                                            <tr key={user.id}>
                                                <td>{user.id}</td>
                                                <td>{user.username}</td>
                                                <td>{user.email}</td>
                                                <td>{user.role}</td>
                                                <td>
                                                    {user.is_active
                                                        ? 'Active'
                                                        : 'Inactive'}
                                                </td>
                                                <td>{user.reason || '—'}</td>
                                                <td>
                                                    {user.archived_at
                                                        ? new Date(
                                                            user.archived_at
                                                        ).toLocaleString()
                                                        : '—'}
                                                </td>
                                                <td>{user.archived_by || '—'}</td>
                                                <td>
                                                    <button
                                                        type="button"
                                                        disabled={actionLoading}
                                                        onClick={() =>
                                                            handleRestore(user.id)
                                                        }
                                                    >
                                                        {actionLoading
                                                            ? 'Processing...'
                                                            : 'Restore'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                ) : (
                    <>
                        <h3>Active User Accounts</h3>

                        {loading ? (
                            <p role="status">Loading user accounts...</p>
                        ) : users.length === 0 ? (
                            <p>No active users found.</p>
                        ) : (
                            <div className="user-table-wrapper">
                                <table>
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>Username</th>
                                            <th>Email</th>
                                            <th>Role</th>
                                            <th>Status</th>
                                            <th>Action</th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {users.map((user) => (
                                            <tr key={user.id}>
                                                <td>{user.id}</td>
                                                <td>{user.username}</td>
                                                <td>{user.email}</td>
                                                <td>{user.role}</td>
                                                <td>
                                                    {user.is_active
                                                        ? 'Active'
                                                        : 'Inactive'}
                                                </td>
                                                <td>
                                                    <button
                                                        type="button"
                                                        disabled={
                                                            actionLoading ||
                                                            user.role === 'Admin'
                                                        }
                                                        onClick={() =>
                                                            handleArchive(user.id)
                                                        }
                                                    >
                                                        {actionLoading
                                                            ? 'Processing...'
                                                            : 'Archive'}
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default UserManagement;
