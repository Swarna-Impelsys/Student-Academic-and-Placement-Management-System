
import { useEffect, useRef, useState } from 'react';
import api from '../services/api';
import './SubjectSelection.css';

// Safely handle direct arrays and paginated API responses.
function getList(data) {
    if (Array.isArray(data)) return data;

    return Array.isArray(data?.results) ? data.results : [];
}

// Normalize IDs so string and number IDs can be compared consistently.
function normalizeId(id) {
    const numericId = Number(id);

    return Number.isInteger(numericId) && numericId > 0
        ? numericId
        : null;
}

function SubjectSelection() {
    const [subjects, setSubjects] = useState([]);
    const [rule, setRule] = useState(null);
    const [savedSelection, setSavedSelection] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [saveError, setSaveError] = useState('');
    const [selectedOptional, setSelectedOptional] = useState([]);
    const [selectedElective, setSelectedElective] = useState([]);
    const [validationError, setValidationError] = useState('');
    const [saving, setSaving] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');

    const savingRef = useRef(false);

    useEffect(() => {
        async function loadSubjectSelection() {
            try {
                setLoading(true);
                setError('');

                // 1. Find the logged-in student's course.
                const dashboardResponse = await api.get(
                    'student-dashboard/'
                );

                const student = dashboardResponse.data?.student;

                // Supports Course as an ID or a nested object.
                const courseId = normalizeId(
                    student?.Course?.id ?? student?.Course
                );

                if (!courseId) {
                    throw new Error(
                        'Your course is not assigned to your student record.'
                    );
                }

                // 2. Load subjects and selection rules for that course.
                const [
                    subjectsResponse,
                    rulesResponse,
                    selectionResponse,
                ] = await Promise.all([
                    api.get('course-subjects/', {
                        params: { course: courseId },
                    }),
                    api.get('course-selection-rules/', {
                        params: { course: courseId },
                    }),
                    api.get('student/subject-selection/'),
                ]);

                const subjectList = getList(subjectsResponse.data);
                const rulesList = getList(rulesResponse.data);

                setSubjects(subjectList);

                const matchingRule = rulesList.find(
                    (item) =>
                        normalizeId(item.course?.id ?? item.course) === courseId
                );

                setRule(matchingRule || null);

                const selectionData = selectionResponse.data || {};

                setSavedSelection(selectionData);

                // Restore previously saved optional and elective subjects.
                const savedSubjects = getList(
                    selectionData.selected_subject_details
                );

                setSelectedOptional(
                    savedSubjects
                        .filter((item) => item.category === 'optional')
                        .map((item) => normalizeId(item.id))
                        .filter((id) => id !== null)
                );

                setSelectedElective(
                    savedSubjects
                        .filter((item) => item.category === 'elective')
                        .map((item) => normalizeId(item.id))
                        .filter((id) => id !== null)
                );
            } catch (err) {
                setError(
                    err.response?.data?.error ||
                    err.response?.data?.detail ||
                    err.message ||
                    'Failed to load subject selection.'
                );
            } finally {
                setLoading(false);
            }
        }

        loadSubjectSelection();
    }, []);

    function handleOptionalChange(subjectId) {
        const normalizedId = normalizeId(subjectId);

        if (normalizedId === null) return;

        setSelectedOptional((previous) => {
            if (previous.includes(normalizedId)) {
                return previous.filter((id) => id !== normalizedId);
            }

            if (previous.length >= (rule?.optional_subject_count ?? 0)) {
                return previous;
            }

            return [...previous, normalizedId];
        });

        setValidationError('');
        setSuccessMessage('');
    }

    function handleElectiveChange(subjectId) {
        const normalizedId = normalizeId(subjectId);

        if (normalizedId === null) return;

        setSelectedElective((previous) => {
            if (previous.includes(normalizedId)) {
                return previous.filter((id) => id !== normalizedId);
            }

            if (previous.length >= (rule?.elective_subject_count ?? 0)) {
                return previous;
            }

            return [...previous, normalizedId];
        });

        setValidationError('');
        setSuccessMessage('');
    }

    // Validate the deadline safely.
    const deadlineDate = rule?.selection_deadline
        ? new Date(rule.selection_deadline)
        : null;

    const validDeadline =
        deadlineDate && !Number.isNaN(deadlineDate.getTime());

    const deadlinePassed =
        !validDeadline || new Date() > deadlineDate;

    const selectionDisabled =
        !rule?.is_selection_open || deadlinePassed;

    function validateSelection() {
        setValidationError('');

        if (selectionDisabled) {
            setValidationError(
                'Subject selection is closed or the deadline has passed.'
            );
            return false;
        }

        if (
            selectedOptional.length !== rule.optional_subject_count
        ) {
            setValidationError(
                `Select exactly ${rule.optional_subject_count} optional subjects.`
            );
            return false;
        }

        if (
            selectedElective.length !== rule.elective_subject_count
        ) {
            const subjectWord =
                rule.elective_subject_count === 1
                    ? 'subject'
                    : 'subjects';

            setValidationError(
                `Select exactly ${rule.elective_subject_count} elective ${subjectWord}.`
            );
            return false;
        }

        return true;
    }

    async function handleSaveSelection() {
        if (savingRef.current) {
            return;
        }

        if (!validateSelection()) {
            return;
        }

        savingRef.current = true;

        setSaving(true);
        setSuccessMessage('');
        setSaveError('');

        try {
            const selectedSubjectIds = [
                ...selectedOptional,
                ...selectedElective,
            ];

            const response = await api.post(
                'student/subject-selection/',
                {
                    selected_subjects: selectedSubjectIds,
                }
            );

            setSavedSelection(response.data);

            setSuccessMessage(
                'Your subject selection has been saved successfully.'
            );

            setValidationError('');
        } catch (err) {
            setSaveError(
                err.response?.data?.error ||
                err.response?.data?.detail ||
                'Failed to save subject selection. Please try again.'
            );
        } finally {
            savingRef.current = false;
            setSaving(false);
        }
    }

    if (loading) {
        return (
            <div className="card">
                <h2>Subject Selection</h2>
                <p role="status">
                    Loading your subjects and selection rules...
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="card">
                <h2>Subject Selection</h2>

                <p className="alert alert-error" role="alert">
                    Unable to load subject selection: {error}
                </p>

                <p>Please try refreshing the page.</p>
            </div>
        );
    }

    if (!rule) {
        return (
            <div className="card">
                <h2>Subject Selection</h2>
                <p>
                    Selection rules have not been configured for your course.
                </p>
            </div>
        );
    }

    const compulsorySubjects = subjects.filter(
        (item) => item.category === 'compulsory'
    );

    const optionalSubjects = subjects.filter(
        (item) => item.category === 'optional'
    );

    const electiveSubjects = subjects.filter(
        (item) => item.category === 'elective'
    );

    return (
        <div className="card subject-selection-card">
            <h2>Subject Selection</h2>

            <p>
                <strong>Course:</strong> {rule.course_name}
            </p>

            <p>
                <strong>Optional subjects to choose:</strong>{' '}
                {rule.optional_subject_count}
            </p>

            <p>
                <strong>Elective subjects to choose:</strong>{' '}
                {rule.elective_subject_count}
            </p>

            <p>
                <strong>Selection status:</strong>{' '}
                {rule.is_selection_open ? 'Open' : 'Closed'}
            </p>

            {selectionDisabled && (
                <p role="status">
                    Subject selection is closed or the deadline has passed.
                    You can still view your saved selection.
                </p>
            )}

            <p>
                <strong>Deadline:</strong>{' '}
                {validDeadline
                    ? deadlineDate.toLocaleString()
                    : 'No valid deadline configured'}
            </p>

            {validationError && (
                <p className="alert alert-error" role="alert">
                    {validationError}
                </p>
            )}

            {saveError && (
                <p className="alert alert-error" role="alert">
                    {saveError}
                </p>
            )}

            {successMessage && (
                <p className="alert alert-success" role="status">
                    {successMessage}
                </p>
            )}

            <h3>Compulsory Subjects</h3>

            {compulsorySubjects.length ? (
                compulsorySubjects.map((item) => (
                    <label key={item.id} className="subject-option">
                        <input
                            type="checkbox"
                            checked
                            disabled
                            readOnly
                        />
                        {item.subject_name} — Compulsory
                    </label>
                ))
            ) : (
                <p>No compulsory subjects configured.</p>
            )}

            <h3>
                Optional Subjects (
                {selectedOptional.length}/{rule.optional_subject_count} selected)
            </h3>

            {optionalSubjects.length ? (
                optionalSubjects.map((item) => {
                    const normalizedId = normalizeId(item.id);
                    const isSelected =
                        normalizedId !== null &&
                        selectedOptional.includes(normalizedId);

                    return (
                        <label key={item.id} className="subject-option">
                            <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleOptionalChange(item.id)}
                                disabled={
                                    selectionDisabled ||
                                    (
                                        selectedOptional.length >=
                                            rule.optional_subject_count &&
                                        !isSelected
                                    )
                                }
                            />
                            {item.subject_name}
                        </label>
                    );
                })
            ) : (
                <p>No optional subjects available.</p>
            )}

            <h3>
                Elective Subjects (
                {selectedElective.length}/{rule.elective_subject_count} selected)
            </h3>

            {electiveSubjects.length ? (
                electiveSubjects.map((item) => {
                    const normalizedId = normalizeId(item.id);
                    const isSelected =
                        normalizedId !== null &&
                        selectedElective.includes(normalizedId);

                    return (
                        <label key={item.id} className="subject-option">
                            <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => handleElectiveChange(item.id)}
                                disabled={
                                    selectionDisabled ||
                                    (
                                        selectedElective.length >=
                                            rule.elective_subject_count &&
                                        !isSelected
                                    )
                                }
                            />
                            {item.subject_name}
                        </label>
                    );
                })
            ) : (
                <p>No elective subjects available.</p>
            )}

            <button
                type="button"
                className="btn btn-primary"
                onClick={handleSaveSelection}
                disabled={saving || selectionDisabled}
            >
                {saving ? 'Saving...' : 'Save Selection'}
            </button>

            <h3>Saved Selection</h3>

            {savedSelection?.selected_subject_details?.length ? (
                savedSelection.selected_subject_details.map((item) => (
                    <p key={item.id}>
                        {item.subject_name} ({item.category})
                    </p>
                ))
            ) : (
                <p>You have not saved a selection yet.</p>
            )}
        </div>
    );
}

export default SubjectSelection;
