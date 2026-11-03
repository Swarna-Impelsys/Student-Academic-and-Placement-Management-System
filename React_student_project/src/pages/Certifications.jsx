
import { useEffect, useState } from 'react';
import {
    getStudents,
    getCertifications,
    createCertification,
    updateCertification,
    deleteCertification
} from '../services/studentService';

const emptyForm = {
    student: '',
    name: '',
    issuing_organization: '',
    issue_date: '',
    expiry_date: '',
    certificate: null
};

function Certifications() {
    const role = localStorage.getItem('role')?.trim().toLowerCase();

    const isAdmin = role === 'admin';
    const isTeacher = role === 'teacher';
    const isStudent = role === 'student';
    const canManage = isStudent;

    const [certifications, setCertifications] = useState([]);
    const [students, setStudents] = useState([]);
    const [form, setForm] = useState(emptyForm);
    const [editingId, setEditingId] = useState(null);

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    async function loadData() {
        try {
            setLoading(true);
            setError('');

            const certificationData = await getCertifications();

            setCertifications(
                Array.isArray(certificationData)
                    ? certificationData
                    : certificationData.results ?? []
            );

            // Admin and Teacher need student names for the table.
            // Students only see their own certifications.
            if (isAdmin || isTeacher) {
                const studentData = await getStudents();

                setStudents(
                    Array.isArray(studentData)
                        ? studentData
                        : studentData.results ?? []
                );
            }
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to load certifications or students.'
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadData();
    }, []);

    function handleChange(event) {
        const { name, value } = event.target;

        setForm(current => ({
            ...current,
            [name]: value
        }));
    }

    function resetForm() {
        setForm(emptyForm);
        setEditingId(null);
    }

    function startEdit(certification) {
        if (!canManage) return;

        setEditingId(certification.id);

        setForm({
            student: String(certification.student),
            name: certification.name || '',
            issuing_organization:
                certification.issuing_organization || '',
            issue_date: certification.issue_date || '',
            expiry_date: certification.expiry_date || '',
            certificate: null
        });

        setError('');
        setSuccess('');
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!canManage) return;

        setError('');
        setSuccess('');

        const payload = new FormData();

        // Do not send the student ID.
        // The backend should assign the logged-in student.
        payload.append('name', form.name.trim());

        payload.append(
            'issuing_organization',
            form.issuing_organization.trim()
        );

        payload.append('issue_date', form.issue_date);

        if (form.expiry_date) {
            payload.append('expiry_date', form.expiry_date);
        }

        if (form.certificate) {
            payload.append('certificate', form.certificate);
        }

        try {
            setSaving(true);

            if (editingId !== null) {
                await updateCertification(editingId, payload);
                setSuccess('Certification updated successfully.');
            } else {
                await createCertification(payload);
                setSuccess('Certification added successfully.');
            }

            resetForm();
            await loadData();
        } catch (err) {
            const data = err.response?.data;

            const firstError = data && Object.values(data).find(
                value => Array.isArray(value) && value.length > 0
            );

            setError(
                firstError?.[0] ||
                data?.detail ||
                'Unable to save certification. Check your permissions and form values.'
            );
        } finally {
            setSaving(false);
        }
    }

    async function handleDelete(certification) {
        if (!canManage) return;

        if (!window.confirm(
            `Delete the certification "${certification.name}"?`
        )) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            await deleteCertification(certification.id);

            setSuccess('Certification deleted successfully.');
            await loadData();
        } catch (err) {
            setError(
                err.response?.data?.detail ||
                'Unable to delete certification. Check your permissions.'
            );
        }
    }

    function studentName(studentId) {
        const student = students.find(
            item => item.id === Number(studentId)
        );

        return student?.Name || `Student #${studentId}`;
    }

    function getCertificateUrl(certificate) {
        if (!certificate) return '';

        if (certificate.startsWith('http')) {
            return certificate;
        }

        return `http://127.0.0.1:8001/${
            certificate.startsWith('/')
                ? certificate.slice(1)
                : certificate
        }`;
    }

    if (!isAdmin && !isTeacher && !isStudent) {
        return (
            <div className="management-page">
                <div className="alert alert-error">
                    You do not have permission to view certifications.
                </div>
            </div>
        );
    }

    return (
        <div className="management-page">
            <div className="management-header">
                <div>
                    <h2>Certifications</h2>

                    <p>
                        {isAdmin
                            ? 'View certifications for all students.'
                            : isTeacher
                                ? 'View certifications for your assigned students.'
                                : 'View and manage your own certifications.'}
                    </p>
                </div>

                <div className="skills-count">
                    {certifications.length} Certifications
                </div>
            </div>

            {error && (
                <div role="alert" className="alert alert-error">
                    {error}
                </div>
            )}

            {success && (
                <div className="alert alert-success">
                    {success}
                </div>
            )}

            {/* Only Students can add or edit certificates */}
            {canManage && (
                <section className="management-card">
                    <div className="card-heading">
                        <div>
                            <h3>
                                {editingId !== null
                                    ? 'Edit Certification'
                                    : 'Add Certification'}
                            </h3>

                            <p>Enter your certification details.</p>
                        </div>
                    </div>

                    <form
                        className="certification-form"
                        onSubmit={handleSubmit}
                    >
                        <div className="form-field">
                            <label htmlFor="cert-name">
                                Certification Name
                            </label>

                            <input
                                id="cert-name"
                                type="text"
                                name="name"
                                placeholder="e.g. Python Certification"
                                value={form.name}
                                onChange={handleChange}
                                minLength={3}
                                required
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="cert-organization">
                                Issuing Organization
                            </label>

                            <input
                                id="cert-organization"
                                type="text"
                                name="issuing_organization"
                                placeholder="e.g. Microsoft"
                                value={form.issuing_organization}
                                onChange={handleChange}
                                minLength={2}
                                required
                            />
                        </div>

                        <div className="certification-date-row">
                            <div className="form-field">
                                <label htmlFor="cert-issue-date">
                                    Issue Date
                                </label>

                                <input
                                    id="cert-issue-date"
                                    type="date"
                                    name="issue_date"
                                    value={form.issue_date}
                                    onChange={handleChange}
                                    max={form.expiry_date || undefined}
                                    required
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="cert-expiry-date">
                                    Expiry Date (optional)
                                </label>

                                <input
                                    id="cert-expiry-date"
                                    type="date"
                                    name="expiry_date"
                                    value={form.expiry_date}
                                    onChange={handleChange}
                                    min={form.issue_date || undefined}
                                />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="cert-file">
                                Certificate File (optional)
                            </label>

                            <input
                                id="cert-file"
                                type="file"
                                accept=".pdf,.png,.jpg,.jpeg"
                                onChange={event =>
                                    setForm(current => ({
                                        ...current,
                                        certificate:
                                            event.target.files?.[0] || null
                                    }))
                                }
                            />

                            <p className="field-help">
                                {editingId !== null
                                    ? 'Leave empty to keep the existing file.'
                                    : 'Attach a PDF or image of your certificate.'}
                            </p>
                        </div>

                        <div className="form-actions">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={saving || loading}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingId !== null
                                        ? 'Update Certification'
                                        : 'Add Certification'}
                            </button>

                            {editingId !== null && (
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={resetForm}
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
                    <div>
                        <h3>Student Certifications</h3>

                        <p>
                            {canManage
                                ? 'Your certificates.'
                                : 'Certificates you are authorized to view.'}
                        </p>
                    </div>
                </div>

                {loading ? (
                    <p>Loading certifications...</p>
                ) : certifications.length === 0 ? (
                    <div className="empty-state">
                        <p>No certifications found.</p>
                    </div>
                ) : (
                    <div className="table-container">
                        <table className="management-table">
                            <thead>
                                <tr>
                                    {(isAdmin || isTeacher) && (
                                        <th>Student</th>
                                    )}

                                    <th>Certification</th>
                                    <th>Organization</th>
                                    <th>Issue Date</th>
                                    <th>Expiry Date</th>
                                    <th>File</th>

                                    {canManage && <th>Actions</th>}
                                </tr>
                            </thead>

                            <tbody>
                                {certifications.map(certification => (
                                    <tr key={certification.id}>
                                        {(isAdmin || isTeacher) && (
                                            <td>
                                                {studentName(
                                                    certification.student
                                                )}
                                            </td>
                                        )}

                                        <td>{certification.name}</td>

                                        <td>
                                            {certification.issuing_organization}
                                        </td>

                                        <td>{certification.issue_date}</td>

                                        <td>
                                            {certification.expiry_date || 'No expiry'}
                                        </td>

                                        <td>
                                            {certification.certificate ? (
                                                <a
                                                    href={getCertificateUrl(
                                                        certification.certificate
                                                    )}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                >
                                                    View file
                                                </a>
                                            ) : (
                                                'No file'
                                            )}
                                        </td>

                                        {canManage && (
                                            <td>
                                                <div className="table-actions">
                                                    <button
                                                        type="button"
                                                        className="btn btn-edit"
                                                        onClick={() =>
                                                            startEdit(certification)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="btn btn-delete"
                                                        onClick={() =>
                                                            handleDelete(certification)
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

export default Certifications;
