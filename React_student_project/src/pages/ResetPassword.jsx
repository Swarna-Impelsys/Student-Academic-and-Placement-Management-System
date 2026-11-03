
import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

function ResetPassword() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const uid = searchParams.get('uid');
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setMessage('');
        setError('');

        if (!uid || !token) {
            setError('The reset link is invalid or incomplete.');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setLoading(true);

        try {
            const response = await api.post('set-password/', {
                uid,
                token,
                password,
                confirm_password: confirmPassword,
            });

            setMessage(
                response.data.message || 'Password reset successfully.'
            );

            setTimeout(() => {
                navigate('/login');
            }, 1500);
        } catch (err) {
            const apiError =
                err.response?.data?.error ||
                err.response?.data?.detail ||
                err.response?.data?.message;

            setError(
                Array.isArray(apiError)
                    ? apiError.join(' ')
                    : typeof apiError === 'string'
                        ? apiError
                        : 'Unable to reset your password. Request a new reset link.'
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-container">
            <form className="login-card" onSubmit={handleSubmit}>
                <h2>Reset Password</h2>
                <p>Enter your new password below.</p>

                {message && <p role="status">{message}</p>}

                {error && (
                    <p className="login-error" role="alert">
                        {Array.isArray(error) ? error.join(' ') : error}
                    </p>
                )}

                <div className="form-group">
                    <label htmlFor="password">New Password</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        autoComplete="new-password"
                        required
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="confirmPassword">
                        Confirm New Password
                    </label>
                    <input
                        id="confirmPassword"
                        type="password"
                        value={confirmPassword}
                        onChange={(event) =>
                            setConfirmPassword(event.target.value)
                        }
                        autoComplete="new-password"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                >
                    {loading ? 'Resetting Password...' : 'Reset Password'}
                </button>

                <p>
                    <Link to="/login">Back to Login</Link>
                </p>
            </form>
        </div>
    );
}

export default ResetPassword;
