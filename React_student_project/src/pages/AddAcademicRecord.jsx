
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import {
    getStudents,
    getSubjects,
    createAcademicRecord,
} from '../services/studentService';

import useApi from '../hooks/useApi';
import './AcademicRecords.css';

function AddAcademicRecord() {
    const navigate = useNavigate();

    const [students, setStudents] = useState([]);
    const [subjects, setSubjects] = useState([]);

    const [optionsLoading, setOptionsLoading] = useState(true);
    const [optionsError, setOptionsError] = useState('');

    const [form, setForm] = useState({
        student: '',
        semester: '',
        subject: '',
        marks: '',
        attendance: '',
        backlog: false,
    });

    const { loading, error, setError, execute } = useApi();
    const [success, setSuccess] = useState('');

    // Load students and subjects for dropdowns.
    useEffect(() => {
        let active = true;

        async function loadOptions() {
            setOptionsLoading(true);
            setOptionsError('');

            try {
                const results = await Promise.allSettled([
                    getStudents(),
                    getSubjects(),
                ]);

                if (!active) return;

                const [studentResult, subjectResult] = results;
                const errors = [];

                // Handle student response.
                if (studentResult.status === 'fulfilled') {
                    const studentData = studentResult.value;

                    setStudents(
                        Array.isArray(studentData)
                            ? studentData
                            : studentData?.results ?? []
                    );
                } else {
                    setStudents([]);
                    errors.push('Unable to load students.');
                    console.error(
                        'Failed to load students:',
                        studentResult.reason
                    );
                }

                // Handle subject response.
                if (subjectResult.status === 'fulfilled') {
                    const subjectData = subjectResult.value;

                    setSubjects(
                        Array.isArray(subjectData)
                            ? subjectData
                            : subjectData?.results ?? []
                    );
                } else {
                    setSubjects([]);
                    errors.push('Unable to load subjects.');
                    console.error(
                        'Failed to load subjects:',
                        subjectResult.reason
                    );
                }

                if (errors.length > 0) {
                    setOptionsError(errors.join(' '));
                }
            } catch (err) {
                if (!active) return;

                console.error('Failed to load form options:', err);

                setOptionsError(
                    'Unable to load student and subject options. Please try again.'
                );
            } finally {
                if (active) {
                    setOptionsLoading(false);
                }
            }
        }

        loadOptions();

        return () => {
            active = false;
        };
    }, []);

    // Handle form input changes.
    function handleChange(event) {
        const { name, value, checked, type } = event.target;

        setForm((previous) => ({
            ...previous,
            [name]: type === 'checkbox' ? checked : value,
        }));
    }

    // Submit the new academic record.
    async function handleSubmit(event) {
        event.preventDefault();

        setError('');
        setSuccess('');

        if (optionsLoading || optionsError) {
            return;
        }

        try {
            await execute(() =>
                createAcademicRecord({
                    student: Number(form.student),
                    semester: Number(form.semester),
                    subject: Number(form.subject),
                    marks: Number(form.marks),
                    attendance: Number(form.attendance),
                    backlog: form.backlog,
                })
            );

            setSuccess('Academic record created successfully!');

            setTimeout(() => {
                navigate('/academic-records');
            }, 1000);
        } catch {
            // The useApi hook displays the API error.
        }
    }

    return (
        <div className="add-academic-record">
            <h2>Add Academic Record</h2>

            <p>
                Enter the student's academic information below.
            </p>

            {/* Dropdown loading status */}
            {optionsLoading && (
                <p role="status">
                    Loading students and subjects...
                </p>
            )}

            {/* Dropdown loading errors */}
            {optionsError && (
                <p role="alert">
                    {optionsError}
                </p>
            )}

            {/* API submission error */}
            {error && (
                <p role="alert">
                    {error}
                </p>
            )}

            {/* Success message */}
            {success && (
                <p role="status">
                    {success}
                </p>
            )}

            <form onSubmit={handleSubmit}>
                {/* Student dropdown */}
                <div>
                    <label htmlFor="student">
                        Student
                    </label>

                    <select
                        id="student"
                        name="student"
                        value={form.student}
                        onChange={handleChange}
                        disabled={optionsLoading || !!optionsError}
                        required
                    >
                        <option value="">
                            {optionsLoading
                                ? 'Loading students...'
                                : 'Select student'}
                        </option>

                        {students.map((item) => (
                            <option
                                key={item.id}
                                value={item.id}
                            >
                                {item.Name} (ID: {item.id})
                            </option>
                        ))}
                    </select>

                    {!optionsLoading &&
                        !optionsError &&
                        students.length === 0 && (
                            <small>No students available.</small>
                        )}
                </div>

                {/* Semester */}
                <div>
                    <label htmlFor="semester">
                        Semester
                    </label>

                    <input
                        id="semester"
                        name="semester"
                        type="number"
                        min="1"
                        value={form.semester}
                        onChange={handleChange}
                        required
                    />
                </div>

                {/* Subject dropdown */}
                <div>
                    <label htmlFor="subject">
                        Subject
                    </label>

                    <select
                        id="subject"
                        name="subject"
                        value={form.subject}
                        onChange={handleChange}
                        disabled={optionsLoading || !!optionsError}
                        required
                    >
                        <option value="">
                            {optionsLoading
                                ? 'Loading subjects...'
                                : 'Select subject'}
                        </option>

                        {subjects.map((item) => (
                            <option
                                key={item.id}
                                value={item.id}
                            >
                                {item.name}
                            </option>
                        ))}
                    </select>

                    {!optionsLoading &&
                        !optionsError &&
                        subjects.length === 0 && (
                            <small>No subjects available.</small>
                        )}
                </div>

                {/* Marks */}
                <div>
                    <label htmlFor="marks">
                        Marks (0–100)
                    </label>

                    <input
                        id="marks"
                        name="marks"
                        type="number"
                        min="0"
                        max="100"
                        step="any"
                        value={form.marks}
                        onChange={handleChange}
                        required
                    />
                </div>

                {/* Attendance */}
                <div>
                    <label htmlFor="attendance">
                        Attendance (0–100%)
                    </label>

                    <input
                        id="attendance"
                        name="attendance"
                        type="number"
                        min="0"
                        max="100"
                        step="any"
                        value={form.attendance}
                        onChange={handleChange}
                        required
                    />
                </div>

                {/* Backlog checkbox */}
                <div>
                    <label>
                        <input
                            name="backlog"
                            type="checkbox"
                            checked={form.backlog}
                            onChange={handleChange}
                        />

                        Has backlog
                    </label>
                </div>

                {/* Form actions */}
                <button
                    type="submit"
                    disabled={
                        loading ||
                        optionsLoading ||
                        !!optionsError ||
                        students.length === 0 ||
                        subjects.length === 0
                    }
                >
                    {loading
                        ? 'Saving...'
                        : 'Save Academic Record'}
                </button>

                <button
                    type="button"
                    onClick={() => navigate('/academic-records')}
                    disabled={loading}
                >
                    Cancel
                </button>
            </form>
        </div>
    );
}

export default AddAcademicRecord;
