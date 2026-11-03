
import { useEffect, useState } from 'react';
import {
    getSelections,
    createSelection,
    updateSelection,
    deleteSelection,
    uploadSelectionResults,
} from '../services/selectionService';
import { getApplications } from '../services/applicationService';
import { getStudents } from '../services/studentService';
import { getJobs } from '../services/jobService';
import '../App.css';

const emptyForm = {
    application: '',
    status: 'pending',
    offer_date: '',
    joining_date: '',
    package: '',
    remarks: '',
};

function getList(data) {
    if (Array.isArray(data)) return data;

    return (
        data?.results ||
        data?.selections ||
        data?.applications ||
        data?.data ||
        []
    );
}

function Selections() {
    // Normalize the role consistently.
    const role = (localStorage.getItem('role') || '')
        .trim()
        .toLowerCase();

    const isAdmin = role === 'admin';

    const [selections, setSelections] = useState([]);
    const [applications, setApplications] = useState([]);
    const [students, setStudents] = useState([]);
    const [jobs, setJobs] = useState([]);

    const [form, setForm] = useState(emptyForm);
    const [editingId, setEditingId] = useState(null);

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Excel upload states.
    const [uploadFile, setUploadFile] = useState(null);
    const [uploadJobId, setUploadJobId] = useState('');
    const [confirmCompleteList, setConfirmCompleteList] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);

    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const selectionData = await getSelections();
            setSelections(getList(selectionData));

            // Only Admin needs these lists for creating/editing selections.
            if (isAdmin) {
                const [
                    applicationData,
                    studentData,
                    jobData,
                ] = await Promise.all([
                    getApplications(),
                    getStudents(),
                    getJobs(),
                ]);

                setApplications(getList(applicationData));
                setStudents(getList(studentData));
                setJobs(getList(jobData));
            }

            return true;
        } catch (err) {
            console.error(
                'Selection loading error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Could not load selection data. Check your backend and login.'
            );

            return false;
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadData();

        // Load data once when this component mounts.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    function handleChange(event) {
        const { name, value } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: value,
            ...(name === 'status' && value === 'rejected'
                ? {
                    offer_date: '',
                    joining_date: '',
                    package: '',
                }
                : {}),
        }));
    }

    function resetForm() {
        setForm(emptyForm);
        setEditingId(null);
    }

    function getApplicationLabel(application) {
        const studentValue = application.student;
        const jobValue = application.job;

        const student = students.find(
            (item) =>
                String(item.id) ===
                String(
                    typeof studentValue === 'object'
                        ? studentValue?.id
                        : studentValue
                )
        );

        const job = jobs.find(
            (item) =>
                String(item.id) ===
                String(
                    typeof jobValue === 'object'
                        ? jobValue?.id
                        : jobValue
                )
        );

        const studentName =
            (typeof studentValue === 'object'
                ? studentValue?.Name ||
                studentValue?.name ||
                studentValue?.full_name
                : null) ||
            student?.Name ||
            student?.name ||
            `Student #${typeof studentValue === 'object'
                ? studentValue?.id ?? '—'
                : studentValue ?? '—'
            }`;

        const jobTitle =
            (typeof jobValue === 'object'
                ? jobValue?.title
                : null) ||
            job?.title ||
            `Job #${typeof jobValue === 'object'
                ? jobValue?.id ?? '—'
                : jobValue ?? '—'
            }`;

        return `${studentName} — ${jobTitle} (Application #${application.id})`;
    }

    function getApplicationDetails(applicationId) {
        const application = applications.find(
            (item) => String(item.id) === String(applicationId?.id ?? applicationId)
        );

        // The API may provide only an application ID to non-Admin users.
        return application
            ? getApplicationLabel(application)
            : `Application #${applicationId?.id ?? applicationId ?? '—'}`;
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!isAdmin) return;

        setError('');
        setSuccess('');

        // Selected candidates must have all three offer details.
        if (
            form.status === 'selected' &&
            (!form.package || !form.offer_date || !form.joining_date)
        ) {
            setError(
                'Package (LPA), offer date, and joining date are required for selected candidates.'
            );
            return;
        }

        if (!form.application) {
            setError('Please select an application.');
            return;
        }

        const payload = {
            application: Number(form.application),
            status: form.status,
            offer_date: form.offer_date || null,
            joining_date: form.joining_date || null,
            package: form.package === '' ? null : Number(form.package),
            remarks: form.remarks.trim(),
        };

        setSaving(true);

        const wasEditing = Boolean(editingId);

        try {
            // Step 1: Save the selection record.
            if (wasEditing) {
                await updateSelection(editingId, payload);
            } else {
                await createSelection(payload);
            }

            resetForm();

            // Step 2: Refresh the list separately.
            const refreshed = await loadData();

            if (refreshed) {
                setSuccess(
                    wasEditing
                        ? 'Selection record updated successfully.'
                        : 'Selection record created successfully.'
                );
            } else {
                setSuccess(
                    wasEditing
                        ? 'Selection record was updated successfully, but the list could not be refreshed. Please refresh the page.'
                        : 'Selection record was created successfully, but the list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            console.error(
                'Selection save error:',
                err.response?.data || err
            );

            const data = err.response?.data;

            setError(
                data
                    ? Object.entries(data)
                        .map(([field, messages]) =>
                            `${field}: ${Array.isArray(messages)
                                ? messages.join(', ')
                                : typeof messages === 'object'
                                    ? JSON.stringify(messages)
                                    : messages
                            }`
                        )
                        .join(' | ')
                    : 'Could not save the selection record.'
            );
        } finally {
            setSaving(false);
        }
    }

    function startEdit(selection) {
        if (!isAdmin) return;

        setEditingId(selection.id);

        setForm({
            application: String(
                selection.application?.id ??
                selection.application ??
                ''
            ),
            status: selection.status || 'pending',
            offer_date: selection.offer_date || '',
            joining_date: selection.joining_date || '',
            package: selection.package ?? '',
            remarks: selection.remarks || '',
        });

        setError('');
        setSuccess('');

        window.scrollTo({
            top: 0,
            behavior: 'smooth',
        });
    }

    async function handleDelete(id) {
        if (!isAdmin) return;

        if (
            !window.confirm(
                'Are you sure you want to delete this selection record?'
            )
        ) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            // Step 1: Delete the selection record.
            await deleteSelection(id);

            if (String(editingId) === String(id)) {
                resetForm();
            }

            // Step 2: Refresh separately.
            const refreshed = await loadData();

            if (refreshed) {
                setSuccess('Selection record deleted successfully.');
            } else {
                setSuccess(
                    'Selection record was deleted successfully, but the list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            console.error(
                'Selection delete error:',
                err.response?.data || err
            );

            setError(
                err.response?.data?.detail ||
                err.response?.data?.error ||
                'Could not delete the selection record.'
            );
        }
    }

    // Upload selection results from Excel.
    async function handleExcelUpload(event) {
        event.preventDefault();

        if (!isAdmin) return;

        setError('');
        setSuccess('');
        setUploadResult(null);

        if (!uploadFile) {
            setError('Please select an Excel file.');
            return;
        }

        if (!uploadJobId) {
            setError('Please select a job.');
            return;
        }

        setUploading(true);

        try {
            const result = await uploadSelectionResults(
                uploadFile,
                uploadJobId,
                confirmCompleteList
            );

            setUploadResult(result);
            setUploadFile(null);
            setUploadJobId('');
            setConfirmCompleteList(false);

            const refreshed = await loadData();

            setSuccess(
                refreshed
                    ? 'Selection Excel file processed. Check the upload results below.'
                    : 'Upload processed, but the selection list could not be refreshed.'
            );
        } catch (err) {
            console.error(
                'Selection Excel upload error:',
                err.response?.data || err
            );

            const data = err.response?.data;

            setError(
                data?.detail ||
                data?.error ||
                (data ? JSON.stringify(data) : 'Could not upload the Excel file.')
            );
        } finally {
            setUploading(false);
        }
    }

    return (
        <div className="selections-page">
            <div className="selections-header">
                <div>
                    <h2>Selection Management</h2>
                    <p>
                        {isAdmin
                            ? 'Record candidate selection decisions and offer details.'
                            : 'View selection decisions and offer details.'}
                    </p>
                </div>

                <div className="selections-count">
                    <span>Total records</span>
                    <strong>{selections.length}</strong>
                </div>
            </div>

            {error && (
                <div className="selections-alert selections-error">
                    {error}
                </div>
            )}

            {success && (
                <div className="selections-alert selections-success">
                    {success}
                </div>
            )}

            {/* Excel upload report */}
            {uploadResult && (
                <section className="selections-card">
                    <h3>Excel Upload Report</h3>

                    <p>
                        <strong>Upload Status:</strong>{' '}
                        {uploadResult.status}
                    </p>

                    <div className="selections-header">
                        <div>
                            <span>Total Rows</span>
                            <strong>{uploadResult.total_rows ?? 0}</strong>
                        </div>

                        <div>
                            <span>Matched Rows</span>
                            <strong>{uploadResult.matched_rows ?? 0}</strong>
                        </div>

                        <div>
                            <span>Failed Rows</span>
                            <strong>{uploadResult.failed_rows ?? 0}</strong>
                        </div>
                    </div>

                    {uploadResult.processing_summary && (
                        <>
                            <h4>Processing Summary</h4>

                            <p>
                                Created: {uploadResult.processing_summary.created ?? 0}
                            </p>

                            <p>
                                Updated: {uploadResult.processing_summary.updated ?? 0}
                            </p>

                            {uploadResult.processing_summary.omitted_marked_not_selected !== undefined && (
                                <p>
                                    Omitted applications marked Not Selected:{' '}
                                    {uploadResult.processing_summary.omitted_marked_not_selected}
                                </p>
                            )}

                            {uploadResult.processing_summary.complete_list_action_skipped && (
                                <p>
                                    {uploadResult.processing_summary.complete_list_action_skipped}
                                </p>
                            )}

                            {uploadResult.processing_summary.errors?.length > 0 && (
                                <>
                                    <h4>Row Errors</h4>

                                    <ul>
                                        {uploadResult.processing_summary.errors.map(
                                            (item, index) => (
                                                <li key={index}>
                                                    {item.row
                                                        ? `Row ${item.row}: `
                                                        : ''}
                                                    {item.error}
                                                </li>
                                            )
                                        )}
                                    </ul>
                                </>
                            )}
                        </>
                    )}
                </section>
            )}

            {/* Admin Excel upload section */}
            {isAdmin && (
                <section className="selections-card">
                    <h3>Upload Final Selection Results</h3>

                    <form
                        className="selections-form"
                        onSubmit={handleExcelUpload}
                    >
                        <div className="selections-field">
                            <label htmlFor="upload-job">
                                Select Job
                            </label>

                            <select
                                id="upload-job"
                                value={uploadJobId}
                                onChange={(event) =>
                                    setUploadJobId(event.target.value)
                                }
                                required
                            >
                                <option value="">Select a job</option>

                                {jobs.map((job) => (
                                    <option key={job.id} value={job.id}>
                                        {job.title} (Job #{job.id})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="selections-field">
                            <label htmlFor="selection-excel">
                                Excel File
                            </label>

                            <input
                                id="selection-excel"
                                type="file"
                                accept=".xlsx,.xls"
                                onChange={(event) =>
                                    setUploadFile(event.target.files[0] || null)
                                }
                                required
                            />
                        </div>

                        <div className="selections-field selections-wide">
                            <label>
                                <input
                                    type="checkbox"
                                    checked={confirmCompleteList}
                                    onChange={(event) =>
                                        setConfirmCompleteList(event.target.checked)
                                    }
                                />
                                I confirm this Excel file contains the complete final selection list.
                            </label>

                            <small>
                                If checked, applications missing from a valid upload
                                will be marked Not Selected. If unchecked, omitted
                                applications will remain unchanged.
                            </small>
                        </div>

                        <div className="selections-actions selections-wide">
                            <button
                                type="submit"
                                disabled={uploading || jobs.length === 0}
                            >
                                {uploading ? 'Uploading...' : 'Upload Results'}
                            </button>
                        </div>
                    </form>
                </section>
            )}

            {/* Manual selection form */}
            {isAdmin && (
                <section className="selections-card">
                    <h3>
                        {editingId
                            ? 'Edit Selection'
                            : 'Record a Selection Decision'}
                    </h3>

                    <form
                        className="selections-form"
                        onSubmit={handleSubmit}
                    >
                        <div className="selections-field selections-wide">
                            <label htmlFor="selection-application">
                                Application
                            </label>

                            <select
                                id="selection-application"
                                name="application"
                                value={form.application}
                                onChange={handleChange}
                                required
                            >
                                <option value="">
                                    Select an application
                                </option>

                                {applications.map((application) => (
                                    <option
                                        key={application.id}
                                        value={application.id}
                                    >
                                        {getApplicationLabel(application)}
                                    </option>
                                ))}
                            </select>

                            {applications.length === 0 && (
                                <small>
                                    Create an application before recording a decision.
                                </small>
                            )}
                        </div>

                        <div className="selections-field">
                            <label htmlFor="selection-status">
                                Decision
                            </label>

                            <select
                                id="selection-status"
                                name="status"
                                value={form.status}
                                onChange={handleChange}
                                required
                            >
                                <option value="pending">Pending</option>
                                <option value="selected">Selected</option>
                                <option value="rejected">Rejected</option>
                            </select>
                        </div>

                        {form.status !== 'rejected' && (
                            <>
                                <div className="selections-field">
                                    <label htmlFor="selection-offer-date">
                                        Offer date
                                    </label>

                                    <input
                                        id="selection-offer-date"
                                        name="offer_date"
                                        type="date"
                                        value={form.offer_date}
                                        onChange={handleChange}
                                        required={form.status === 'selected'}
                                    />
                                </div>

                                <div className="selections-field">
                                    <label htmlFor="selection-joining-date">
                                        Joining date
                                    </label>

                                    <input
                                        id="selection-joining-date"
                                        name="joining_date"
                                        type="date"
                                        value={form.joining_date}
                                        onChange={handleChange}
                                        required={form.status === 'selected'}
                                    />
                                </div>

                                <div className="selections-field">
                                    <label htmlFor="selection-package">
                                        Package (LPA)
                                    </label>

                                    <input
                                        id="selection-package"
                                        name="package"
                                        type="number"
                                        min="0.01"
                                        step="0.01"
                                        placeholder="e.g. 6.00"
                                        value={form.package}
                                        onChange={handleChange}
                                        required={form.status === 'selected'}
                                    />
                                </div>
                            </>
                        )}

                        <div className="selections-field selections-wide">
                            <label htmlFor="selection-remarks">
                                Remarks
                            </label>

                            <textarea
                                id="selection-remarks"
                                name="remarks"
                                rows="3"
                                placeholder="Add decision notes or comments"
                                value={form.remarks}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="selections-actions selections-wide">
                            <button
                                type="submit"
                                disabled={saving || applications.length === 0}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingId
                                        ? 'Update Selection'
                                        : 'Save Decision'}
                            </button>

                            {editingId && (
                                <button
                                    type="button"
                                    className="selections-secondary"
                                    onClick={resetForm}
                                >
                                    Cancel Edit
                                </button>
                            )}
                        </div>
                    </form>
                </section>
            )}

            {/* Selection records table */}
            <section className="selections-card">
                <div className="selections-list-header">
                    <h3>Selection Records</h3>

                    <button
                        type="button"
                        className="selections-secondary"
                        onClick={loadData}
                        disabled={loading}
                    >
                        {loading ? 'Loading...' : 'Refresh'}
                    </button>
                </div>

                {loading ? (
                    <p className="selections-empty">
                        Loading selection records...
                    </p>
                ) : selections.length === 0 ? (
                    <p className="selections-empty">
                        No selection records found.
                    </p>
                ) : (
                    <div className="selections-table-wrap">
                        <table className="selections-table">
                            <thead>
                                <tr>
                                    <th>Application</th>
                                    <th>Decision</th>
                                    <th>Offer Date</th>
                                    <th>Joining Date</th>
                                    <th>Package</th>
                                    <th>Remarks</th>
                                    {isAdmin && <th>Actions</th>}
                                </tr>
                            </thead>

                            <tbody>
                                {selections.map((selection) => (
                                    <tr key={selection.id}>
                                        <td>
                                            {getApplicationDetails(
                                                selection.application
                                            )}
                                        </td>

                                        <td>
                                            <span
                                                className={`selection-status selection-${selection.status}`}
                                            >
                                                {selection.status}
                                            </span>
                                        </td>

                                        <td>
                                            {selection.offer_date || '—'}
                                        </td>

                                        <td>
                                            {selection.joining_date || '—'}
                                        </td>

                                        <td>
                                            {selection.package != null
                                                ? `${Number(selection.package).toFixed(2)} LPA`
                                                : '—'}
                                        </td>

                                        <td>
                                            {selection.remarks || '—'}
                                        </td>

                                        {isAdmin && (
                                            <td>
                                                <div className="selections-row-actions">
                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            startEdit(selection)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="selections-delete"
                                                        onClick={() =>
                                                            handleDelete(selection.id)
                                                        }
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </td>
                                        )}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>
        </div>
    );
}

export default Selections;
