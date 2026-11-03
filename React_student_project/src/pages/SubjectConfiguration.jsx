
import { useEffect, useState } from 'react';
import api from '../services/api';
import "./SubjectConfiguration.css";

function getList(data) {
    if (Array.isArray(data)) {
        return data;
    }

    if (Array.isArray(data?.results)) {
        return data.results;
    }

    return [];
}

function getErrorMessage(err, fallback) {
    const data = err.response?.data;

    if (typeof data === 'string') {
        return data;
    }

    return (
        data?.detail ||
        data?.error ||
        data?.non_field_errors?.[0] ||
        data?.name?.[0] ||
        data?.course?.[0] ||
        data?.subject?.[0] ||
        data?.category?.[0] ||
        data?.optional_subject_count?.[0] ||
        data?.elective_subject_count?.[0] ||
        fallback
    );
}

function SubjectConfiguration() {
    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [courseSubjects, setCourseSubjects] = useState([]);
    const [rules, setRules] = useState([]);

    const [editingRuleId, setEditingRuleId] = useState(null);
    const [ruleSaveSuccess, setRuleSaveSuccess] = useState('');
    const [ruleSaveError, setRuleSaveError] = useState('');
    const [savingRules, setSavingRules] = useState(false);
    const [editOptionalCount, setEditOptionalCount] = useState(0);
    const [editElectiveCount, setEditElectiveCount] = useState(0);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [loadAttempt, setLoadAttempt] = useState(0);

    const [selectedCourseId, setSelectedCourseId] = useState('');
    const [selectedSubjectId, setSelectedSubjectId] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('compulsory');
    const [assigning, setAssigning] = useState(false);
    const [assignmentError, setAssignmentError] = useState('');
    const [assignmentSuccess, setAssignmentSuccess] = useState('');

    const [newSubjectName, setNewSubjectName] = useState('');
    const [creatingSubject, setCreatingSubject] = useState(false);
    const [subjectCreateError, setSubjectCreateError] = useState('');
    const [subjectCreateSuccess, setSubjectCreateSuccess] = useState('');

    // Load all configuration data.
    // loadAttempt allows retrying after a failed request.
    useEffect(() => {
        let isActive = true;

        async function loadConfiguration() {
            setLoading(true);
            setError('');

            try {
                const [
                    coursesResponse,
                    subjectsResponse,
                    courseSubjectsResponse,
                    rulesResponse,
                ] = await Promise.all([
                    api.get('students/courses/'),
                    api.get('students/subjects/'),
                    api.get('course-subjects/'),
                    api.get('course-selection-rules/'),
                ]);

                if (!isActive) {
                    return;
                }

                const loadedCourses = getList(coursesResponse.data);
                const loadedSubjects = getList(subjectsResponse.data);
                const loadedCourseSubjects = getList(
                    courseSubjectsResponse.data
                );
                const loadedRules = getList(rulesResponse.data);

                setCourses(loadedCourses);
                setSubjects(loadedSubjects);
                setCourseSubjects(loadedCourseSubjects);
                setRules(loadedRules);

                // Clear selections that are no longer available.
                setSelectedCourseId((previous) => {
                    const stillExists = loadedCourses.some(
                        (course) => String(course.id) === String(previous)
                    );

                    return stillExists ? previous : '';
                });

                setSelectedSubjectId('');
                setAssignmentError('');
                setAssignmentSuccess('');
            } catch (err) {
                if (!isActive) {
                    return;
                }

                setError(
                    getErrorMessage(
                        err,
                        'Failed to load subject configuration. Please try again.'
                    )
                );
            } finally {
                if (isActive) {
                    setLoading(false);
                }
            }
        }

        loadConfiguration();

        return () => {
            isActive = false;
        };
    }, [loadAttempt]);

    // Return subjects not already assigned to the selected course.
    function getAvailableSubjects() {
        return subjects.filter(
            (subject) =>
                !courseSubjects.some(
                    (item) =>
                        Number(item.course) === Number(selectedCourseId) &&
                        Number(item.subject) === Number(subject.id)
                )
        );
    }

    // Clear old selection-rule messages.
    function clearRuleMessages() {
        setRuleSaveSuccess('');
        setRuleSaveError('');
    }

    function handleEditRules(rule) {
        clearRuleMessages();

        setEditingRuleId(rule.id);
        setEditOptionalCount(rule.optional_subject_count);
        setEditElectiveCount(rule.elective_subject_count);
    }

    function handleCancelEdit() {
        setEditingRuleId(null);
        clearRuleMessages();
    }

    // Assign a subject to a course.
    async function handleAssignSubject(event) {
        event.preventDefault();

        if (assigning || loading) {
            return;
        }

        setAssignmentError('');
        setAssignmentSuccess('');

        if (!selectedCourseId || !selectedSubjectId) {
            setAssignmentError(
                'Please select both a course and a subject.'
            );
            return;
        }

        const alreadyAssigned = courseSubjects.some(
            (item) =>
                Number(item.course) === Number(selectedCourseId) &&
                Number(item.subject) === Number(selectedSubjectId)
        );

        if (alreadyAssigned) {
            setAssignmentError(
                'This subject is already assigned to the selected course.'
            );
            return;
        }

        setAssigning(true);

        try {
            const response = await api.post('course-subjects/', {
                course: Number(selectedCourseId),
                subject: Number(selectedSubjectId),
                category: selectedCategory,
            });

            setCourseSubjects((previous) => [
                ...previous,
                response.data,
            ]);

            setSelectedSubjectId('');
            setAssignmentSuccess('Subject assigned successfully.');
        } catch (err) {
            setAssignmentError(
                getErrorMessage(
                    err,
                    'Failed to assign subject. Check whether it is already assigned and try again.'
                )
            );
        } finally {
            setAssigning(false);
        }
    }

    // Create a new subject.
    async function handleCreateSubject(event) {
        event.preventDefault();

        if (creatingSubject) {
            return;
        }

        const subjectName = newSubjectName.trim();

        setSubjectCreateError('');
        setSubjectCreateSuccess('');

        if (!subjectName) {
            setSubjectCreateError('Please enter a subject name.');
            return;
        }

        // Check duplicates in the currently loaded subjects.
        const duplicateSubject = subjects.some(
            (subject) =>
                subject.name?.trim().toLowerCase() ===
                subjectName.toLowerCase()
        );

        if (duplicateSubject) {
            setSubjectCreateError(
                'A subject with this name already exists.'
            );
            return;
        }

        setCreatingSubject(true);

        try {
            const response = await api.post('students/subjects/', {
                name: subjectName,
            });

            setSubjects((previous) => [
                ...previous,
                response.data,
            ]);

            setNewSubjectName('');
            setSubjectCreateSuccess('Subject created successfully.');
        } catch (err) {
            setSubjectCreateError(
                getErrorMessage(
                    err,
                    'Failed to create subject. The name may already exist.'
                )
            );
        } finally {
            setCreatingSubject(false);
        }
    }

    // Save optional and elective selection rules.
    async function handleSaveRules(rule) {
        if (savingRules) {
            return;
        }

        clearRuleMessages();

        const optionalCount = Number(editOptionalCount);
        const electiveCount = Number(editElectiveCount);

        if (
            editOptionalCount === '' ||
            editElectiveCount === '' ||
            !Number.isInteger(optionalCount) ||
            !Number.isInteger(electiveCount) ||
            optionalCount < 0 ||
            electiveCount < 0
        ) {
            setRuleSaveError(
                'Enter a whole number of 0 or greater for both subject counts.'
            );
            return;
        }

        if (optionalCount > 100 || electiveCount > 100) {
            setRuleSaveError(
                'Optional and elective subject counts cannot exceed 100.'
            );
            return;
        }

        setSavingRules(true);

        try {
            const response = await api.patch(
                `courses/${rule.course}/selection-rules/`,
                {
                    optional_subject_count: optionalCount,
                    elective_subject_count: electiveCount,
                }
            );

            setRules((previousRules) =>
                previousRules.map((item) =>
                    item.id === rule.id
                        ? { ...item, ...response.data }
                        : item
                )
            );

            setRuleSaveSuccess('Selection rules saved successfully.');
            setEditingRuleId(null);
        } catch (err) {
            setRuleSaveError(
                getErrorMessage(
                    err,
                    'Failed to save selection rules. Please try again.'
                )
            );

            console.error(
                'Failed to save rules:',
                err.response?.data || err.message
            );
        } finally {
            setSavingRules(false);
        }
    }

    if (loading) {
        return (
            <div className="card subject-config-layout">
                <h2>Subject Configuration</h2>
                <p role="status">Loading configuration...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="card subject-config-layout">
                <h2>Subject Configuration</h2>

                <p className="alert alert-error" role="alert">
                    {error}
                </p>

                <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() =>
                        setLoadAttempt((previous) => previous + 1)
                    }
                >
                    Retry Loading
                </button>
            </div>
        );
    }

    const availableSubjects = getAvailableSubjects();

    return (
        <div className="card subject-config-layout">
            <h2>Subject Configuration</h2>

            {/* Select a course */}
            <div className="subject-config-section">
                <div className="form-group">
                    <label htmlFor="course-select">
                        Select Course
                    </label>

                    <select
                        id="course-select"
                        value={selectedCourseId}
                        onChange={(event) => {
                            setSelectedCourseId(event.target.value);
                            setSelectedSubjectId('');
                            setAssignmentError('');
                            setAssignmentSuccess('');
                        }}
                        disabled={assigning}
                    >
                        <option value="">Choose a course</option>

                        {courses.map((course) => (
                            <option key={course.id} value={course.id}>
                                {course.name}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Course list */}
            <div className="subject-config-section">
                <h3>Courses ({courses.length})</h3>

                <div className="subject-config-list">
                    {courses.map((course) => (
                        <p key={course.id}>{course.name}</p>
                    ))}
                </div>
            </div>

            {/* Available subjects */}
            <div className="subject-config-section">
                <h3>Available Subjects ({subjects.length})</h3>

                <form onSubmit={handleCreateSubject}>
                    <div className="form-group">
                        <label htmlFor="new-subject-name">
                            New Subject Name
                        </label>

                        <input
                            id="new-subject-name"
                            type="text"
                            value={newSubjectName}
                            onChange={(event) => {
                                setNewSubjectName(event.target.value);
                                setSubjectCreateError('');
                                setSubjectCreateSuccess('');
                            }}
                            placeholder="Enter subject name"
                            required
                            disabled={creatingSubject}
                        />
                    </div>

                    {subjectCreateError && (
                        <p className="alert alert-error" role="alert">
                            {subjectCreateError}
                        </p>
                    )}

                    {subjectCreateSuccess && (
                        <p className="alert alert-success" role="status">
                            {subjectCreateSuccess}
                        </p>
                    )}

                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={
                            creatingSubject || !newSubjectName.trim()
                        }
                    >
                        {creatingSubject ? 'Creating...' : 'Create Subject'}
                    </button>
                </form>

                <div className="subject-config-list">
                    {subjects.map((subject) => (
                        <p key={subject.id}>
                            {subject.name}
                        </p>
                    ))}
                </div>
            </div>

            {/* Assigned subjects */}
            <div className="subject-config-section">
                <h3>Assigned Subjects</h3>

                {!selectedCourseId ? (
                    <p>Select a course to view its assigned subjects.</p>
                ) : (
                    <div className="subject-config-category-grid">
                        {['compulsory', 'optional', 'elective'].map(
                            (category) => {
                                const assignedSubjects = courseSubjects.filter(
                                    (item) =>
                                        Number(item.course) ===
                                            Number(selectedCourseId) &&
                                        item.category === category
                                );

                                return (
                                    <div
                                        key={category}
                                        className="subject-config-category-card"
                                    >
                                        <h4>
                                            {category.charAt(0).toUpperCase() +
                                                category.slice(1)}{' '}
                                            Subjects ({assignedSubjects.length})
                                        </h4>

                                        {assignedSubjects.length === 0 ? (
                                            <p>
                                                No {category} subjects assigned.
                                            </p>
                                        ) : (
                                            assignedSubjects.map((item) => (
                                                <p key={item.id}>
                                                    {item.subject_name}
                                                </p>
                                            ))
                                        )}
                                    </div>
                                );
                            }
                        )}
                    </div>
                )}
            </div>

            {/* Assign a subject */}
            <div className="subject-config-section">
                <h3>Assign Subject to Course</h3>

                {assignmentError && (
                    <p className="alert alert-error" role="alert">
                        {assignmentError}
                    </p>
                )}

                {assignmentSuccess && (
                    <p className="alert alert-success" role="status">
                        {assignmentSuccess}
                    </p>
                )}

                {!selectedCourseId ? (
                    <p>Select a course before assigning subjects.</p>
                ) : (
                    <form onSubmit={handleAssignSubject}>
                        <div className="form-group">
                            <label htmlFor="subject-select">
                                Select Subject
                            </label>

                            <select
                                id="subject-select"
                                value={selectedSubjectId}
                                onChange={(event) => {
                                    setSelectedSubjectId(event.target.value);
                                    setAssignmentError('');
                                    setAssignmentSuccess('');
                                }}
                                required
                                disabled={assigning || loading}
                            >
                                <option value="">Choose a subject</option>

                                {availableSubjects.map((subject) => (
                                    <option
                                        key={subject.id}
                                        value={subject.id}
                                    >
                                        {subject.name}
                                    </option>
                                ))}
                            </select>

                            {availableSubjects.length === 0 && (
                                <p>
                                    No available subjects remain for this course.
                                </p>
                            )}
                        </div>

                        <div className="form-group">
                            <label htmlFor="category-select">
                                Subject Category
                            </label>

                            <select
                                id="category-select"
                                value={selectedCategory}
                                onChange={(event) => {
                                    setSelectedCategory(event.target.value);
                                    setAssignmentError('');
                                    setAssignmentSuccess('');
                                }}
                                disabled={assigning || loading}
                            >
                                <option value="compulsory">Compulsory</option>
                                <option value="optional">Optional</option>
                                <option value="elective">Elective</option>
                            </select>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={
                                assigning ||
                                loading ||
                                !selectedSubjectId ||
                                availableSubjects.length === 0
                            }
                        >
                            {assigning ? 'Assigning...' : 'Assign Subject'}
                        </button>
                    </form>
                )}
            </div>

            {/* Selection rules */}
            <div className="subject-config-section">
                <h3>Selection Rules ({rules.length})</h3>

                {rules.map((rule) => (
                    <div
                        key={rule.id}
                        className="subject-config-rule-card"
                    >
                        <p>
                            {rule.course_name}: {rule.optional_subject_count}{' '}
                            optional, {rule.elective_subject_count} elective,{' '}
                            {rule.is_selection_open ? 'Open' : 'Closed'}
                        </p>

                        <button
                            type="button"
                            onClick={() => handleEditRules(rule)}
                            disabled={savingRules}
                        >
                            Edit Rules
                        </button>

                        {editingRuleId === rule.id && (
                            <div className="subject-config-rule-edit">
                                <h4>Edit Rules for {rule.course_name}</h4>

                                <div className="form-group">
                                    <label htmlFor={`optional-count-${rule.id}`}>
                                        Optional Subject Count
                                    </label>

                                    <input
                                        id={`optional-count-${rule.id}`}
                                        type="number"
                                        min="0"
                                        max="100"
                                        step="1"
                                        required
                                        aria-invalid={Boolean(ruleSaveError)}
                                        aria-describedby={
                                            ruleSaveError
                                                ? 'rule-save-error'
                                                : undefined
                                        }
                                        value={editOptionalCount}
                                        onChange={(event) => {
                                            clearRuleMessages();

                                            setEditOptionalCount(
                                                event.target.value === ''
                                                    ? ''
                                                    : Number(event.target.value)
                                            );
                                        }}
                                        disabled={savingRules}
                                    />
                                </div>

                                <div className="form-group">
                                    <label htmlFor={`elective-count-${rule.id}`}>
                                        Elective Subject Count
                                    </label>

                                    <input
                                        id={`elective-count-${rule.id}`}
                                        type="number"
                                        min="0"
                                        max="100"
                                        step="1"
                                        required
                                        aria-invalid={Boolean(ruleSaveError)}
                                        aria-describedby={
                                            ruleSaveError
                                                ? 'rule-save-error'
                                                : undefined
                                        }
                                        value={editElectiveCount}
                                        onChange={(event) => {
                                            clearRuleMessages();

                                            setEditElectiveCount(
                                                event.target.value === ''
                                                    ? ''
                                                    : Number(event.target.value)
                                            );
                                        }}
                                        disabled={savingRules}
                                    />
                                </div>

                                <button
                                    type="button"
                                    onClick={() => handleSaveRules(rule)}
                                    disabled={savingRules}
                                >
                                    {savingRules ? 'Saving...' : 'Save Rules'}
                                </button>

                                <button
                                    type="button"
                                    onClick={handleCancelEdit}
                                    disabled={savingRules}
                                >
                                    Cancel
                                </button>
                            </div>
                        )}
                    </div>
                ))}

                {/* Selection-rule messages */}
                {ruleSaveSuccess && (
                    <p className="alert alert-success" role="status">
                        {ruleSaveSuccess}
                    </p>
                )}

                {ruleSaveError && (
                    <p
                        id="rule-save-error"
                        className="alert alert-error"
                        role="alert"
                    >
                        {ruleSaveError}
                    </p>
                )}
            </div>
        </div>
    );
}

export default SubjectConfiguration;
