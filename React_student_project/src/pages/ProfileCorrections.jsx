
import { useCallback, useEffect, useState } from 'react';
import api from '../services/api';
import './ProfileCorrections.css';

function ProfileCorrections() {
    // Existing correction requests
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    // Correction form fields
    const [fieldName, setFieldName] = useState('address');
    const [requestedValue, setRequestedValue] = useState('');
    const [reason, setReason] = useState('');

    // Supporting document
    const [documentType, setDocumentType] = useState('');
    const [documentFile, setDocumentFile] = useState(null);

    // Submission states
    const [submitting, setSubmitting] = useState(false);
    const [uploading, setUploading] = useState(false);

    // Editing state
    const [editingRequestId, setEditingRequestId] = useState(null);

    // Logged-in user role
    const role = localStorage.getItem('role')?.trim().toLowerCase();

    const isStudent = role === 'student';
    const isTeacher = role === 'teacher';
    const canSubmitRequest = isStudent || isTeacher;

    // Check whether the user already has an active request
    const activeStatuses = [
        'pending',
        'under_review',
        'more_evidence_required'
    ];

    const hasActiveRequest = requests.some((request) =>
        activeStatuses.includes(request.status)
    );

    const activeRequest = requests.find((request) =>
        activeStatuses.includes(request.status)
    );

    // =====================================
    // LOAD EXISTING CORRECTION REQUESTS
    // =====================================

    const loadRequests = useCallback(async () => {
        setLoading(true);
        setError('');

        try {
            const response = await api.get('profile-corrections/');
            const data = response.data;

            setRequests(
                Array.isArray(data)
                    ? data
                    : data.results || []
            );
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Unable to load your correction requests.'
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadRequests();
    }, [loadRequests]);

    // =====================================
    // RESET FORM
    // =====================================

    const resetForm = () => {
        setEditingRequestId(null);
        setFieldName(isStudent ? 'address' : 'first_name');
        setRequestedValue('');
        setReason('');
        setDocumentType('');
        setDocumentFile(null);

        const fileInput = document.getElementById('documentFile');

        if (fileInput) {
            fileInput.value = '';
        }
    };

    // =====================================
    // VALIDATE FORM
    // =====================================

    const validateForm = () => {
        if (!requestedValue.trim() || !reason.trim()) {
            setError('Please enter the new value and reason.');
            return false;
        }

        if (documentFile && !documentType) {
            setError('Please select the supporting document type.');
            return false;
        }

        if (documentFile && documentFile.size > 5 * 1024 * 1024) {
            setError('The document must not exceed 5 MB.');
            return false;
        }

        return true;
    };

    // =====================================
    // UPLOAD SUPPORTING DOCUMENT
    // =====================================

    const uploadDocument = async (requestId) => {
        if (!documentFile) {
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();

            formData.append('file', documentFile);
            formData.append('document_type', documentType);

            await api.post(
                `profile-corrections/${requestId}/documents/`,
                formData
            );
        } finally {
            setUploading(false);
        }
    };

    // =====================================
    // SUBMIT NEW CORRECTION REQUEST
    // =====================================

    const submitRequest = async (event) => {
        event.preventDefault();

        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        setError('');
        setMessage('');

        let createdRequest = null;

        try {
            const response = await api.post(
                'profile-corrections/',
                {
                    field_name: fieldName,
                    requested_value: requestedValue.trim(),
                    reason: reason.trim(),
                }
            );

            createdRequest = response.data.request ?? response.data;

            if (documentFile) {
                if (!createdRequest?.id) {
                    throw new Error(
                        'Request was created, but its ID was not returned by the server.'
                    );
                }

                await uploadDocument(createdRequest.id);
            }

            setMessage(
                'Your correction request was submitted successfully.'
            );

            resetForm();

            await loadRequests();

        } catch (err) {
            if (createdRequest?.id) {
                // Request was created, but document upload may have failed.
                setEditingRequestId(createdRequest.id);

                setMessage(
                    `Request #${createdRequest.id} was created, but the document upload failed. Your request details are saved. Submit again to retry the document upload.`
                );

                await loadRequests();
            } else {
                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.error ||
                    err.message ||
                    'Unable to submit your correction request.'
                );
            }
        } finally {
            setSubmitting(false);
            setUploading(false);
        }
    };

    // =====================================
    // EDIT EXISTING CORRECTION REQUEST
    // =====================================

    const editRequest = async (requestId) => {
        if (!validateForm()) {
            return;
        }

        setSubmitting(true);
        setError('');
        setMessage('');

        try {
            await api.patch(
                `profile-corrections/${requestId}/edit/`,
                {
                    field_name: fieldName,
                    requested_value: requestedValue.trim(),
                    reason: reason.trim(),
                }
            );

            // Upload new supporting document if selected
            if (documentFile) {
                await uploadDocument(requestId);
            }

            setMessage(
                `Request #${requestId} updated successfully.`
            );

            resetForm();

            await loadRequests();

        } catch (err) {
            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                err.message ||
                'Unable to update the correction request.'
            );

            // The PATCH may have succeeded even if document upload failed.
            // Check the request before retrying.
        } finally {
            setSubmitting(false);
            setUploading(false);
        }
    };

    // =====================================
    // START EDITING A REQUEST
    // =====================================

    const startEditing = (request) => {
        setEditingRequestId(request.id);
        setFieldName(request.field_name);

        setRequestedValue(
            request.requested_value ||
            request.requested_address ||
            request.requested_date_of_birth ||
            ''
        );

        setReason(request.reason || '');

        setDocumentType('');
        setDocumentFile(null);

        const fileInput = document.getElementById('documentFile');

        if (fileInput) {
            fileInput.value = '';
        }

        setError('');
        setMessage('');

        window.scrollTo({
            top: 0,
            behavior: 'smooth',
        });
    };

    // =====================================
    // HANDLE FORM SUBMISSION
    // =====================================

    const handleFormSubmit = (event) => {
        if (editingRequestId) {
            event.preventDefault();
            editRequest(editingRequestId);
        } else {
            submitRequest(event);
        }
    };

    // =====================================
    // RENDER COMPONENT
    // =====================================

    return (
        <main className="correction-page">

            {/* PAGE HEADING */}

            <div className="correction-heading">
                <div>
                    <p className="correction-eyebrow">
                        PROFILE MANAGEMENT
                    </p>

                    <h2>Request Profile Correction</h2>

                    <p>
                        Submit a correction request if your profile
                        information is incorrect.
                    </p>
                </div>
            </div>

            {/* SUCCESS MESSAGE */}

            {message && (
                <div className="correction-alert success" role="status">
                    {message}
                </div>
            )}

            {/* ERROR MESSAGE */}

            {error && (
                <div className="correction-alert error" role="alert">
                    {error}
                </div>
            )}

            {/* ACTIVE REQUEST INFORMATION */}

            {canSubmitRequest &&
                !loading &&
                hasActiveRequest &&
                !editingRequestId && (
                    <div className="correction-notice" role="status">
                        You already have an active correction request.

                        {activeRequest?.status === 'under_review'
                            ? ' Your request is under review. Please wait for the Registration Officer.'
                            : ' You can edit your existing request below if it is pending or requires more evidence.'}
                    </div>
                )}

            {/* CORRECTION FORM */}

            {canSubmitRequest &&
                !loading &&
                (!hasActiveRequest || editingRequestId) && (

                    <section className="correction-panel">

                        <div className="correction-panel-title">
                            <div>
                                <h3>
                                    {editingRequestId
                                        ? `Edit Request #${editingRequestId}`
                                        : 'Submit a New Correction'}
                                </h3>

                                <p>
                                    Provide the corrected information
                                    and supporting evidence.
                                </p>
                            </div>

                            {editingRequestId && (
                                <button
                                    type="button"
                                    className="btn btn-outline-secondary btn-sm"
                                    onClick={() => {
                                        resetForm();
                                        setError('');
                                        setMessage('');
                                    }}
                                    disabled={submitting || uploading}
                                >
                                    Cancel Editing
                                </button>
                            )}
                        </div>

                        <form
                            onSubmit={handleFormSubmit}
                            className="correction-form"
                        >

                            {/* SELECT FIELD */}

                            <div className="correction-field">

                                <label htmlFor="fieldName">
                                    Select field to correct
                                </label>

                                <select
                                    id="fieldName"
                                    value={fieldName}
                                    onChange={(event) => {
                                        setFieldName(event.target.value);
                                        setRequestedValue('');
                                    }}
                                    required
                                    disabled={submitting}
                                >
                                    {isStudent ? (
                                        <>
                                            <option value="name">Name</option>
                                            <option value="date_of_birth">
                                                Date of Birth
                                            </option>
                                            <option value="address">Address</option>
                                            <option value="phone">Phone</option>
                                            <option value="email">Email</option>
                                        </>
                                    ) : (
                                        <>
                                            <option value="first_name">
                                                First Name
                                            </option>
                                            <option value="last_name">
                                                Last Name
                                            </option>
                                            <option value="email">Email</option>
                                        </>
                                    )}
                                </select>

                            </div>

                            {/* REQUESTED VALUE */}

                            <div className="correction-field">

                                <label htmlFor="requestedValue">
                                    New value
                                </label>

                                <input
                                    id="requestedValue"
                                    type={
                                        fieldName === 'date_of_birth'
                                            ? 'date'
                                            : 'text'
                                    }
                                    value={requestedValue}
                                    onChange={(event) =>
                                        setRequestedValue(event.target.value)
                                    }
                                    placeholder="Enter the correct information"
                                    required
                                    disabled={submitting}
                                />

                            </div>

                            {/* REASON */}

                            <div className="correction-field full">

                                <label htmlFor="correctionReason">
                                    Reason for correction
                                </label>

                                <textarea
                                    id="correctionReason"
                                    rows={3}
                                    value={reason}
                                    onChange={(event) =>
                                        setReason(event.target.value)
                                    }
                                    placeholder="Explain why this information needs correction"
                                    required
                                    disabled={submitting}
                                />

                            </div>

                            {/* DOCUMENT TYPE */}

                            <div className="correction-field">

                                <label htmlFor="documentType">
                                    Supporting document type
                                </label>

                                <select
                                    id="documentType"
                                    value={documentType}
                                    onChange={(event) =>
                                        setDocumentType(event.target.value)
                                    }
                                    disabled={submitting}
                                >
                                    <option value="">
                                        Select document type
                                    </option>
                                    <option value="Birth Certificate">
                                        Birth Certificate
                                    </option>
                                    <option value="School Certificate">
                                        School Certificate
                                    </option>
                                    <option value="Address Proof">
                                        Address Proof
                                    </option>
                                    <option value="Identity Proof">
                                        Identity Proof
                                    </option>
                                    <option value="Other">Other</option>
                                </select>

                            </div>

                            {/* DOCUMENT UPLOAD */}

                            <div className="correction-field">

                                <label htmlFor="documentFile">
                                    Upload supporting document (PDF, JPG or PNG)
                                </label>

                                <input
                                    id="documentFile"
                                    type="file"
                                    accept=".pdf,.jpg,.jpeg,.png"
                                    onChange={(event) =>
                                        setDocumentFile(
                                            event.target.files?.[0] || null
                                        )
                                    }
                                    disabled={submitting}
                                />

                                <small>
                                    Maximum file size: 5 MB.
                                </small>

                            </div>

                            {/* FORM FOOTER */}

                            <div className="correction-form-footer">

                                <span>
                                    Your request will be reviewed by
                                    the Registration Officer.
                                </span>

                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={submitting || uploading}
                                >
                                    {uploading
                                        ? 'Uploading document...'
                                        : submitting
                                            ? 'Submitting...'
                                            : editingRequestId
                                                ? 'Update Correction Request'
                                                : 'Submit Correction Request'}
                                </button>

                            </div>

                        </form>

                    </section>
                )}

            {/* EXISTING CORRECTION REQUESTS */}

            <section className="correction-panel">

                <div className="correction-panel-title">
                    <div>
                        <h3>My Correction Requests</h3>
                        <p>
                            Track the status of your submitted
                            profile corrections.
                        </p>
                    </div>
                </div>

                {loading && (
                    <div className="correction-empty">
                        Loading your correction requests...
                    </div>
                )}

                {!loading && !error && requests.length === 0 && (
                    <div className="correction-empty">
                        You have not submitted any correction
                        requests yet.
                    </div>
                )}

                {!loading && requests.length > 0 && (

                    <div className="correction-request-list">

                        {requests.map((request) => (

                            <section
                                key={request.id}
                                className="correction-request-card"
                            >

                                {/* REQUEST HEADER */}

                                <div className="request-card-top">
                                    <div>
                                        <span className="request-id">
                                            Request #{request.id}
                                        </span>

                                        <h4>{request.field_name?.replaceAll('_', ' ')}</h4>
                                    </div>

                                    <span
                                        className={`correction-status status-${request.status}`}
                                    >
                                        {request.status?.replaceAll('_', ' ')}
                                    </span>
                                </div>

                                {/* REQUEST VALUES */}

                                <div className="request-values">

                                    <div>
                                        <span>Previous value</span>
                                        <strong>
                                            {request.old_value || 'Not available'}
                                        </strong>
                                    </div>

                                    <div>
                                        <span>Requested value</span>
                                        <strong>
                                            {request.requested_value || 'Not provided'}
                                        </strong>
                                    </div>

                                </div>

                                {/* REQUEST REASON */}

                                <p className="request-reason">
                                    <strong>Reason:</strong>{' '}
                                    {request.reason || 'Not provided'}
                                </p>

                                {/* UPLOADED EVIDENCE */}

                                {Array.isArray(request.documents) &&
                                    request.documents.length > 0 && (

                                        <div className="evidence-list">

                                            <h5>Uploaded Evidence</h5>

                                            {request.documents.map((document) => (

                                                <div
                                                    key={document.id}
                                                    className="evidence-item"
                                                >

                                                    <div>
                                                        <strong>
                                                            {document.document_type}
                                                        </strong>

                                                        <span
                                                            className={`ocr-result ${
                                                                document.ocr_result === 'match'
                                                                    ? 'ocr-match'
                                                                    : document.ocr_result === 'mismatch'
                                                                        ? 'ocr-mismatch'
                                                                        : document.ocr_result === 'unable_to_verify'
                                                                            ? 'ocr-unable_to_verify'
                                                                            : ''
                                                            }`}
                                                        >
                                                            {document.ocr_result?.replaceAll('_', ' ') || 'Not processed'}
                                                        </span>

                                                        {document.file && (
                                                            <a
                                                                href={document.file}
                                                                target="_blank"
                                                                rel="noreferrer"
                                                            >
                                                                View uploaded document
                                                            </a>
                                                        )}

                                                        {document.ocr_warning && (
                                                            <p className="ocr-warning">
                                                                {document.ocr_warning}
                                                            </p>
                                                        )}
                                                    </div>

                                                </div>

                                            ))}

                                            <p className="ocr-disclaimer">
                                                OCR results are supporting information
                                                only. The Registration Officer makes
                                                the final verification decision.
                                            </p>

                                        </div>
                                    )}

                                {/* OFFICER NOTES */}

                                {request.decision_note && (
                                    <p className="request-review-note">
                                        <strong>Officer note:</strong>{' '}
                                        {request.decision_note}
                                    </p>
                                )}

                                {request.rejection_reason && (
                                    <p className="request-review-note rejected-note">
                                        <strong>Rejection reason:</strong>{' '}
                                        {request.rejection_reason}
                                    </p>
                                )}

                                {/* SUBMISSION DATE */}

                                <p className="request-meta">
                                    <strong>Submitted:</strong>{' '}
                                    {request.submitted_at
                                        ? new Date(
                                            request.submitted_at
                                        ).toLocaleString()
                                        : 'Unknown'}
                                </p>

                                {/* EDIT REQUEST */}

                                {[
                                    'pending',
                                    'more_evidence_required'
                                ].includes(request.status) && (

                                    <div style={{ marginTop: '14px' }}>
                                        <button
                                            type="button"
                                            className="btn btn-outline-primary"
                                            onClick={() => startEditing(request)}
                                            disabled={submitting || uploading}
                                        >
                                            Edit Request
                                        </button>
                                    </div>

                                )}

                            </section>

                        ))}

                    </div>
                )}

            </section>

        </main>
    );
}

export default ProfileCorrections;
