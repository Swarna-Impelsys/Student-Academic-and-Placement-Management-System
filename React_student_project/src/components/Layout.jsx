
import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';

import { logoutUser } from '../services/logoutService';
import { getUnreadNotifications } from '../services/notificationService';

function Layout() {
    const role = localStorage.getItem('role')?.trim().toLowerCase();

    const navigate = useNavigate();
    const location = useLocation();

    const [unreadCount, setUnreadCount] = useState(0);

    // Fetch unread notification count
    useEffect(() => {
        if (role !== 'student') {
            setUnreadCount(0);
            return;
        }

        let isMounted = true;

        async function loadUnreadCount() {
            try {
                const data = await getUnreadNotifications();

                const notifications = Array.isArray(data)
                    ? data
                    : data.results || [];

                const count = typeof data.count === 'number'
                    ? data.count
                    : notifications.length;

                if (isMounted) {
                    setUnreadCount(count);
                }
            } catch (error) {
                console.error(
                    'Failed to load unread notifications:',
                    error
                );
            }
        }

        // Initial fetch
        loadUnreadCount();

        // Listen for notification updates
        window.addEventListener(
            'notifications-updated',
            loadUnreadCount
        );

        // Refresh every 30 seconds
        const interval = setInterval(loadUnreadCount, 30000);

        return () => {
            isMounted = false;

            window.removeEventListener(
                'notifications-updated',
                loadUnreadCount
            );

            clearInterval(interval);
        };
    }, [role, location.pathname]);

    async function handleLogout() {
        const refreshToken = localStorage.getItem('refreshToken');

        try {
            await logoutUser(refreshToken);
        } catch (error) {
            console.error('Logout API failed:', error);
        } finally {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');

            navigate('/login', { replace: true });
        }
    }

    return (
        <div className="layout">
            <aside className="sidebar">
                <h2>Student PMS</h2>

                <nav>
                    {/* ADMIN */}
                    {role === 'admin' && (
                        <>
                            <NavLink to="/admin-dashboard">Dashboard</NavLink>
                            <NavLink to="/students">Students</NavLink>
                            <NavLink to="/academic-records">Academic Records</NavLink>
                            <NavLink to="/jobs">Jobs</NavLink>
                            <NavLink to="/applications">Applications</NavLink>
                            <NavLink to="/certifications">Certifications</NavLink>
                            <NavLink to="/courses">Courses</NavLink>
                            <NavLink to="/companies">Companies</NavLink>
                            <NavLink to="/subject-configuration">Subject Configuration</NavLink>
                            <NavLink to="/user-management">User Management</NavLink>
                            <NavLink to="/placement-drives">Placement Drives</NavLink>
                            <NavLink to="/interviews">Interviews</NavLink>
                            <NavLink to="/selections">Selections</NavLink>
                        </>
                    )}

                    {/* REGISTRATION OFFICER */}
                    {role === 'registration officer' && (
                        <>
                            <NavLink to="/registration-officer-dashboard">
                                Dashboard
                            </NavLink>
                            <NavLink to="/students">Students</NavLink>
                            <NavLink to="/academic-records">Academic Records</NavLink>
                            <NavLink to="/jobs">Jobs</NavLink>
                            <NavLink to="/profile-corrections">
                                Profile Correction Requests
                            </NavLink>
                            <NavLink to="/eligibility-coordination">
                                Eligibility Coordination
                            </NavLink>
                            <NavLink to="/applications">Applications</NavLink>
                            <NavLink to="/companies">Companies</NavLink>
                            <NavLink to="/placement-drives">Placement Drives</NavLink>
                            <NavLink to="/interviews">Interviews</NavLink>
                            <NavLink to="/selections">Selections</NavLink>
                        </>
                    )}

                    {/* TEACHER */}
                    {role === 'teacher' && (
                        <>
                            <NavLink to="/teacher-dashboard">Dashboard</NavLink>
                            <NavLink to="/profile-correction-request">
                             Request Profile Correction
                             </NavLink>
                            <NavLink to="/students">Assigned Students</NavLink>
                            <NavLink to="/academic-records">Academic Records</NavLink>
                            <NavLink to="/jobs">Jobs</NavLink>
                            <NavLink to="/applications">Applications</NavLink>
                            <NavLink to="/certifications">Certifications</NavLink>
                            <NavLink to="/courses">Courses</NavLink>
                            <NavLink to="/companies">Companies</NavLink>
                            <NavLink to="/placement-drives">Placement Drives</NavLink>
                            <NavLink to="/eligibility">Eligibility Criteria</NavLink>
                            <NavLink to="/interviews">Interviews</NavLink>
                            <NavLink to="/selections">Selections</NavLink>
                        </>
                    )}

                    {/* STUDENT */}
                    {role === 'student' && (
                        <>
                            <NavLink to="/student-dashboard">Dashboard</NavLink>
                            <NavLink to="/profile-correction-request">
                            Request Profile Correction
                            </NavLink>
                            <NavLink to="/subject-selection">Subject Selection</NavLink>
                            <NavLink to="/academic-records">Academic Records</NavLink>
                            <NavLink to="/jobs">Jobs</NavLink>
                            <NavLink to="/companies">Companies</NavLink>
                            <NavLink to="/applications">Applications</NavLink>
                            <NavLink to="/skills">My Skills</NavLink>
                            <NavLink to="/certifications">My Certifications</NavLink>
                            <NavLink to="/placement-drives">Placement Drives</NavLink>
                            <NavLink to="/interviews">Interviews</NavLink>
                            <NavLink to="/selections">Selections</NavLink>
                        </>
                    )}
                </nav>

                <button
                    type="button"
                    className="btn btn-primary"
                    onClick={handleLogout}
                >
                    Logout
                </button>
            </aside>

            <div className="main-area">
                <header className="topbar">
                    <h1>Academic & Placement Management</h1>

                    {/* STUDENT NOTIFICATION BELL */}
                    {role === 'student' && (
                        <button
                            type="button"
                            className="notification-bell"
                            onClick={() => navigate('/notifications')}
                            aria-label={`Notifications, ${unreadCount} unread`}
                            title="Notifications"
                        >
                            <span className="bell-icon">🔔</span>

                            {unreadCount > 0 && (
                                <span className="notification-badge">
                                    {unreadCount > 99 ? '99+' : unreadCount}
                                </span>
                            )}
                        </button>
                    )}
                </header>

                <main className="page-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

export default Layout;
