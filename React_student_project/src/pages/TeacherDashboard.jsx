
import { useEffect, useState } from "react";
import api from "../services/api";
import "./AdminDashboard.css";

function TeacherDashboard() {
    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // Fetch teacher dashboard data
    useEffect(() => {
        async function fetchDashboard() {
            try {
                const response = await api.get("dashboard/");
                setDashboard(response.data);
            } catch (err) {
                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.error ||
                    err.response?.data?.message ||
                    "Unable to load teacher dashboard."
                );
            } finally {
                setLoading(false);
            }
        }

        fetchDashboard();
    }, []);

    if (loading) {
        return <p>Loading teacher dashboard...</p>;
    }

    if (error) {
        return <p role="alert">{error}</p>;
    }

    if (!dashboard) {
        return <p>No dashboard data available.</p>;
    }

    return (
        <main className="admin-dashboard">
            <header className="dashboard-header">
                <h1>Teacher Dashboard</h1>
                <p>
                    Student academics and placement progress
                </p>
            </header>

            {/* Dashboard summary cards */}
            <section className="dashboard-cards">
                <article className="dashboard-card">
                    <p>Total Students</p>
                    <h2>{dashboard.total_students ?? 0}</h2>
                </article>

                <article className="dashboard-card">
                    <p>Active Jobs</p>
                    <h2>{dashboard.total_active_jobs ?? 0}</h2>
                </article>

                <article className="dashboard-card">
                    <p>Total Applications</p>
                    <h2>{dashboard.total_applications ?? 0}</h2>
                </article>

                <article className="dashboard-card">
                    <p>Upcoming Interviews</p>
                    <h2>
                        {dashboard.upcoming_interviews?.length ?? 0}
                    </h2>
                </article>
            </section>

            {/* Students by course */}
            <section className="dashboard-panel">
                <h2>Students by Course</h2>

                {(dashboard.course_statistics || []).length === 0 ? (
                    <p>No course statistics available.</p>
                ) : (
                    (dashboard.course_statistics || []).map((course) => (
                        <div
                            className="statistics-row"
                            key={course.course}
                        >
                            <span>{course.course}</span>
                            <strong>{course.student_count}</strong>
                        </div>
                    ))
                )}
            </section>

            {/* Upcoming interviews */}
            <section className="dashboard-panel">
                <h2>Upcoming Interviews</h2>

                {(dashboard.upcoming_interviews || []).length === 0 ? (
                    <p>No upcoming interviews.</p>
                ) : (
                    <div className="dashboard-table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Interview ID</th>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Type</th>
                                    <th>Status</th>
                                </tr>
                            </thead>

                            <tbody>
                                {(dashboard.upcoming_interviews || []).map(
                                    (interview) => (
                                        <tr key={interview.id}>
                                            <td>{interview.id}</td>
                                            <td>{interview.interview_date}</td>
                                            <td>{interview.interview_time}</td>
                                            <td>{interview.interview_type}</td>
                                            <td>{interview.status}</td>
                                        </tr>
                                    )
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </main>
    );
}

export default TeacherDashboard;
