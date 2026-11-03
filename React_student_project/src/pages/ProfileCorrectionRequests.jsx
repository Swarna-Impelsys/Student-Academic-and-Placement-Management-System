
import { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import './ProfileCorrections.css';

function ProfileCorrectionRequests() {
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const [filter, setFilter] = useState('all');
    const [notes, setNotes] = useState({});
    const [reasons, setReasons] = useState({});
    const [processingId, setProcessingId] = useState(null);

    const loadRequests = useCallback(async () => {
        setLoading(true);
        setError('');

        try {
            const response = await api.get('profile-corrections/');
            const data = response.data;

            setRequests(
                Array.isArray(data) ? data : data.results || []
            );
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to load correction requests. Please try again.'
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadRequests();
    }, [loadRequests]);

    const reviewRequest = async (requestId, status) => {
        const decisionNote = notes[requestId]?.trim() || '';
        const rejectionReason = reasons[requestId]?.trim() || '';

        if (status === 'more_evidence_required' && !decisionNote) {
            setError(
                'Enter a note explaining what additional evidence is required.'
            );
            return;
        }

        if (status === 'rejected' && !rejectionReason) {
            setError('Enter a reason before rejecting the request.');
            return;
        }

        if (
            status === 'approved' &&
            !window.confirm(
                'Approve this correction and update the official profile?'
            )
        ) {
            return;
        }

        setProcessingId(requestId);
        setError('');
        setMessage('');

        try {
            await api.patch(
                `profile-corrections/${requestId}/review/`,
                {
                    status,
                    decision_note: decisionNote,
                    rejection_reason: rejectionReason,
                }
            );

            setMessage(`Request #${requestId} updated successfully.`);
            await loadRequests();
        } catch (err) {
            const data = err.response?.data;

            setError(
                data?.detail ||
                data?.error ||
                (typeof data === 'object'
                    ? JSON.stringify(data)
                    : 'Unable to update the request.')
            );
        } finally {
            setProcessingId(null);
        }
    };

    const visibleRequests = requests.filter((request) => {
        return filter === 'all' || request.status === filter;
    });

    const statusLabel = (status) =>
        (status || 'unknown')
            .replaceAll('_', ' ')
            .replace(/\b\w/g, (letter) => letter.toUpperCase());

    if (loading) {
        return (
            <main className="correction-page">
                <p>Loading correction requests...</p>
            </main>
        );
    }

    return (
        <main className="correction-page">
            <div className="correction-heading">
                <div>
                    <p className="correction-eyebrow">
                        REGISTRATION OFFICER
                    </p>
                    <h2>Profile Correction Requests</h2>
                    <p>
                        Review profile changes requested by students and teachers.
                    </p>
                </div>
            </div>

            <section className="correction-panel">
                <div className="officer-filters">
                    <div className="correction-field">
                        <label htmlFor="correction-filter">
                            Filter by status
                        </label>

                        <select
                            id="correction-filter"
                            value={filter}
                            onChange={(event) => setFilter(event.target.value)}
                        >
                            <option value="all">All requests</option>
                            <option value="pending">Pending</option>
                            <option value="under_review">Under Review</option>
                            <option value="more_evidence_required">
                                More Evidence Required
                            </option>
                            <option value="approved">Approved</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </div>

                    <button
                        type="button"
                        className="btn btn-outline-primary"
                        onClick={loadRequests}
                        disabled={loading}
                    >
                        Refresh
                    </button>
                </div>
            </section>

            {error && (
                <div className="correction-alert error" role="alert">
                    {error}
                </div>
            )}

            {message && (
                <div className="correction-alert success" role="status">
                    {message}
                </div>
            )}

            {!error && visibleRequests.length === 0 && (
                <div className="correction-empty">
                    No correction requests found.
                </div>
            )}

            <div className="correction-request-list">
                {visibleRequests.map((request) => {
                    const requester =
                        request.student_name ||
                        request.teacher_name ||
                        'Unknown requester';

                    const isClosed = [
                        'approved',
                        'rejected',
                    ].includes(request.status);

                    return (
                        <section
                            key={request.id}
                            className="correction-request-card"
                        >
                            <div className="request-card-top">
                                <div>
                                    <h3 className="request-id">
                                        Request #{request.id}
                                    </h3>
                                    <p className="request-submitter">
                                        {requester}
                                    </p>
                                </div>

                                <span
                                    className={`correction-status status-${request.status}`}
                                >
                                    {statusLabel(request.status)}
                                </span>
                            </div>

                            <div className="request-values">
                                <p>
                                    <strong>Field:</strong>{' '}
                                    {statusLabel(request.field_name)}
                                </p>

                                <p>
                                    <strong>Previous value:</strong>{' '}
                                    {request.old_value || 'Not available'}
                                </p>

                                <p>
                                    <strong>Requested value:</strong>{' '}
                                    {request.requested_value ||
                                        request.requested_address ||
                                        request.requested_date_of_birth ||
                                        'Not provided'}
                                </p>
                            </div>

                            <div className="request-reason">
                                <strong>Reason:</strong>
                                <p>{request.reason || 'Not provided'}</p>
                            </div>

                            <p className="request-meta">
                                <strong>Submitted:</strong>{' '}
                                {request.submitted_at
                                    ? new Date(
                                        request.submitted_at
                                    ).toLocaleString()
                                    : 'Unknown'}
                            </p>

                            {request.decision_note && (
                                <div className="request-review-note">
                                    <strong>Officer note:</strong>
                                    <p>{request.decision_note}</p>
                                </div>
                            )}

                            {request.rejection_reason && (
                                <div className="rejected-note">
                                    <strong>Rejection reason:</strong>
                                    <p>{request.rejection_reason}</p>
                                </div>
                            )}

                            {Array.isArray(request.documents) &&
                                request.documents.length > 0 && (
                                    <div className="evidence-list">
                                        <h4>Evidence and OCR results</h4>

                                        {request.documents.map((document) => (
                                            <div
                                                key={document.id}
                                                className="evidence-item"
                                            >
                                                <div>
                                                    <p>
                                                        <strong>Document:</strong>{' '}
                                                        {document.document_type}
                                                    </p>

                                                    <p>
                                                        <strong>OCR result:</strong>{' '}
                                                        <span
                                                            className={`ocr-result ocr-${document.ocr_result || 'unable_to_verify'}`}
                                                        >
                                                            {statusLabel(
                                                                document.ocr_result
                                                            )}
                                                        </span>
                                                    </p>

                                                    {document.file && (
                                                        <a
                                                            href={document.file}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                        >
                                                            Open evidence
                                                        </a>
                                                    )}

                                                    {document.ocr_warning && (
                                                        <p className="ocr-warning">
                                                            {document.ocr_warning}
                                                        </p>
                                                    )}

                                                    {document.reviewer_note && (
                                                        <p>
                                                            <strong>Review note:</strong>{' '}
                                                            {document.reviewer_note}
                                                        </p>
                                                    )}

                                                    {document.ocr_text && (
                                                        <details className="ocr-text">
                                                            <summary>
                                                                View extracted OCR text
                                                            </summary>
                                                            <p>{document.ocr_text}</p>
                                                        </details>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}

                            {!isClosed && (
                                <div className="officer-decision">
                                    <div className="correction-field">
                                        <label htmlFor={`note-${request.id}`}>
                                            Decision note / additional evidence instructions
                                        </label>

                                        <textarea
                                            id={`note-${request.id}`}
                                            rows={3}
                                            value={notes[request.id] || ''}
                                            onChange={(event) =>
                                                setNotes((previous) => ({
                                                    ...previous,
                                                    [request.id]: event.target.value,
                                                }))
                                            }
                                            placeholder="Enter instructions or decision notes"
                                        />
                                    </div>

                                    <div className="correction-field">
                                        <label htmlFor={`reason-${request.id}`}>
                                            Rejection reason (required to reject)
                                        </label>

                                        <textarea
                                            id={`reason-${request.id}`}
                                            rows={3}
                                            value={reasons[request.id] || ''}
                                            onChange={(event) =>
                                                setReasons((previous) => ({
                                                    ...previous,
                                                    [request.id]: event.target.value,
                                                }))
                                            }
                                            placeholder="Explain why the request is rejected"
                                        />
                                    </div>

                                    <div className="officer-actions">
                                        <button
                                            type="button"
                                            className="btn btn-outline-primary"
                                            disabled={processingId === request.id}
                                            onClick={() =>
                                                reviewRequest(
                                                    request.id,
                                                    'under_review'
                                                )
                                            }
                                        >
                                            Under Review
                                        </button>

                                        <button
                                            type="button"
                                            className="btn btn-warning"
                                            disabled={processingId === request.id}
                                            onClick={() =>
                                                reviewRequest(
                                                    request.id,
                                                    'more_evidence_required'
                                                )
                                            }
                                        >
                                            Request More Evidence
                                        </button>

                                        <button
                                            type="button"
                                            className="btn btn-success"
                                            disabled={processingId === request.id}
                                            onClick={() =>
                                                reviewRequest(
                                                    request.id,
                                                    'approved'
                                                )
                                            }
                                        >
                                            Approve
                                        </button>

                                        <button
                                            type="button"
                                            className="btn btn-danger"
                                            disabled={processingId === request.id}
                                            onClick={() =>
                                                reviewRequest(
                                                    request.id,
                                                    'rejected'
                                                )
                                            }
                                        >
                                            Reject
                                        </button>
                                    </div>
                                </div>
                            )}
                        </section>
                    );
                })}
            </div>
        </main>
    );
}

export default ProfileCorrectionRequests;
