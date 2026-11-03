
import { Navigate, Outlet, useLocation } from 'react-router-dom';

function ProtectedRoute({ allowedRoles }) {
    const accessToken = localStorage.getItem('accessToken');
    const role = localStorage.getItem('role')?.trim();
    const location = useLocation();

    // Step 1: Check whether the user is logged in
    if (!accessToken || !role) {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('role');

    return <Navigate to="/login" replace state={{ from: location }} />;
}


    // Step 2: Check whether the user's role is allowed
    if (allowedRoles && !allowedRoles.includes(role)) {
        // Send the user to their own dashboard
        const dashboardRoutes = {
            Admin: '/admin-dashboard',
            Teacher: '/teacher-dashboard',
            Student: '/student-dashboard',
            'Registration Officer': '/registration-officer-dashboard',
        };

        const dashboardPath = dashboardRoutes[role];

        // If the role is invalid, return to login
        if (!dashboardPath) {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');

            return (
                <Navigate
                    to="/login"
                    replace
                    state={{ from: location }}
                />
            );
        }

        return <Navigate to={dashboardPath} replace />;
    }

    // Step 3: Allow access
    return <Outlet />;
}

export default ProtectedRoute;
