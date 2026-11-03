
import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    async function handleSubmit(event) {
        event.preventDefault();

        setMessage('');
        setError('');
        setLoading(true);

        try {
            const response = await api.post(
                'forgot-password/',
                { email }
            );

            setMessage(
                response.data.message ||
                'If an account exists for that email, password reset instructions will be sent.'
            );

        } catch (err) {
            setError(
                err.response?.data?.error ||
                'Unable to process your request. Please try again.'
            );
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
                <h2>Forgot Password</h2>

                <p>
                    Enter the email address associated
                    with your account.
                </p>

                {message && (
                    <p role="status">{message}</p>
                )}

                {error && (
                    <p className="login-error" role="alert">
                        {error}
                    </p>
                )}

                <div className="form-group">
                    <label htmlFor="email">Email Address</label>

                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(event) =>
                            setEmail(event.target.value)
                        }
                        placeholder="Enter your email"
                        autoComplete="email"
                        required
                    />
                </div>

                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                >
                    {loading
                        ? 'Sending Request...'
                        : 'Send Reset Link'}
                </button>

                <p>
                    <Link to="/login">Back to Login</Link>
                </p>
            </form>
        </div>
    );
}

export default ForgotPassword;
