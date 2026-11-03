
import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

function SetPassword() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    const uid = searchParams.get('uid');
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setMessage('');
        setError('');

        if (!uid || !token) {
            setError(
                'The invitation link is incomplete. Please request a new invitation.'
            );
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        setSubmitting(true);

        try {
            const response = await api.post('set-password/', {
                uid,
                token,
                password,
                confirm_password: confirmPassword,
            });

            setMessage(
                response.data.message ||
                'Password set successfully.'
            );

            setPassword('');
            setConfirmPassword('');

            // Allow the user to read the success message
            // before navigating to the login page.
            setTimeout(() => {
                navigate('/login', { replace: true });
            }, 1500);
        } catch (err) {
            const data = err.response?.data;

            const errorMessage =
                data?.error ||
                data?.detail ||
                data?.message ||
                data?.password ||
                data?.confirm_password;

            setError(
                Array.isArray(errorMessage)
                    ? errorMessage.join(' ')
                    : typeof errorMessage === 'string'
                        ? errorMessage
                        : 'Unable to set the password. Please try again.'
            );
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="set-password-page">
            <h1>Set Your Password</h1>
            <p>Create a password for your Student PMS account.</p>

            {!uid || !token ? (
                <p role="alert">
                    The invitation link is incomplete.
                    Please request a new invitation.
                </p>
            ) : (
                <form onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="password">
                            New Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            autoComplete="new-password"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="confirmPassword">
                            Confirm Password
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

                    <button type="submit" disabled={submitting}>
                        {submitting
                            ? 'Setting Password...'
                            : 'Set Password'}
                    </button>
                </form>
            )}

            {message && <p role="status">{message}</p>}
            {error && <p role="alert">{error}</p>}

            <p>
                Already have a password? <Link to="/login">Log in</Link>
            </p>
        </div>
    );
}

export default SetPassword;
