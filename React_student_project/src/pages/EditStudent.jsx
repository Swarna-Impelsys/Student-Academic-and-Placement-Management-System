
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
    getStudentById,
    getCourses,
    getSubjects,
    updateStudent,
} from '../services/studentService';

import './AddStudent.css';

function EditStudent() {
    const { id } = useParams();
    const navigate = useNavigate();

    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]);

    const [formData, setFormData] = useState({
        Name: '',
        Age: '',
        Email: '',
        Phone: '',
        Course: '',
        status: 'active',
        subjects: [],
    });

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [fieldErrors, setFieldErrors] = useState({});

    // Load student details and dropdown options.
    useEffect(() => {
        let active = true;

        async function loadStudentAndOptions() {
            setLoading(true);
            setError('');

            try {
                const [
                    student,
                    courseData,
                    subjectData,
                ] = await Promise.all([
                    getStudentById(id),
                    getCourses(),
                    getSubjects(),
                ]);

                if (!active) return;

                setCourses(
                    Array.isArray(courseData)
                        ? courseData
                        : courseData.results ?? []
                );

                setSubjects(
                    Array.isArray(subjectData)
                        ? subjectData
                        : subjectData.results ?? []
                );

                setFormData({
                    Name: student.Name ?? '',
                    Age: student.Age ?? '',
                    Email: student.Email ?? '',
                    Phone: student.Phone ?? '',

                    Course: String(
                        student.Course?.id ??
                        student.Course ??
                        ''
                    ),

                    status: student.status ?? 'active',

                    subjects: (student.subjects ?? []).map((item) =>
                        Number(
                            typeof item === 'object'
                                ? item.id
                                : item
                        )
                    ),
                });
            } catch (err) {
                if (!active) return;

                setError(
                    err.response?.data?.detail ||
                    'Unable to load student details. Check your access and try again.'
                );
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        loadStudentAndOptions();

        return () => {
            active = false;
        };
    }, [id]);

    // Handle text and select input changes.
    function handleChange(event) {
        const { name, value } = event.target;

        setFormData((previous) => ({
            ...previous,
            [name]: value,
        }));

        setFieldErrors((previous) => ({
            ...previous,
            [name]: undefined,
        }));
    }

    // Handle subject checkbox changes.
    function handleSubjectChange(event) {
        const selectedId = Number(event.target.value);

        setFormData((previous) => ({
            ...previous,

            subjects: event.target.checked
                ? [...previous.subjects, selectedId]
                : previous.subjects.filter(
                    (item) => item !== selectedId
                ),
        }));
    }

    // Display field validation errors.
    function displayError(field) {
        const message = fieldErrors[field];

        if (!message) return null;

        return (
            <span className="as-field-error">
                {Array.isArray(message)
                    ? message.join(' ')
                    : String(message)}
            </span>
        );
    }

    // Get a readable label for course or subject.
    function getLabel(item, fields) {
        for (const field of fields) {
            if (
                item?.[field] !== undefined &&
                item[field] !== null
            ) {
                return String(item[field]);
            }
        }

        return `Option ${item?.id ?? ''}`;
    }

    // Submit updated student information.
    async function handleSubmit(event) {
        event.preventDefault();

        setError('');
        setFieldErrors({});

        if (formData.Name.trim().length < 3) {
            setFieldErrors({
                Name: 'Name must contain at least 3 characters.',
            });
            return;
        }

        if (!formData.Age || Number(formData.Age) <= 18) {
            setFieldErrors({
                Age: 'Age must be greater than 18.',
            });
            return;
        }

        if (!/^\d{10}$/.test(formData.Phone)) {
            setFieldErrors({
                Phone: 'Enter a valid 10-digit phone number.',
            });
            return;
        }

        if (!formData.Course) {
            setFieldErrors({
                Course: 'Please select a course.',
            });
            return;
        }

        const payload = {
            Name: formData.Name.trim(),
            Age: Number(formData.Age),
            Email: formData.Email.trim(),
            Phone: formData.Phone.trim(),
            Course: Number(formData.Course),
            status: formData.status,
            subjects: formData.subjects,
        };

        setSubmitting(true);

        try {
            await updateStudent(id, payload);

            navigate(`/students/${id}`);
        } catch (err) {
            const data = err.response?.data;

            if (
                data &&
                typeof data === 'object' &&
                !Array.isArray(data)
            ) {
                setFieldErrors(data);

                setError(
                    data.detail ||
                    data.message ||
                    'Unable to update student. Check the highlighted fields.'
                );
            } else {
                setError(
                    'Unable to update student. Please try again.'
                );
            }
        } finally {
            setSubmitting(false);
        }
    }

    // Cancel editing and return to student details.
    function handleCancel() {
        if (!submitting) {
            navigate(`/students/${id}`);
        }
    }

    if (loading) {
        return (
            <div className="as-page">
                <div className="as-card">
                    Loading student details...
                </div>
            </div>
        );
    }

    if (error && !formData.Name) {
        return (
            <div className="as-page">
                <div className="as-alert as-alert-error">
                    {String(error)}
                </div>

                <Link
                    to="/students"
                    className="as-button as-button-secondary"
                >
                    Back to Students
                </Link>
            </div>
        );
    }

    return (
        <div className="as-page">
            <div className="as-heading">
                <div>
                    <p className="as-eyebrow">
                        STUDENT MANAGEMENT
                    </p>

                    <h1>Edit Student</h1>

                    <p className="as-subtitle">
                        Update the student's personal and academic information.
                    </p>
                </div>

                <Link
                    to={`/students/${id}`}
                    className="as-back-link"
                >
                    ← Back to Details
                </Link>
            </div>

            <form
                className="as-card"
                onSubmit={handleSubmit}
            >
                {error && (
                    <div
                        className="as-alert as-alert-error"
                        role="alert"
                    >
                        {typeof error === 'string'
                            ? error
                            : 'Please check the fields below.'}
                    </div>
                )}

                {/* Personal Information */}
                <section className="as-section">
                    <div className="as-section-heading">
                        <span className="as-section-number">
                            01
                        </span>

                        <div>
                            <h2>Personal Information</h2>
                            <p>Update the student's basic details</p>
                        </div>
                    </div>

                    <div className="as-grid">
                        <div className="as-field">
                            <label htmlFor="edit-name">
                                Full Name *
                            </label>

                            <input
                                id="edit-name"
                                name="Name"
                                value={formData.Name}
                                onChange={handleChange}
                                minLength={3}
                                required
                            />

                            {displayError('Name')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="edit-age">
                                Age *
                            </label>

                            <input
                                id="edit-age"
                                type="number"
                                name="Age"
                                min="19"
                                value={formData.Age}
                                onChange={handleChange}
                                required
                            />

                            {displayError('Age')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="edit-email">
                                Email *
                            </label>

                            <input
                                id="edit-email"
                                type="email"
                                name="Email"
                                value={formData.Email}
                                onChange={handleChange}
                                required
                            />

                            {displayError('Email')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="edit-phone">
                                Phone *
                            </label>

                            <input
                                id="edit-phone"
                                name="Phone"
                                type="tel"
                                inputMode="numeric"
                                maxLength={10}
                                pattern="[0-9]{10}"
                                value={formData.Phone}
                                onChange={handleChange}
                                required
                            />

                            {displayError('Phone')}
                        </div>
                    </div>
                </section>

                <div className="as-divider" />

                {/* Academic Information */}
                <section className="as-section">
                    <div className="as-section-heading">
                        <span className="as-section-number">
                            02
                        </span>

                        <div>
                            <h2>Academic Information</h2>
                            <p>
                                Update course, status, and subjects
                            </p>
                        </div>
                    </div>

                    <div className="as-grid">
                        <div className="as-field">
                            <label htmlFor="edit-course">
                                Course *
                            </label>

                            <select
                                id="edit-course"
                                name="Course"
                                value={formData.Course}
                                onChange={handleChange}
                                required
                            >
                                <option value="">
                                    Select a course
                                </option>

                                {courses.map((course) => (
                                    <option
                                        key={course.id}
                                        value={course.id}
                                    >
                                        {getLabel(course, [
                                            'name',
                                            'Name',
                                            'course_name',
                                            'title',
                                        ])}
                                    </option>
                                ))}
                            </select>

                            {displayError('Course')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="edit-status">
                                Student Status *
                            </label>

                            <select
                                id="edit-status"
                                name="status"
                                value={formData.status}
                                onChange={handleChange}
                                required
                            >
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="graduated">Graduated</option>
                            </select>

                            {displayError('status')}
                        </div>
                    </div>

                    {/* Subjects */}
                    <div className="as-field as-options-field">
                        <div className="as-options-heading">
                            <label>Subjects</label>
                            <span>
                                Optional · Select all that apply
                            </span>
                        </div>

                        <div className="as-checkbox-grid">
                            {subjects.map((subject) => (
                                <label
                                    className="as-checkbox-option"
                                    key={subject.id}
                                >
                                    <input
                                        type="checkbox"
                                        value={subject.id}
                                        checked={formData.subjects.includes(
                                            Number(subject.id)
                                        )}
                                        onChange={handleSubjectChange}
                                    />

                                    <span>
                                        {getLabel(subject, [
                                            'name',
                                            'Name',
                                            'subject_name',
                                            'title',
                                        ])}
                                    </span>
                                </label>
                            ))}
                        </div>

                        {displayError('subjects')}
                    </div>
                </section>

                {/* Form Actions */}
                <div className="as-form-footer">
                    <p className="as-required-note">
                        * Required fields
                    </p>

                    <div className="as-actions">
                        <button
                            type="button"
                            className="as-button as-button-secondary"
                            onClick={handleCancel}
                            disabled={submitting}
                        >
                            Cancel
                        </button>

                        <button
                            type="submit"
                            className="as-button as-button-primary"
                            disabled={submitting}
                        >
                            {submitting
                                ? 'Saving Changes...'
                                : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}

export default EditStudent;
