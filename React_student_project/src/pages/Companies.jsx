
import { useEffect, useState } from 'react';
import {
    getCompanies,
    createCompany,
    updateCompany,
    deleteCompany
} from '../services/companyService';

const emptyForm = {
    name: '',
    description: '',
    website: '',
    location: '',
    contact_person: '',
    contact_email: '',
    contact_phone: '',
    is_active: true
};

function Companies() {
    const role = localStorage.getItem('role')?.trim().toLowerCase();
    const isAdmin = role === 'admin';

    const [companies, setCompanies] = useState([]);
    const [form, setForm] = useState(emptyForm);
    const [logo, setLogo] = useState(null);
    const [editingId, setEditingId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
        loadCompanies();
    }, []);

    async function loadCompanies() {
        setLoading(true);
        setError('');

        try {
            const data = await getCompanies();

            setCompanies(
                Array.isArray(data)
                    ? data
                    : data.results || []
            );

            return true;
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to load companies. Please try again.'
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
            [name]: type === 'checkbox' ? checked : value
        }));
    }

    function resetForm() {
        setForm(emptyForm);
        setLogo(null);
        setEditingId(null);

        const fileInput = document.getElementById('company-logo');
        if (fileInput) fileInput.value = '';
    }

    function startEdit(company) {
        if (!isAdmin) return;

        setForm({
            name: company.name || '',
            description: company.description || '',
            website: company.website || '',
            location: company.location || '',
            contact_person: company.contact_person || '',
            contact_email: company.contact_email || '',
            contact_phone: company.contact_phone || '',
            is_active: company.is_active ?? true
        });

        setLogo(null);
        setEditingId(company.id);
        setError('');
        setSuccess('');

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function getErrorMessage(err) {
        const data = err.response?.data;

        if (data && typeof data === 'object') {
            const messages = Object.entries(data)
                .map(([field, messages]) => {
                    const text = Array.isArray(messages)
                        ? messages.join(', ')
                        : typeof messages === 'object'
                            ? JSON.stringify(messages)
                            : String(messages);

                    return `${field}: ${text}`;
                })
                .join(' | ');

            return messages || 'Unable to save company.';
        }

        if (typeof data === 'string') {
            return data;
        }

        return 'Unable to save company. Please try again.';
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!isAdmin) {
            setError('Only Admin can manage companies.');
            return;
        }

        setSaving(true);
        setError('');
        setSuccess('');

        try {
            const formData = new FormData();

            Object.entries(form).forEach(([key, value]) => {
                formData.append(key, value);
            });

            if (logo) {
                formData.append('logo', logo);
            }

            const wasEditing = editingId !== null;

            if (wasEditing) {
                await updateCompany(editingId, formData);
            } else {
                await createCompany(formData);
            }

            // The create/update request succeeded.
            resetForm();

            // Refresh the list separately so a refresh failure
            // is not mistaken for a failed save operation.
            const refreshed = await loadCompanies();

            if (refreshed) {
                setSuccess(
                    wasEditing
                        ? 'Company updated successfully.'
                        : 'Company added successfully.'
                );
            } else {
                setSuccess(
                    wasEditing
                        ? 'Company was updated successfully, but the company list could not be refreshed. Please refresh the page.'
                        : 'Company was added successfully, but the company list could not be refreshed. Please refresh the page.'
                );
            }
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(company) {
        if (!isAdmin) return;

        const confirmed = window.confirm(
            `Are you sure you want to delete ${company.name}?`
        );

        if (!confirmed) return;

        setError('');
        setSuccess('');

        try {
            await deleteCompany(company.id);

            setCompanies(previous =>
                previous.filter(item => item.id !== company.id)
            );

            if (editingId === company.id) {
                resetForm();
            }

            setSuccess('Company deleted successfully.');
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to delete company.'
            );
        }
    }

    function getLogoUrl(path) {
        if (!path) return '';

        if (path.startsWith('http://') || path.startsWith('https://')) {
            return path;
        }

        return `http://127.0.0.1:8001${
            path.startsWith('/') ? path : `/${path}`
        }`;
    }

    // Admin, Teacher, Student, and Registration Officer
    // can view companies.
    // Only Admin can manage companies.
    if (
        ![
            'admin',
            'teacher',
            'student',
            'registration officer'
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
                    <h2>Company Details</h2>
                    <p>
                        {isAdmin
                            ? 'Manage company profiles and placement contacts.'
                            : 'View company profiles and placement contacts.'}
                    </p>
                </div>

                <div className="skills-count">
                    Total Companies: {companies.length}
                </div>
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
                <div className="management-card">
                    <div className="card-heading">
                        <h3>
                            {editingId !== null
                                ? 'Edit Company'
                                : 'Add New Company'}
                        </h3>
                    </div>

                    <form className="company-form" onSubmit={handleSubmit}>
                        <div className="form-field">
                            <label htmlFor="company-name">Company Name *</label>
                            <input
                                id="company-name"
                                name="name"
                                value={form.name}
                                onChange={handleChange}
                                required
                                maxLength={150}
                                placeholder="Enter company name"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-location">Location *</label>
                            <input
                                id="company-location"
                                name="location"
                                value={form.location}
                                onChange={handleChange}
                                required
                                maxLength={200}
                                placeholder="Enter company location"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-description">Description</label>
                            <textarea
                                id="company-description"
                                name="description"
                                value={form.description}
                                onChange={handleChange}
                                rows={3}
                                placeholder="Describe the company"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-website">Website</label>
                            <input
                                id="company-website"
                                name="website"
                                type="url"
                                value={form.website}
                                onChange={handleChange}
                                placeholder="https://example.com"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-contact-person">
                                Contact Person *
                            </label>
                            <input
                                id="company-contact-person"
                                name="contact_person"
                                value={form.contact_person}
                                onChange={handleChange}
                                required
                                maxLength={100}
                                placeholder="Enter contact person"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-email">Contact Email *</label>
                            <input
                                id="company-email"
                                name="contact_email"
                                type="email"
                                value={form.contact_email}
                                onChange={handleChange}
                                required
                                placeholder="contact@example.com"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-phone">Contact Phone *</label>
                            <input
                                id="company-phone"
                                name="contact_phone"
                                type="tel"
                                value={form.contact_phone}
                                onChange={handleChange}
                                required
                                maxLength={15}
                                placeholder="Enter contact number"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="company-logo">Company Logo</label>
                            <input
                                id="company-logo"
                                type="file"
                                accept="image/*"
                                onChange={event =>
                                    setLogo(event.target.files?.[0] || null)
                                }
                            />
                            <p className="field-help">
                                Optional. Choose an image file.
                                {editingId !== null &&
                                    ' Leave empty to keep the existing logo.'}
                            </p>
                        </div>

                        <div className="company-active-field">
                            <label>
                                <input
                                    type="checkbox"
                                    name="is_active"
                                    checked={form.is_active}
                                    onChange={handleChange}
                                />
                                Company is active
                            </label>
                        </div>

                        <div className="form-actions">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={saving}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingId !== null
                                        ? 'Update Company'
                                        : 'Add Company'}
                            </button>

                            {editingId !== null && (
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={resetForm}
                                    disabled={saving}
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>
                </div>
            )}

            <div className="management-card">
                <div className="card-heading">
                    <h3>Company List</h3>
                </div>

                {loading ? (
                    <p>Loading companies...</p>
                ) : companies.length === 0 ? (
                    <div className="empty-state">
                        No companies found.
                        {isAdmin && ' Add your first company above.'}
                    </div>
                ) : (
                    <div className="table-container">
                        <table className="management-table">
                            <thead>
                                <tr>
                                    <th>Logo</th>
                                    <th>Company</th>
                                    <th>Location</th>
                                    <th>Contact Person</th>
                                    <th>Email</th>
                                    <th>Phone</th>
                                    <th>Status</th>
                                    <th>Website</th>
                                    {isAdmin && <th>Actions</th>}
                                </tr>
                            </thead>

                            <tbody>
                                {companies.map(company => (
                                    <tr key={company.id}>
                                        <td>
                                            {company.logo ? (
                                                <img
                                                    src={getLogoUrl(company.logo)}
                                                    alt={`${company.name} logo`}
                                                    className="company-logo"
                                                />
                                            ) : (
                                                <span>No logo</span>
                                            )}
                                        </td>

                                        <td>{company.name}</td>
                                        <td>{company.location}</td>
                                        <td>{company.contact_person}</td>
                                        <td>{company.contact_email}</td>
                                        <td>{company.contact_phone}</td>

                                        <td>
                                            <span
                                                className={
                                                    company.is_active
                                                        ? 'company-status active'
                                                        : 'company-status inactive'
                                                }
                                            >
                                                {company.is_active
                                                    ? 'Active'
                                                    : 'Inactive'}
                                            </span>
                                        </td>

                                        <td>
                                            {company.website ? (
                                                <a
                                                    href={company.website}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    Visit
                                                </a>
                                            ) : (
                                                '—'
                                            )}
                                        </td>

                                        {isAdmin && (
                                            <td>
                                                <div className="table-actions">
                                                    <button
                                                        type="button"
                                                        className="btn btn-edit"
                                                        onClick={() =>
                                                            startEdit(company)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="btn btn-delete"
                                                        onClick={() =>
                                                            handleDelete(company)
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
            </div>
        </div>
    );
}

export default Companies;
