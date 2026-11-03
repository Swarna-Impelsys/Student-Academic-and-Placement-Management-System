
import { useEffect, useState } from "react";
import api from "../services/api";
import "./AdminDashboard.css";

function AdminDashboard() {
    const [dashboard, setDashboard] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

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
                    "Unable to load dashboard data."
                );
            } finally {
                setLoading(false);
            }
        }

        fetchDashboard();
    }, []);

    if (loading) {
        return <p>Loading dashboard...</p>;
    }

    if (error) {
        return <p role="alert">{error}</p>;
    }

    if (!dashboard) {
        return <p>No dashboard data available.</p>;
    }

    const cards = [
        {
            label: "Total Students",
            value: dashboard.total_students,
        },
        {
            label: "Total Companies",
            value: dashboard.total_companies,
        },
        {
            label: "Active Jobs",
            value: dashboard.total_active_jobs,
        },
        {
            label: "Total Applications",
            value: dashboard.total_applications,
        },
        {
            label: "Total Interviews",
            value: dashboard.total_interviews,
        },
        {
            label: "Selected Applications",
            value: dashboard.total_selected_students,
        },
        {
            label: "Total Vacancies",
            value: dashboard.total_vacancies,
        },
        {
            label: "Average Salary",
            value: `₹${Number(
                dashboard.average_salary || 0
            ).toLocaleString("en-IN")}`,
        },
    ];

    return (
        <main className="admin-dashboard">
            <header className="dashboard-header">
                <div>
                    <h1>Admin Dashboard</h1>
                    <p>
                        Overview of students and placement activities
                    </p>
                </div>
            </header>

            {/* Dashboard Statistics Cards */}
            <section className="dashboard-cards">
                {cards.map((card) => (
                    <article
                        className="dashboard-card"
                        key={card.label}
                    >
                        <p>{card.label}</p>
                        <h2>{card.value ?? 0}</h2>
                    </article>
                ))}
            </section>

            {/* Placement Overview */}
            <section className="dashboard-panel">
                <h2>Placement Overview</h2>

                <p>
                    Placement selection rate:{" "}
                    <strong>
                        {dashboard.placement_percentage ?? 0}%
                    </strong>
                </p>

                <p>
                    Active companies:{" "}
                    <strong>
                        {dashboard.total_active_companies ?? 0}
                    </strong>
                </p>

                <p>
                    Active jobs:{" "}
                    <strong>
                        {dashboard.total_active_jobs ?? 0}
                    </strong>
                </p>
            </section>

            {/* Recent Applications */}
            <section className="dashboard-panel">
                <h2>Recent Applications</h2>

                {!dashboard.recent_applications?.length ? (
                    <p>No applications found.</p>
                ) : (
                    <div className="dashboard-table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Application ID</th>
                                    <th>Student ID</th>
                                    <th>Job ID</th>
                                    <th>Status</th>
                                </tr>
                            </thead>

                            <tbody>
                                {dashboard.recent_applications.map(
                                    (application) => (
                                        <tr key={application.id}>
                                            <td>{application.id}</td>
                                            <td>{application.student}</td>
                                            <td>{application.job}</td>
                                            <td>{application.status}</td>
                                        </tr>
                                    )
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* Upcoming Interviews */}
            <section className="dashboard-panel">
                <h2>Upcoming Interviews</h2>

                {!dashboard.upcoming_interviews?.length ? (
                    <p>No upcoming interviews.</p>
                ) : (
                    <div className="dashboard-table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Interview ID</th>
                                    <th>Application ID</th>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Type</th>
                                    <th>Status</th>
                                </tr>
                            </thead>

                            <tbody>
                                {dashboard.upcoming_interviews.map(
                                    (interview) => (
                                        <tr key={interview.id}>
                                            <td>{interview.id}</td>
                                            <td>{interview.application}</td>
                                            <td>
                                                {interview.interview_date}
                                            </td>
                                            <td>
                                                {interview.interview_time}
                                            </td>
                                            <td>
                                                {interview.interview_type}
                                            </td>
                                            <td>{interview.status}</td>
                                        </tr>
                                    )
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* Course and Company Statistics */}
            <section className="dashboard-two-columns">
                <div className="dashboard-panel">
                    <h2>Students by Course</h2>

                    {!(dashboard.course_statistics || []).length ? (
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
                </div>

                <div className="dashboard-panel">
                    <h2>Selections by Company</h2>

                    {!(dashboard.company_statistics || []).length ? (
                        <p>No company statistics available.</p>
                    ) : (
                        (dashboard.company_statistics || []).map((company) => (
                            <div
                                className="statistics-row"
                                key={company.company}
                            >
                                <span>{company.company}</span>
                                <strong>{company.selected_count}</strong>
                            </div>
                        ))
                    )}
                </div>
            </section>
        </main>
    );
}

export default AdminDashboard;
