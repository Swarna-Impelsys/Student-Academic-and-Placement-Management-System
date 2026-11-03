
import { useEffect, useState } from 'react';
import {
    getPlacementDrives,
    createPlacementDrive,
    updatePlacementDrive,
    deletePlacementDrive,
} from '../services/placementDriveService';
import { getCompanies } from '../services/companyService';

const initialForm = {
    company: '',
    title: '',
    description: '',
    drive_date: '',
    application_start_date: '',
    application_end_date: '',
    location: '',
    is_active: true,
};

function PlacementDrives() {
    const role = localStorage.getItem('role')?.trim().toLowerCase();
    const isAdmin = role === 'admin';

    const [drives, setDrives] = useState([]);
    const [companies, setCompanies] = useState([]);
    const [form, setForm] = useState(initialForm);
    const [editingId, setEditingId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        setError('');

        try {
            const driveData = await getPlacementDrives();

            setDrives(
                Array.isArray(driveData)
                    ? driveData
                    : driveData.results || []
            );

            // Only Admin needs the company list to create or edit drives.
            if (isAdmin) {
                const companyData = await getCompanies();

                setCompanies(
                    Array.isArray(companyData)
                        ? companyData
                        : companyData.results || []
                );
            }

            return true;
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to load placement drives. Please check your login and API.'
            );

            return false;
        } finally {
            setLoading(false);
        }
    }

    function handleChange(event) {
        const { name, value, type, checked } = event.target;

        setForm(previous => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    }

    function resetForm() {
        setForm(initialForm);
        setEditingId(null);
        setError('');
        setSuccess('');
    }

    function startEdit(drive) {
        if (!isAdmin) return;

        setForm({
            company: String(drive.company ?? ''),
            title: drive.title || '',
            description: drive.description || '',
            drive_date: drive.drive_date || '',
            application_start_date: drive.application_start_date || '',
            application_end_date: drive.application_end_date || '',
            location: drive.location || '',
            is_active: drive.is_active ?? true,
        });

        setEditingId(drive.id);
        setError('');
        setSuccess('');

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function getErrorMessage(err) {
        const data = err.response?.data;

        if (!data) {
            return 'Something went wrong. Please check your connection and try again.';
        }

        if (typeof data === 'string') return data;

        return Object.entries(data)
            .map(([field, messages]) => {
                const message = Array.isArray(messages)
                    ? messages.join(', ')
                    : typeof messages === 'object'
                        ? JSON.stringify(messages)
                        : messages;

                return `${field}: ${message}`;
            })
            .join(' | ');
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!isAdmin) {
            setError('Only Admin can manage placement drives.');
            return;
        }

        setError('');
        setSuccess('');

        if (
            form.application_start_date &&
            form.application_end_date &&
            form.application_start_date > form.application_end_date
        ) {
            setError('Application end date cannot be before the start date.');
            return;
        }

        setSaving(true);

        const payload = {
            ...form,
            company: Number(form.company),
        };

        try {
            const wasEditing = editingId !== null;

            if (wasEditing) {
                await updatePlacementDrive(editingId, payload);
            } else {
                await createPlacementDrive(payload);
            }

            // The create/update request succeeded.
            // Reset the form before refreshing the list.
            setForm(initialForm);
            setEditingId(null);

            const refreshed = await loadData();

            if (refreshed) {
                setSuccess(
                    wasEditing
                        ? 'Placement drive updated successfully.'
                        : 'Placement drive created successfully.'
                );
            } else {
                setSuccess(
                    wasEditing
                        ? 'Placement drive was updated successfully, but the list could not be refreshed. Please refresh the page.'
                        : 'Placement drive was created successfully, but the list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(drive) {
        if (!isAdmin) return;

        const confirmed = window.confirm(
            `Delete the placement drive "${drive.title}"?`
        );

        if (!confirmed) return;

        setError('');
        setSuccess('');

        try {
            await deletePlacementDrive(drive.id);

            setDrives(previous =>
                previous.filter(item => item.id !== drive.id)
            );

            if (editingId === drive.id) resetForm();

            setSuccess('Placement drive deleted successfully.');
        } catch (err) {
            setError(getErrorMessage(err));
        }
    }

    function companyName(companyId) {
        const company = companies.find(
            item => item.id === companyId
        );

        return company?.name || `Company #${companyId}`;
    }

    function formatDate(value) {
        if (!value) return '—';

        const [year, month, day] = value.split('-');
        return `${day}-${month}-${year}`;
    }

    // Registration Officers can view placement drives,
    // but only Admin can manage them.
    if (
        ![
            'admin',
            'teacher',
            'student',
            'registration officer',
        ].includes(role)
    ) {
        return (
            <div className="management-page">
                <div className="alert alert-error" role="alert">
                    Your role is not recognized. Please log in again.
                </div>
            </div>
        );
    }

    return (
        <div className="management-page">
            <div className="management-header">
                <div>
                    <h2>Placement Drives</h2>
                    <p>
                        {isAdmin
                            ? 'Create and manage company placement drives.'
                            : 'View placement drive details.'}
                    </p>
                </div>

                <span className="skills-count">
                    {drives.length} drives
                </span>
            </div>

            {error && (
                <div className="alert alert-error" role="alert">
                    {error}
                </div>
            )}

            {success && (
                <div className="alert alert-success" role="status">
                    {success}
                </div>
            )}

            {isAdmin && (
                <section className="management-card">
                    <div className="card-heading">
                        <h3>
                            {editingId !== null
                                ? 'Edit Placement Drive'
                                : 'Add Placement Drive'}
                        </h3>
                    </div>

                    {companies.length === 0 && !loading && (
                        <p className="field-help">
                            No companies found. Add a company first.
                        </p>
                    )}

                    <form
                        className="placement-drive-form"
                        onSubmit={handleSubmit}
                    >
                        <div className="form-field">
                            <label htmlFor="company">Company *</label>
                            <select
                                id="company"
                                name="company"
                                value={form.company}
                                onChange={handleChange}
                                required
                            >
                                <option value="">Select company</option>
                                {companies.map(company => (
                                    <option
                                        key={company.id}
                                        value={company.id}
                                    >
                                        {company.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-field">
                            <label htmlFor="title">Drive Title *</label>
                            <input
                                id="title"
                                name="title"
                                value={form.title}
                                onChange={handleChange}
                                maxLength={150}
                                placeholder="e.g. Graduate Recruitment Drive"
                                required
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="location">Location *</label>
                            <input
                                id="location"
                                name="location"
                                value={form.location}
                                onChange={handleChange}
                                maxLength={200}
                                placeholder="e.g. Bengaluru"
                                required
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="drive_date">Drive Date *</label>
                            <input
                                id="drive_date"
                                name="drive_date"
                                type="date"
                                value={form.drive_date}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="application_start_date">
                                Application Start Date *
                            </label>
                            <input
                                id="application_start_date"
                                name="application_start_date"
                                type="date"
                                value={form.application_start_date}
                                onChange={handleChange}
                                required
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="application_end_date">
                                Application End Date *
                            </label>
                            <input
                                id="application_end_date"
                                name="application_end_date"
                                type="date"
                                value={form.application_end_date}
                                onChange={handleChange}
                                min={form.application_start_date || undefined}
                                required
                            />
                        </div>

                        <div className="form-field placement-description">
                            <label htmlFor="description">Description</label>
                            <textarea
                                id="description"
                                name="description"
                                value={form.description}
                                onChange={handleChange}
                                rows={4}
                                placeholder="Enter drive details..."
                            />
                        </div>

                        <div className="form-field placement-active-field">
                            <label>
                                <input
                                    type="checkbox"
                                    name="is_active"
                                    checked={form.is_active}
                                    onChange={handleChange}
                                />
                                Active placement drive
                            </label>
                        </div>

                        <div className="form-actions">
                            <button
                                className="btn btn-primary"
                                type="submit"
                                disabled={saving || companies.length === 0}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingId !== null
                                        ? 'Update Drive'
                                        : 'Add Drive'}
                            </button>

                            {editingId !== null && (
                                <button
                                    className="btn btn-secondary"
                                    type="button"
                                    onClick={resetForm}
                                    disabled={saving}
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>
                </section>
            )}

            <section className="management-card">
                <div className="card-heading">
                    <h3>Placement Drive List</h3>
                </div>

                {loading ? (
                    <p>Loading placement drives...</p>
                ) : drives.length === 0 ? (
                    <div className="empty-state">
                        No placement drives found.
                        {isAdmin && ' Add your first drive above.'}
                    </div>
                ) : (
                    <div className="table-container">
                        <table className="management-table">
                            <thead>
                                <tr>
                                    <th>Company</th>
                                    <th>Drive Title</th>
                                    <th>Drive Date</th>
                                    <th>Application Period</th>
                                    <th>Location</th>
                                    <th>Status</th>
                                    {isAdmin && <th>Actions</th>}
                                </tr>
                            </thead>

                            <tbody>
                                {drives.map(drive => (
                                    <tr key={drive.id}>
                                        <td>{companyName(drive.company)}</td>
                                        <td>{drive.title}</td>
                                        <td>{formatDate(drive.drive_date)}</td>
                                        <td>
                                            {formatDate(drive.application_start_date)}
                                            {' – '}
                                            {formatDate(drive.application_end_date)}
                                        </td>
                                        <td>{drive.location}</td>
                                        <td>
                                            <span
                                                className={
                                                    drive.is_active
                                                        ? 'company-status active'
                                                        : 'company-status inactive'
                                                }
                                            >
                                                {drive.is_active
                                                    ? 'Active'
                                                    : 'Inactive'}
                                            </span>
                                        </td>

                                        {isAdmin && (
                                            <td>
                                                <div className="table-actions">
                                                    <button
                                                        className="btn btn-edit"
                                                        type="button"
                                                        onClick={() => startEdit(drive)}
                                                    >
                                                        Edit
                                                    </button>
                                                    <button
                                                        className="btn btn-delete"
                                                        type="button"
                                                        onClick={() => handleDelete(drive)}
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

export default PlacementDrives;
