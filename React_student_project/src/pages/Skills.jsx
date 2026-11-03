
import { useEffect, useState } from 'react';

import {
    getSkills,
    createSkill,
    updateSkill,
    deleteSkill,
    getMySkills,
    createMySkill,
    updateMySkill,
    deleteMySkill,
} from '../services/studentService';

function getErrorMessage(err, fallback) {
    const data = err.response?.data;

    if (typeof data?.detail === 'string') return data.detail;
    if (typeof data?.error === 'string') return data.error;
    if (typeof data?.name?.[0] === 'string') return data.name[0];

    return fallback;
}

function getList(data) {
    return Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
            ? data.results
            : [];
}

function Skills() {
    const role = (localStorage.getItem('role') || '')
        .trim()
        .toLowerCase();

    const isAdmin = role === 'admin';
    const isStudent = role === 'student';
    const isTeacher = role === 'teacher';

    const [skills, setSkills] = useState([]);
    const [mySkills, setMySkills] = useState([]);

    const [name, setName] = useState('');
    const [editingId, setEditingId] = useState(null);

    const [personalName, setPersonalName] = useState('');
    const [editingPersonalId, setEditingPersonalId] = useState(null);

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Load master skills for Admin only.
    async function loadSkills() {
        const data = await getSkills();
        setSkills(getList(data));
    }

    // Load personal skills for the logged-in Student.
    async function loadMySkills() {
        const data = await getMySkills();
        setMySkills(getList(data));
    }

    // Load data according to the logged-in role.
    useEffect(() => {
        let active = true;

        async function loadData() {
            if (isTeacher) {
                setLoading(false);
                return;
            }

            setLoading(true);
            setError('');

            try {
                if (isAdmin) {
                    const data = await getSkills();

                    if (!active) return;

                    setSkills(getList(data));
                }

                if (isStudent) {
                    const data = await getMySkills();

                    if (!active) return;

                    setMySkills(getList(data));
                }
            } catch (err) {
                if (!active) return;

                setError(
                    getErrorMessage(
                        err,
                        isAdmin
                            ? 'Unable to load master skills.'
                            : 'Unable to load your personal skills.'
                    )
                );
            } finally {
                if (active) {
                    setLoading(false);
                }
            }
        }

        loadData();

        return () => {
            active = false;
        };
    }, [isAdmin, isStudent, isTeacher]);

    // Start editing a master skill.
    function startEdit(skill) {
        if (!isAdmin) return;

        setEditingId(skill.id);
        setName(skill.name);
        setError('');
        setSuccess('');
    }

    // Cancel master skill editing.
    function cancelEdit() {
        setEditingId(null);
        setName('');
        setError('');
    }

    // Add or update a master skill.
    async function handleSubmit(event) {
        event.preventDefault();

        if (!isAdmin) return;

        setError('');
        setSuccess('');

        const trimmedName = name.trim();

        if (trimmedName.length < 2) {
            setError('Skill name must contain at least 2 characters.');
            return;
        }

        try {
            setSaving(true);

            if (editingId !== null) {
                await updateSkill(editingId, {
                    name: trimmedName,
                });

                setSuccess('Master skill updated successfully.');
            } else {
                await createSkill({
                    name: trimmedName,
                });

                setSuccess('Master skill added successfully.');
            }

            setName('');
            setEditingId(null);

            await loadSkills();
        } catch (err) {
            setError(
                getErrorMessage(
                    err,
                    'Unable to save the master skill.'
                )
            );
        } finally {
            setSaving(false);
        }
    }

    // Delete a master skill.
    async function handleDelete(skill) {
        if (!isAdmin) return;

        if (!window.confirm(`Delete the master skill "${skill.name}"?`)) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            await deleteSkill(skill.id);

            setSuccess('Master skill deleted successfully.');

            await loadSkills();
        } catch (err) {
            setError(
                getErrorMessage(
                    err,
                    'Unable to delete the master skill.'
                )
            );
        }
    }

    // Start editing a personal skill.
    function startPersonalEdit(skill) {
        if (!isStudent) return;

        setEditingPersonalId(skill.id);
        setPersonalName(skill.name);
        setError('');
        setSuccess('');
    }

    // Cancel personal skill editing.
    function cancelPersonalEdit() {
        setEditingPersonalId(null);
        setPersonalName('');
        setError('');
    }

    // Add or update a personal skill.
    async function handlePersonalSubmit(event) {
        event.preventDefault();

        if (!isStudent) return;

        const trimmedName = personalName.trim();

        setError('');
        setSuccess('');

        if (trimmedName.length < 2) {
            setError('Skill name must contain at least 2 characters.');
            return;
        }

        try {
            setSaving(true);

            if (editingPersonalId !== null) {
                await updateMySkill(editingPersonalId, {
                    name: trimmedName,
                });

                setSuccess('Your skill was updated successfully.');
            } else {
                await createMySkill({
                    name: trimmedName,
                });

                setSuccess('Your new skill was added successfully.');
            }

            setPersonalName('');
            setEditingPersonalId(null);

            await loadMySkills();
        } catch (err) {
            setError(
                getErrorMessage(
                    err,
                    'Unable to save your personal skill.'
                )
            );
        } finally {
            setSaving(false);
        }
    }

    // Delete a personal skill.
    async function handlePersonalDelete(skill) {
        if (!isStudent) return;

        if (!window.confirm(
            `Remove "${skill.name}" from your personal skills?`
        )) {
            return;
        }

        setError('');
        setSuccess('');

        try {
            await deleteMySkill(skill.id);

            setSuccess('Personal skill removed successfully.');

            await loadMySkills();
        } catch (err) {
            setError(
                getErrorMessage(
                    err,
                    'Unable to remove your personal skill.'
                )
            );
        }
    }

    if (isTeacher) {
        return (
            <div className="management-page">
                <div className="alert alert-error">
                    The Skills feature is not available for Teachers.
                </div>
            </div>
        );
    }

    return (
        <div className="management-page">
            <div className="management-header">
                <div>
                    <h2>
                        {isAdmin ? 'Skills Management' : 'My Skills'}
                    </h2>

                    <p>
                        {isAdmin
                            ? 'Manage the master skills available in Student PMS.'
                            : 'Maintain your personal skills.'}
                    </p>
                </div>

                <div className="skills-count">
                    <span>
                        {isAdmin ? 'Total Skills' : 'My Skills'}
                    </span>

                    <strong>
                        {isAdmin ? skills.length : mySkills.length}
                    </strong>
                </div>
            </div>

            {error && (
                <div className="alert alert-error">
                    {error}
                </div>
            )}

            {success && (
                <div className="alert alert-success">
                    {success}
                </div>
            )}

            {/* Admin master skill form */}
            {isAdmin && (
                <section className="management-card">
                    <div className="card-heading">
                        <div>
                            <h3>
                                {editingId !== null
                                    ? 'Edit Master Skill'
                                    : 'Add Master Skill'}
                            </h3>

                            <p>
                                Manage the shared skills list.
                            </p>
                        </div>
                    </div>

                    <form className="skill-form" onSubmit={handleSubmit}>
                        <div className="form-field">
                            <label htmlFor="skill-name">
                                Skill Name
                            </label>

                            <input
                                id="skill-name"
                                type="text"
                                value={name}
                                onChange={(event) =>
                                    setName(event.target.value)
                                }
                                placeholder="e.g. Python, React, SQL"
                                minLength={2}
                                required
                            />
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
                                        ? 'Update Skill'
                                        : 'Add Skill'}
                            </button>

                            {editingId !== null && (
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={cancelEdit}
                                    disabled={saving}
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>
                </section>
            )}

            {/* Student personal skill form and list */}
            {isStudent && (
                <section className="management-card">
                    <div className="card-heading">
                        <div>
                            <h3>
                                {editingPersonalId !== null
                                    ? 'Edit My Skill'
                                    : 'Add a Skill You Have Gained'}
                            </h3>

                            <p>
                                Add skills learned through courses,
                                projects, internships, or practice.
                                This does not change the Admin master list.
                            </p>
                        </div>
                    </div>

                    <form
                        className="skill-form"
                        onSubmit={handlePersonalSubmit}
                    >
                        <div className="form-field">
                            <label htmlFor="personal-skill-name">
                                My Skill
                            </label>

                            <input
                                id="personal-skill-name"
                                type="text"
                                value={personalName}
                                onChange={(event) =>
                                    setPersonalName(event.target.value)
                                }
                                placeholder="e.g. Docker, Git, Power BI"
                                minLength={2}
                                required
                            />
                        </div>

                        <div className="form-actions">
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={saving || loading}
                            >
                                {saving
                                    ? 'Saving...'
                                    : editingPersonalId !== null
                                        ? 'Update My Skill'
                                        : 'Add My Skill'}
                            </button>

                            {editingPersonalId !== null && (
                                <button
                                    type="button"
                                    className="btn btn-secondary"
                                    onClick={cancelPersonalEdit}
                                    disabled={saving}
                                >
                                    Cancel
                                </button>
                            )}
                        </div>
                    </form>

                    <div className="card-heading">
                        <div>
                            <h3>My Personal Skills</h3>

                            <p>
                                You can edit or remove only your own entries.
                            </p>
                        </div>

                        <span className="record-count">
                            {mySkills.length} skills
                        </span>
                    </div>

                    {loading ? (
                        <p className="empty-state">
                            Loading your skills...
                        </p>
                    ) : mySkills.length === 0 ? (
                        <div className="empty-state">
                            You haven't added any personal skills yet.
                        </div>
                    ) : (
                        <div className="table-container">
                            <table className="management-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Skill Name</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {mySkills.map((skill) => (
                                        <tr key={skill.id}>
                                            <td>#{skill.id}</td>
                                            <td>{skill.name}</td>
                                            <td>
                                                <div className="table-actions">
                                                    <button
                                                        type="button"
                                                        className="btn btn-edit"
                                                        onClick={() =>
                                                            startPersonalEdit(skill)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="btn btn-delete"
                                                        onClick={() =>
                                                            handlePersonalDelete(skill)
                                                        }
                                                    >
                                                        Remove
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            )}

            {/* Available master skills: Admin only */}
            {isAdmin && (
                <section className="management-card">
                    <div className="card-heading">
                        <div>
                            <h3>Available Master Skills</h3>

                            <p>
                                Manage the shared skills list using the actions below.
                            </p>
                        </div>

                        <span className="record-count">
                            {skills.length} skills
                        </span>
                    </div>

                    {loading ? (
                        <p className="empty-state">
                            Loading skills...
                        </p>
                    ) : skills.length === 0 ? (
                        <div className="empty-state">
                            No master skills found.
                        </div>
                    ) : (
                        <div className="table-container">
                            <table className="management-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Skill Name</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {skills.map((skill) => (
                                        <tr key={skill.id}>
                                            <td className="skill-id">
                                                #{skill.id}
                                            </td>

                                            <td>
                                                <span className="skill-name">
                                                    {skill.name}
                                                </span>
                                            </td>

                                            <td>
                                                <div className="table-actions">
                                                    <button
                                                        type="button"
                                                        className="btn btn-edit"
                                                        onClick={() =>
                                                            startEdit(skill)
                                                        }
                                                    >
                                                        Edit
                                                    </button>

                                                    <button
                                                        type="button"
                                                        className="btn btn-delete"
                                                        onClick={() =>
                                                            handleDelete(skill)
                                                        }
                                                    >
                                                        Delete
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}

export default Skills;
