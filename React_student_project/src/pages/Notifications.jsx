import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import api from '../services/api';

import {
    getNotifications,
    markNotificationAsRead
} from '../services/notificationService';

function Notifications() {
    const navigate = useNavigate();

    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [updatingId, setUpdatingId] = useState(null);

    const [expandedId, setExpandedId] = useState(null);
    const [declineReasons, setDeclineReasons] = useState({});
    const [declineModeId, setDeclineModeId] = useState(null);
    const [respondingId, setRespondingId] = useState(null);

    // Load notifications
    const loadNotifications = async () => {
        try {
            setLoading(true);
            setError('');

            const data = await getNotifications();

            const notificationList = Array.isArray(data)
                ? data
                : data.results || [];

            setNotifications(notificationList);
        } catch (err) {
            console.error('Error loading notifications:', err);

            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Unable to load notifications. Please try again.'
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadNotifications();
    }, []);

    // Mark notification as read
    const updateNotificationAsRead = async (notification) => {
        if (notification.is_read) return;

        await markNotificationAsRead(notification.id);

        setNotifications((previousNotifications) =>
            previousNotifications.map((item) =>
                item.id === notification.id
                    ? { ...item, is_read: true }
                    : item
            )
        );

        window.dispatchEvent(
            new Event('notifications-updated')
        );
    };

    const handleMarkAsRead = async (notification) => {
        try {
            setUpdatingId(notification.id);
            await updateNotificationAsRead(notification);
        } catch (err) {
            console.error('Error marking notification as read:', err);

            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Unable to mark notification as read.'
            );
        } finally {
            setUpdatingId(null);
        }
    };

    // Open or close notification details
    const handleOpenNotification = async (notification) => {
        setError('');

        setExpandedId((previousId) =>
            previousId === notification.id ? null : notification.id
        );

        if (!notification.is_read) {
            try {
                setUpdatingId(notification.id);
                await updateNotificationAsRead(notification);
            } catch (err) {
                console.error('Error marking notification as read:', err);
                setError(
                    'Unable to mark this notification as read. You can still view its details.'
                );
            } finally {
                setUpdatingId(null);
            }
        }
    };

    // Accept job opportunity
    const handleAccept = async (notification) => {
        if (!notification.job) {
            setError('Job information is not available for this notification.');
            return;
        }

        try {
            setRespondingId(notification.id);
            setError('');

            await api.patch('job-interest-response/', {
                job: notification.job,
                response: 'accepted'
            });

            try {
                await updateNotificationAsRead(notification);
            } catch (readError) {
                console.error('Unable to mark notification as read:', readError);
            }

            navigate(`/applications?job=${notification.job}`);
        } catch (err) {
            console.error('Error accepting job opportunity:', err);

            setError(
                err.response?.data?.error ||
                err.response?.data?.detail ||
                'Unable to accept this job opportunity. Please try again.'
            );
        } finally {
            setRespondingId(null);
        }
    };

    // Open decline reason form
    const handleOpenDeclineForm = (notificationId) => {
        setError('');
        setDeclineModeId(notificationId);

        setDeclineReasons((previous) => ({
            ...previous,
            [notificationId]: ''
        }));
    };

    // Cancel decline
    const handleCancelDecline = () => {
        setDeclineModeId(null);
    };

    // Submit decline with reason
    const handleDecline = async (notification) => {
        const reason = (declineReasons[notification.id] || '').trim();

        if (!reason) {
            setError('Please enter a reason before declining this opportunity.');
            return;
        }

        if (!notification.job) {
            setError('Job information is not available for this notification.');
            return;
        }

        try {
            setRespondingId(notification.id);
            setError('');

            await api.patch('job-interest-response/', {
                job: notification.job,
                response: 'declined',
                decline_reason: reason
            });

            try {
                await updateNotificationAsRead(notification);
            } catch (readError) {
                console.error('Unable to mark notification as read:', readError);
            }

            setNotifications((previousNotifications) =>
                previousNotifications.map((item) =>
                    item.id === notification.id
                        ? {
                            ...item,
                            interest_response: 'declined'
                        }
                        : item
                )
            );

            setDeclineModeId(null);
            setExpandedId(null);

            setDeclineReasons((previous) => ({
                ...previous,
                [notification.id]: ''
            }));

        } catch (err) {
            console.error('Error declining job opportunity:', err);

            setError(
                err.response?.data?.error ||
                err.response?.data?.detail ||
                'Unable to decline this job opportunity. Please try again.'
            );
        } finally {
            setRespondingId(null);
        }
    };

    const unreadCount = notifications.filter(
        (notification) => !notification.is_read
    ).length;

    const formatDate = (dateValue) => {
        if (!dateValue) return 'Date unavailable';

        const date = new Date(dateValue);

        if (Number.isNaN(date.getTime())) {
            return 'Date unavailable';
        }

        return date.toLocaleString();
    };

    const formatDeadline = (dateValue) => {
        if (!dateValue) return 'Not specified';

        const date = new Date(`${dateValue}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            return 'Not specified';
        }

        return date.toLocaleDateString('en-IN');
    };

    if (loading) {
        return (
            <div className="page-container notification-page">
                <div className="notification-loading">
                    Loading notifications...
                </div>
            </div>
        );
    }

    return (
        <div className="page-container notification-page">

            {/* Page Header */}
            <div className="notification-page-header">
                <div>
                    <span className="notification-eyebrow">
                        STUDENT PMS
                    </span>

                    <h2>My Notifications</h2>

                    <p>
                        Stay updated with your job opportunities and activities.
                    </p>
                </div>

                <div className="notification-header-actions">
                    <div className="notification-unread-count">
                        <span>{unreadCount}</span>
                        <small>Unread</small>
                    </div>

                    <button
                        type="button"
                        className="notification-refresh-btn"
                        onClick={loadNotifications}
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="notification-alert" role="alert">
                    {error}
                </div>
            )}

            {/* Empty State */}
            {!error && notifications.length === 0 && (
                <div className="notification-empty">
                    <div className="notification-empty-icon">🔔</div>
                    <h3>No notifications yet</h3>
                    <p>
                        You will see job opportunities and important updates here.
                    </p>
                </div>
            )}

            {/* Notifications List */}
            <div className="notifications-list">

                {notifications.map((notification) => {
                    const isInterviewNotification =
                    notification.notification_type === 'interview';

                    const isJobNotification = Boolean(
                         notification.job && notification.job_title
                        ) && !isInterviewNotification;

                    const isExpanded =
                        expandedId === notification.id;

                    const isResponded = Boolean(
                        notification.interest_response === 'accepted' ||
                        notification.interest_response === 'declined'
                    );

                    const isDeclining =
                        declineModeId === notification.id;

                    return (
                        <article
                            key={notification.id}
                            className={`notification-card ${
                                notification.is_read ? 'read' : 'unread'
                            }`}
                        >

                            {/* Notification Summary */}
                            <div className="notification-card-header">

                                <div className="notification-card-content">

                                    <div className="notification-type-row">
                                        <span className="notification-type">
                                            {isInterviewNotification
                                            ? 'Interview'
                                            : isJobNotification
                                             ? 'Job Opportunity'
                                             : (notification.notification_type || 'Notification')}
                                             </span>

                                        {!notification.is_read && (
                                            <span className="notification-new-badge">
                                                New
                                            </span>
                                        )}
                                    </div>

                                    <p className="notification-message">
                                        {notification.message}
                                    </p>

                                    <span className="notification-date">
                                        {formatDate(notification.created_at)}
                                    </span>

                                </div>

                                <div className="notification-card-actions">

                                    {(isJobNotification || isInterviewNotification) && (
                                        <button
                                            type="button"
                                            className="notification-view-btn"
                                            onClick={() => handleOpenNotification(notification)}
                                        >
                                            {isExpanded ? 'Hide Details' : 'View Details'}
                                        </button>
                                    )}


                                    {notification.is_read ? (
                                        <span className="notification-read-label">
                                            ✓ Read
                                        </span>
                                    ) : (
                                        <button
                                            type="button"
                                            className="notification-read-btn"
                                            disabled={updatingId === notification.id}
                                            onClick={() =>
                                                handleMarkAsRead(notification)
                                            }
                                        >
                                            {updatingId === notification.id
                                                ? 'Updating...'
                                                : 'Mark as read'}
                                        </button>
                                    )}

                                </div>
                            </div>

                            {/* Expanded Job Details */}
                            {isJobNotification && isExpanded && (
                                <div className="notification-job-card">

                                    {/* Job Heading */}
                                    <div className="notification-job-header">

                                        <div>
                                            <span className="notification-job-label">
                                                JOB OPPORTUNITY
                                            </span>

                                            <h3>{notification.job_title}</h3>

                                            <p className="notification-company-name">
                                                {notification.company_name ||
                                                    'Company not specified'}
                                            </p>
                                        </div>

                                        {notification.company_website && (
                                            <a
                                                className="notification-company-link"
                                                href={notification.company_website}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                Visit Company Website ↗
                                            </a>
                                        )}

                                    </div>

                                    {/* Description */}
                                    <div className="notification-job-section">
                                        <h4>Job Description</h4>

                                        <p className="notification-description">
                                            {notification.job_description ||
                                                'No job description available.'}
                                        </p>
                                    </div>

                                    {/* Job Information */}
                                    <div className="notification-job-section">

                                        <h4>Job Details</h4>

                                        <div className="notification-job-info">

                                            <div className="notification-info-item">
                                                <span>Job Role</span>
                                                <strong>
                                                    {notification.job_title || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Company</span>
                                                <strong>
                                                    {notification.company_name || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Job Type</span>
                                                <strong>
                                                    {notification.job_type || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Location</span>
                                                <strong>
                                                    {notification.job_location || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Salary</span>
                                                <strong>
                                                    {notification.job_salary != null
                                                        ? `₹${Number(
                                                            notification.job_salary
                                                        ).toLocaleString('en-IN')}`
                                                        : 'Not specified'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Vacancies</span>
                                                <strong>
                                                    {notification.job_vacancies ?? '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Placement Drive</span>
                                                <strong>
                                                    {notification.drive_title || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item notification-deadline-item">
                                                <span>Last Date to Apply</span>
                                                <strong>
                                                    {formatDeadline(
                                                        notification.application_end_date
                                                    )}
                                                </strong>
                                            </div>

                                        </div>
                                    </div>

                                    {/* Required Skills */}
                                    <div className="notification-job-section">

                                        <h4>Required Skills</h4>

                                        {notification.required_skills?.length > 0 ? (
                                            <div className="notification-skills">
                                                {notification.required_skills.map(
                                                    (skill, index) => (
                                                        <span key={`${skill}-${index}`}>
                                                            {skill}
                                                        </span>
                                                    )
                                                )}
                                            </div>
                                        ) : (
                                            <p className="notification-no-skills">
                                                No specific skills listed.
                                            </p>
                                        )}

                                    </div>

                                    {/* Accept / Decline */}
                                    <div className="notification-response-section">

                                        {isResponded ? (
                                            <div className="notification-response-status">
                                                You have already{' '}
                                                <strong>
                                                    {notification.interest_response}
                                                </strong>{' '}
                                                this opportunity.
                                            </div>
                                        ) : (
                                            <>
                                                <h4>Your Response</h4>

                                                {!isDeclining ? (
                                                    <div className="notification-job-actions">

                                                        <button
                                                            type="button"
                                                            className="notification-accept-btn"
                                                            disabled={
                                                                respondingId === notification.id
                                                            }
                                                            onClick={() =>
                                                                handleAccept(notification)
                                                            }
                                                        >
                                                            {respondingId === notification.id
                                                                ? 'Submitting...'
                                                                : '✓ Accept Opportunity'}
                                                        </button>

                                                        <button
                                                            type="button"
                                                            className="notification-decline-btn"
                                                            disabled={
                                                                respondingId === notification.id
                                                            }
                                                            onClick={() =>
                                                                handleOpenDeclineForm(
                                                                    notification.id
                                                                )
                                                            }
                                                        >
                                                            Decline
                                                        </button>

                                                    </div>
                                                ) : (
                                                    <div className="notification-decline-form">

                                                        <label>
                                                            Reason for declining
                                                        </label>

                                                        <textarea
                                                            rows="3"
                                                            value={
                                                                declineReasons[notification.id] || ''
                                                            }
                                                            onChange={(event) =>
                                                                setDeclineReasons(
                                                                    (previous) => ({
                                                                        ...previous,
                                                                        [notification.id]:
                                                                            event.target.value
                                                                    })
                                                                )
                                                            }
                                                            placeholder="Please explain why you are declining this opportunity..."
                                                        />

                                                        <div className="notification-decline-actions">

                                                            <button
                                                                type="button"
                                                                className="notification-submit-decline-btn"
                                                                disabled={
                                                                    respondingId === notification.id ||
                                                                    !(declineReasons[notification.id] || '').trim()
                                                                }
                                                                onClick={() =>
                                                                    handleDecline(notification)
                                                                }
                                                            >
                                                                {respondingId === notification.id
                                                                    ? 'Submitting...'
                                                                    : 'Submit Decline'}
                                                            </button>

                                                            <button
                                                                type="button"
                                                                className="notification-cancel-btn"
                                                                disabled={
                                                                    respondingId === notification.id
                                                                }
                                                                onClick={handleCancelDecline}
                                                            >
                                                                Cancel
                                                            </button>

                                                        </div>

                                                    </div>
                                                )}
                                            </>
                                        )}

                                    </div>

                                </div>
                            )}

                            {/* Expanded Interview Details */}
                            {isInterviewNotification && isExpanded && (
                                <div className="notification-job-card">

                                    <div className="notification-job-header">
                                        <div>
                                            <span className="notification-job-label">
                                                INTERVIEW DETAILS
                                            </span>

                                            <h3>
                                                {notification.job_title || 'Interview'}
                                            </h3>

                                            <p className="notification-company-name">
                                                {notification.company_name || 'Company not specified'}
                                            </p>
                                        </div>

                                        <span className="notification-type">
                                            {notification.interview_status || 'Scheduled'}
                                        </span>
                                    </div>

                                    <div className="notification-job-section">
                                        <h4>Interview Information</h4>

                                        <div className="notification-job-info">

                                            <div className="notification-info-item">
                                                <span>Job Role</span>
                                                <strong>
                                                    {notification.job_title || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Company</span>
                                                <strong>
                                                    {notification.company_name || '—'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Interview Date</span>
                                                <strong>
                                                    {formatDeadline(notification.interview_date)}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Interview Time</span>
                                                <strong>
                                                    {notification.interview_time || 'Not specified'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Interview Mode</span>
                                                <strong>
                                                    {notification.interview_type
                                                        ? notification.interview_type.charAt(0).toUpperCase() +
                                                          notification.interview_type.slice(1)
                                                        : 'Not specified'}
                                                </strong>
                                            </div>

                                            <div className="notification-info-item">
                                                <span>Interview Status</span>
                                                <strong>
                                                    {notification.interview_status || 'Not specified'}
                                                </strong>
                                            </div>

                                        </div>
                                    </div>

                                    {/* Online Interview */}
                                    {notification.interview_type === 'online' && (
                                        <div className="notification-job-section">
                                            <h4>Online Meeting</h4>

                                            {notification.meeting_link ? (
                                                <a
                                                    href={notification.meeting_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="notification-company-link"
                                                >
                                                    Join Interview Meeting ↗
                                                </a>
                                            ) : (
                                                <p>Meeting link not available.</p>
                                            )}
                                        </div>
                                    )}

                                    {/* Offline Interview */}
                                    {notification.interview_type === 'offline' && (
                                        <div className="notification-job-section">
                                            <h4>Interview Location</h4>

                                            <p>
                                                {notification.interview_location ||
                                                    'Interview location not specified.'}
                                            </p>
                                        </div>
                                    )}

                                </div>
                            )}

                        </article>
                    );
                })}

            </div>
        </div>
    );
}

export default Notifications;