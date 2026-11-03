
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import {
    createStudent,
    getCourses,
    getSubjects,
} from '../services/studentService';

import useApi from '../hooks/useApi';
import './AddStudent.css';

function AddStudent() {
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

    const {
        loading: loadingOptions,
        error: optionsError,
        execute: executeOptions,
    } = useApi();

    const {
        loading: submitting,
        error: submitError,
        setError: setSubmitError,
        execute: executeSubmit,
    } = useApi();

    const [fieldErrors, setFieldErrors] = useState({});
    const [successMessage, setSuccessMessage] = useState('');

    // Load courses and subjects only.
    useEffect(() => {
        let active = true;

        async function loadOptions() {
            try {
                const [courseData, subjectData] =
                    await executeOptions(() =>
                        Promise.all([
                            getCourses(),
                            getSubjects(),
                        ])
                    );

                if (!active) return;

                setCourses(
                    Array.isArray(courseData)
                        ? courseData
                        : courseData?.results ?? []
                );

                setSubjects(
                    Array.isArray(subjectData)
                        ? subjectData
                        : subjectData?.results ?? []
                );
            } catch {
                // The reusable hook stores the error message.
            }
        }

        loadOptions();

        return () => {
            active = false;
        };
    }, [executeOptions]);

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

        setSubmitError('');
        setSuccessMessage('');
    }

    function handleCheckboxChange(event, field) {
        const id = Number(event.target.value);

        setFormData((previous) => {
            const currentIds = previous[field];

            return {
                ...previous,
                [field]: event.target.checked
                    ? currentIds.includes(id)
                        ? currentIds
                        : [...currentIds, id]
                    : currentIds.filter((item) => item !== id),
            };
        });

        setFieldErrors((previous) => ({
            ...previous,
            [field]: undefined,
        }));

        setSubmitError('');
        setSuccessMessage('');
    }

    function getErrorMessage(value) {
        if (Array.isArray(value)) {
            return value.map(String).join(' ');
        }

        if (typeof value === 'string') {
            return value;
        }

        return 'Please check this field.';
    }

    async function handleSubmit(event) {
        event.preventDefault();

        setFieldErrors({});
        setSubmitError('');
        setSuccessMessage('');

        const name = formData.Name.trim();
        const email = formData.Email.trim();
        const phone = formData.Phone.trim();
        const age = Number(formData.Age);

        if (name.length < 3) {
            setFieldErrors({
                Name: 'Name must contain at least 3 characters.',
            });
            return;
        }

        if (!formData.Age || !Number.isFinite(age) || age <= 18) {
            setFieldErrors({
                Age: 'Age must be greater than 18.',
            });
            return;
        }

        if (!/^\d{10}$/.test(phone)) {
            setFieldErrors({
                Phone: 'Enter a valid 10-digit phone number.',
            });
            return;
        }

        if (!email) {
            setFieldErrors({
                Email: 'Email is required.',
            });
            return;
        }

        if (!formData.Course) {
            setFieldErrors({
                Course: 'Please select a course.',
            });
            return;
        }

        // Prepare student data without personal skills.
        const payload = {
            ...formData,
            Name: name,
            Email: email,
            Phone: phone,
            Age: age,
            Course: Number(formData.Course),
            subjects: formData.subjects,
        };

        try {
            const student = await executeSubmit(
                () => createStudent(payload)
            );

            setSuccessMessage('Student added successfully!');

            if (student?.id) {
                navigate(`/students/${student.id}`);
            } else {
                navigate('/students');
            }
        } catch (error) {
            const data = error.response?.data;

            if (
                data &&
                typeof data === 'object' &&
                !Array.isArray(data)
            ) {
                const nextErrors = {};

                Object.entries(data).forEach(([key, value]) => {
                    if (key === 'detail' || key === 'message') {
                        setSubmitError(getErrorMessage(value));
                    } else {
                        nextErrors[key] = getErrorMessage(value);
                    }
                });

                setFieldErrors(nextErrors);

                if (
                    Object.keys(nextErrors).length === 0 &&
                    !data.detail &&
                    !data.message
                ) {
                    setSubmitError(
                        'Unable to add student. Please check your input.'
                    );
                }
            } else {
                setSubmitError(
                    'Unable to add student. Please try again.'
                );
            }
        }
    }

    function displayError(field) {
        const error = fieldErrors[field];

        if (!error) return null;

        return (
            <span className="as-field-error">
                {error}
            </span>
        );
    }

    function getOptionLabel(item, possibleFields) {
        for (const field of possibleFields) {
            if (item?.[field] !== undefined && item[field] !== null) {
                return String(item[field]);
            }
        }

        return `Option ${item?.id ?? ''}`;
    }

    return (
        <div className="as-page">
            <div className="as-heading">
                <div>
                    <p className="as-eyebrow">
                        STUDENT MANAGEMENT
                    </p>

                    <h1>Add Student</h1>

                    <p className="as-subtitle">
                        Enter personal and academic information to
                        register a student.
                    </p>
                </div>

                <Link
                    to="/students"
                    className="as-back-link"
                >
                    ← Back to Students
                </Link>
            </div>

            <form
                className="as-card"
                onSubmit={handleSubmit}
            >
                {optionsError && (
                    <div
                        className="as-alert as-alert-error"
                        role="alert"
                    >
                        Unable to load form options: {optionsError}

                        <button
                            type="button"
                            className="as-button as-button-secondary"
                            onClick={() => window.location.reload()}
                        >
                            Reload Page
                        </button>
                    </div>
                )}

                {submitError && (
                    <div
                        className="as-alert as-alert-error"
                        role="alert"
                    >
                        {submitError}
                    </div>
                )}

                {successMessage && (
                    <div
                        className="as-alert as-alert-success"
                        role="status"
                    >
                        {successMessage}
                    </div>
                )}

                <section className="as-section">
                    <div className="as-section-heading">
                        <span className="as-section-number">
                            01
                        </span>

                        <div>
                            <h2>Personal Information</h2>
                            <p>Basic details of the student</p>
                        </div>
                    </div>

                    <div className="as-grid">
                        <div className="as-field">
                            <label htmlFor="student-name">
                                Full Name *
                            </label>

                            <input
                                id="student-name"
                                type="text"
                                name="Name"
                                value={formData.Name}
                                onChange={handleChange}
                                placeholder="Enter full name"
                                minLength={3}
                                required
                            />

                            {displayError('Name')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="student-age">
                                Age *
                            </label>

                            <input
                                id="student-age"
                                type="number"
                                name="Age"
                                value={formData.Age}
                                onChange={handleChange}
                                placeholder="Enter age"
                                min="19"
                                required
                            />

                            {displayError('Age')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="student-email">
                                Email *
                            </label>

                            <input
                                id="student-email"
                                type="email"
                                name="Email"
                                value={formData.Email}
                                onChange={handleChange}
                                placeholder="student@example.com"
                                required
                            />

                            {displayError('Email')}
                        </div>

                        <div className="as-field">
                            <label htmlFor="student-phone">
                                Phone *
                            </label>

                            <input
                                id="student-phone"
                                type="tel"
                                name="Phone"
                                value={formData.Phone}
                                onChange={handleChange}
                                placeholder="10-digit phone number"
                                inputMode="numeric"
                                maxLength={10}
                                pattern="[0-9]{10}"
                                required
                            />

                            {displayError('Phone')}
                        </div>
                    </div>
                </section>

                <div className="as-divider" />

                <section className="as-section">
                    <div className="as-section-heading">
                        <span className="as-section-number">
                            02
                        </span>

                        <div>
                            <h2>Academic Information</h2>
                            <p>Course, current status, and subjects</p>
                        </div>
                    </div>

                    <div className="as-grid">
                        <div className="as-field">
                            <label htmlFor="student-course">
                                Course *
                            </label>

                            <select
                                id="student-course"
                                name="Course"
                                value={formData.Course}
                                onChange={handleChange}
                                required
                                disabled={loadingOptions}
                            >
                                <option value="">
                                    {loadingOptions
                                        ? 'Loading courses...'
                                        : 'Select a course'}
                                </option>

                                {courses.map((course) => (
                                    <option
                                        key={course.id}
                                        value={course.id}
                                    >
                                        {getOptionLabel(course, [
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
                            <label htmlFor="student-status">
                                Student Status *
                            </label>

                            <select
                                id="student-status"
                                name="status"
                                value={formData.status}
                                onChange={handleChange}
                                required
                            >
                                <option value="active">
                                    Active
                                </option>

                                <option value="inactive">
                                    Inactive
                                </option>

                                <option value="graduated">
                                    Graduated
                                </option>
                            </select>

                            {displayError('status')}
                        </div>
                    </div>

                    <div className="as-field as-options-field">
                        <div className="as-options-heading">
                            <label>Subjects</label>
                            <span>
                                Optional · Select all that apply
                            </span>
                        </div>

                        {loadingOptions ? (
                            <p className="as-muted">
                                Loading subjects...
                            </p>
                        ) : subjects.length === 0 ? (
                            <p className="as-muted">
                                No subjects available.
                            </p>
                        ) : (
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
                                            onChange={(event) =>
                                                handleCheckboxChange(
                                                    event,
                                                    'subjects'
                                                )
                                            }
                                        />

                                        <span>
                                            {getOptionLabel(subject, [
                                                'name',
                                                'Name',
                                                'subject_name',
                                                'title',
                                            ])}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        )}

                        {displayError('subjects')}
                    </div>
                </section>

                <div className="as-form-footer">
                    <p className="as-required-note">
                        * Required fields
                    </p>

                    <div className="as-actions">
                        <Link
                            to="/students"
                            className="as-button as-button-secondary"
                        >
                            Cancel
                        </Link>

                        <button
                            type="submit"
                            className="as-button as-button-primary"
                            disabled={submitting || loadingOptions}
                        >
                            {submitting ? (
                                <>
                                    <span className="as-spinner" />
                                    Adding Student...
                                </>
                            ) : (
                                <>
                                    <span aria-hidden="true">
                                        ＋
                                    </span>
                                    Add Student
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}

export default AddStudent;
