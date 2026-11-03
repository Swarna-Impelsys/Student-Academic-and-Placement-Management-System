
import { useEffect, useState } from 'react';
import api from '../services/api';
import useApi from '../hooks/useApi';

function StudentDashboard() {
    const [dashboard, setDashboard] = useState(null);
    const { loading, error, execute } = useApi();

    const [isEditing, setIsEditing] = useState(false);
    const [saving, setSaving] = useState(false);

    const [formData, setFormData] = useState({
        address: '',
        date_of_birth: ''
    });

    const [saveMessage, setSaveMessage] = useState('');

    useEffect(() => {
        async function fetchDashboard() {
            try {
                const response = await execute(() =>
                    api.get('student-dashboard/')
                );

                setDashboard(response.data);
            } catch (err) {
                // useApi already stores the error message.
                console.error('Failed to load student dashboard:', err);
            }
        }

        fetchDashboard();
    }, [execute]);

    if (loading) {
        return <p>Loading student dashboard...</p>;
    }

    if (error) {
        return <p role="alert">Error: {error}</p>;
    }

    if (!dashboard) {
        return <p>No dashboard data available.</p>;
    }

    // Safe fallbacks if backend data is missing.
    const student = dashboard.student || {};
    const summary = dashboard.summary || {};

    function handleEditClick() {
        setFormData({
            address: student.address || '',
            date_of_birth: student.date_of_birth || ''
        });

        setSaveMessage('');
        setIsEditing(true);
    }

    async function handleSaveProfile(event) {
        event.preventDefault();
        setSaveMessage('');
        setSaving(true);

        try {
            await api.post('profile-corrections/', {
                requested_address: formData.address,
                requested_date_of_birth:
                    formData.date_of_birth || null
            });

            setSaveMessage(
                'Correction request submitted successfully! Your profile will be updated after Registration Officer approval.'
            );

            setIsEditing(false);
        } catch (err) {
            const data = err.response?.data;

            setSaveMessage(
                data?.detail ||
                data?.error ||
                data?.requested_address?.[0] ||
                data?.requested_date_of_birth?.[0] ||
                'Failed to submit correction request. Please try again.'
            );
        } finally {
            setSaving(false);
        }
    }

    return (
        <div className="student-dashboard">
            <header className="student-dashboard-header">
                <div>
                    <p className="dashboard-eyebrow">
                        ACADEMIC &amp; PLACEMENT MANAGEMENT
                    </p>

                    <h1>Student Dashboard</h1>

                    <p className="dashboard-welcome">
                        Welcome back, <strong>{student.Name}</strong>!
                    </p>
                </div>
            </header>

            <section className="student-profile-card">
                <div className="student-avatar">
                    {student.Name?.charAt(0)?.toUpperCase() || 'S'}
                </div>

                <div className="student-profile-info">
                    <h2>My Profile</h2>

                    <p>
                        <strong>Name:</strong> {student.Name}
                    </p>

                    <p>
                        <strong>Email:</strong> {student.Email}
                    </p>

                    <p>
                        <strong>Course:</strong> {student.course_name}
                    </p>

                    {!isEditing ? (
                        <>
                            <p>
                                <strong>Address:</strong>{' '}
                                {student.address || 'Not provided'}
                            </p>

                            <p>
                                <strong>Date of Birth:</strong>{' '}
                                {student.date_of_birth || 'Not provided'}
                            </p>

                            <button
                                type="button"
                                onClick={handleEditClick}
                            >
                                Edit Profile
                            </button>
                        </>
                    ) : (
                        <form onSubmit={handleSaveProfile}>
                            <div>
                                <label htmlFor="address">
                                    Address
                                </label>

                                <input
                                    id="address"
                                    type="text"
                                    value={formData.address}
                                    onChange={(event) =>
                                        setFormData((previous) => ({
                                            ...previous,
                                            address: event.target.value
                                        }))
                                    }
                                />
                            </div>

                            <div>
                                <label htmlFor="date_of_birth">
                                    Date of Birth
                                </label>

                                <input
                                    id="date_of_birth"
                                    type="date"
                                    value={formData.date_of_birth || ''}
                                    onChange={(event) =>
                                        setFormData((previous) => ({
                                            ...previous,
                                            date_of_birth:
                                                event.target.value
                                        }))
                                    }
                                />
                            </div>

                            <button type="submit" disabled={saving}>
                                {saving
                                    ? 'Submitting...'
                                    : 'Submit Correction Request'}
                            </button>

                            <button
                                type="button"
                                onClick={() => setIsEditing(false)}
                                disabled={saving}
                            >
                                Cancel
                            </button>
                        </form>
                    )}

                    {saveMessage && (
                        <p role="status">{saveMessage}</p>
                    )}
                </div>
            </section>

            <section className="student-summary-section">
                <h2>My Summary</h2>

                <div className="student-summary-grid">
                    <div className="student-summary-card">
                        <span className="summary-icon">📚</span>
                        <p>Academic Records</p>
                        <h3>{summary.total_academic_records ?? 0}</h3>
                    </div>

                    <div className="student-summary-card">
                        <span className="summary-icon">📄</span>
                        <p>Applications</p>
                        <h3>{summary.total_applications ?? 0}</h3>
                    </div>

                    <div className="student-summary-card">
                        <span className="summary-icon">⏳</span>
                        <p>Pending Applications</p>
                        <h3>{summary.pending_applications ?? 0}</h3>
                    </div>

                    <div className="student-summary-card">
                        <span className="summary-icon">🗓️</span>
                        <p>Interviews</p>
                        <h3>{summary.total_interviews ?? 0}</h3>
                    </div>

                    <div className="student-summary-card">
                        <span className="summary-icon">🏆</span>
                        <p>Selections</p>
                        <h3>{summary.total_selections ?? 0}</h3>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default StudentDashboard;
