
import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { loginUser } from '../services/authService';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const navigate = useNavigate();
    const location = useLocation();

    async function handleSubmit(event) {
        event.preventDefault();

        setError('');
        setLoading(true);

        try {
            const data = await loginUser(username, password);

            const dashboardRoutes = {
                Admin: '/admin-dashboard',
                Teacher: '/teacher-dashboard',
                Student: '/student-dashboard',
                'Registration Officer': '/registration-officer-dashboard',
            };


            const dashboardPath = dashboardRoutes[data.role];

            if (!dashboardPath) {
                setError(
                    'Your account does not have a valid role.'
                );
                return;
            }

            localStorage.setItem('accessToken', data.access);
            localStorage.setItem('refreshToken', data.refresh);
            localStorage.setItem('role', data.role);

            const destination = location.state?.from;
            
            navigate(
                 destination
                 ? `${destination.pathname}${destination.search || ''}${destination.hash || ''}`
                 : dashboardPath,
                  { replace: true }
                );

        } catch (err) {
            if (err.response) {
                const responseData = err.response.data;

                setError(
                    responseData.detail ||
                    responseData.error ||
                    responseData.message ||
                    'Login failed. Check your credentials.'
                );
            } else if (err.request) {
                setError(
                    'Cannot connect to the backend. Check that Django is running.'
                );
            } else {
                setError(
                    'Something went wrong. Please try again.'
                );
            }
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-container">
            <form
                className="login-card"
                onSubmit={handleSubmit}
            >
                <h2>Student PMS</h2>
                <p>Sign in to your account</p>

                {error && (
                    <p className="login-error">
                        {error}
                    </p>
                )}

                <div className="form-group">
                    <label htmlFor="username">
                        Username
                    </label>

                    <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(event) =>
                            setUsername(event.target.value)
                        }
                        placeholder="Enter your username"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">
                        Password
                    </label>

                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) =>
                            setPassword(event.target.value)
                        }
                        placeholder="Enter your password"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                >
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                <p>
                    <Link to="/forgot-password">
                        Forgot Password?
                    </Link>
                </p>
            </form>
        </div>
    );
}

export default Login;
