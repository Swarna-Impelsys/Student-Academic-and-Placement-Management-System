
import { useEffect, useState } from 'react';
import api from '../services/api';
import './Courses.css';

function getList(data) {
    if (Array.isArray(data)) {
        return data;
    }

    return data?.results ?? [];
}

function getErrorMessage(err, fallback) {
    const data = err.response?.data;

    if (data?.detail) return data.detail;
    if (data?.error) return data.error;

    if (data && typeof data === 'object') {
        const firstError = Object.values(data).find(
            value => Array.isArray(value) && value.length > 0
        );

        if (firstError) return firstError[0];
    }

    return fallback;
}

function Courses() {
    const role = localStorage.getItem('role')?.trim().toLowerCase();

    const isAdmin = role === 'admin';
    const isTeacher = role === 'teacher';

    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const [courseName, setCourseName] = useState('');
    const [message, setMessage] = useState('');
    const [saving, setSaving] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);

    // View students
    const [selectedCourse, setSelectedCourse] = useState(null);
    const [students, setStudents] = useState([]);
    const [studentsLoading, setStudentsLoading] = useState(false);
    const [studentsError, setStudentsError] = useState('');

    // Admin-only teacher assignments
    const [assignmentCourse, setAssignmentCourse] = useState(null);
    const [teachers, setTeachers] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [selectedTeacher, setSelectedTeacher] = useState('');
    const [assignmentsLoading, setAssignmentsLoading] = useState(false);
    const [assignmentSaving, setAssignmentSaving] = useState(false);
    const [assignmentError, setAssignmentError] = useState('');
    const [assignmentMessage, setAssignmentMessage] = useState('');

    // Load courses
    async function fetchCourses() {
        try {
            setLoading(true);
            setError('');

            const response = await api.get('students/courses/');

            setCourses(getList(response.data));
        } catch (err) {
            setError(
                getErrorMessage(
                    err,
                    'Failed to load courses. Please try again.'
                )
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        fetchCourses();
    }, []);

    // Admin: add or edit a course
    const handleAddCourse = async (event) => {
        event.preventDefault();

        if (!isAdmin || saving) return;

        const name = courseName.trim();

        if (!name) {
            setMessage('Please enter a course name.');
            return;
        }

        setSaving(true);
        setMessage('');

        try {
            let response;

            if (editingCourse) {
                response = await api.patch(
                    `courses/${editingCourse.id}/`,
                    { name }
                );

                setCourses(previous =>
                    previous.map(course =>
                        course.id === editingCourse.id
                            ? { ...course, ...response.data }
                            : course
                    )
                );

                setMessage('Course updated successfully.');
            } else {
                response = await api.post(
                    'students/courses/',
                    { name }
                );

                setCourses(previous => [
                    ...previous,
                    response.data
                ]);

                setMessage('Course added successfully.');
            }

            setCourseName('');
            setEditingCourse(null);
        } catch (err) {
            setMessage(
                getErrorMessage(
                    err,
                    'Failed to save course. Please try again.'
                )
            );
        } finally {
            setSaving(false);
        }
    };

    // Admin or Teacher: view students in a course
    const handleViewStudents = async (course) => {
        if (studentsLoading) return;

        setSelectedCourse(course);
        setStudents([]);
        setStudentsError('');
        setStudentsLoading(true);

        try {
            const response = await api.get(
                `courses/${course.id}/students/`
            );

            const data = response.data;

            setStudents(
                Array.isArray(data)
                    ? data
                    : data.students ?? data.results ?? []
            );
        } catch (err) {
            setStudentsError(
                getErrorMessage(
                    err,
                    'Failed to load students for this course.'
                )
            );
        } finally {
            setStudentsLoading(false);
        }
    };

    const handleCloseStudents = () => {
        setSelectedCourse(null);
        setStudents([]);
        setStudentsError('');
    };

    // Admin only: open teacher assignment panel
    const handleManageTeachers = async (course) => {
        if (!isAdmin || assignmentsLoading) return;

        setAssignmentCourse(course);
        setSelectedTeacher('');
        setAssignmentError('');
        setAssignmentMessage('');
        setAssignments([]);
        setTeachers([]);
        setAssignmentsLoading(true);

        try {
            const [usersResponse, assignmentsResponse] =
                await Promise.all([
                    api.get('admin/users/'),
                    api.get('admin/teacher-course-assignments/')
                ]);

            const users = getList(usersResponse.data);

            const teacherUsers = users.filter(user => {
                const userRole = String(
                    user.role || ''
                ).trim().toLowerCase();

                const groups = Array.isArray(user.groups)
                    ? user.groups.map(group =>
                        typeof group === 'string'
                            ? group.toLowerCase()
                            : String(group.name || '').toLowerCase()
                    )
                    : [];

                return (
                    (
                        userRole === 'teacher' ||
                        groups.includes('teacher')
                    ) &&
                    user.is_active !== false
                );
            });

            setTeachers(teacherUsers);
            setAssignments(getList(assignmentsResponse.data));
        } catch (err) {
            setAssignmentError(
                getErrorMessage(
                    err,
                    'Could not load teachers or assignments.'
                )
            );
        } finally {
            setAssignmentsLoading(false);
        }
    };

    // Admin only: assign a teacher
    const handleAssignTeacher = async (event) => {
        event.preventDefault();

        if (!isAdmin || !assignmentCourse || !selectedTeacher) {
            setAssignmentError('Please select a teacher.');
            return;
        }

        const alreadyAssigned = assignments.some(
            assignment =>
                Number(assignment.course) ===
                    Number(assignmentCourse.id) &&
                Number(assignment.teacher) ===
                    Number(selectedTeacher)
        );

        if (alreadyAssigned) {
            setAssignmentError(
                'This teacher is already assigned to this course.'
            );
            return;
        }

        setAssignmentSaving(true);
        setAssignmentError('');
        setAssignmentMessage('');

        try {
            const response = await api.post(
                'admin/teacher-course-assignments/',
                {
                    teacher: Number(selectedTeacher),
                    course: assignmentCourse.id
                }
            );

            // Both 200 and 201 indicate a successful response.
            if (
                response.status === 200 ||
                response.status === 201
            ) {
                setAssignments(previous => [
                    ...previous,
                    response.data
                ]);

                setAssignmentMessage(
                    'Teacher assigned successfully.'
                );

                setSelectedTeacher('');
            }
        } catch (err) {
            setAssignmentError(
                getErrorMessage(
                    err,
                    'Failed to assign teacher. Please try again.'
                )
            );
        } finally {
            setAssignmentSaving(false);
        }
    };

    const handleCloseAssignments = () => {
        setAssignmentCourse(null);
        setTeachers([]);
        setAssignments([]);
        setSelectedTeacher('');
        setAssignmentError('');
        setAssignmentMessage('');
    };

    const handleEditCourse = (course) => {
        if (!isAdmin || saving) return;

        setEditingCourse(course);
        setCourseName(course.name);
        setMessage('');
    };

    const handleCancelEdit = () => {
        if (saving) return;

        setEditingCourse(null);
        setCourseName('');
        setMessage('');
    };

    const courseAssignments = assignments.filter(
        assignment =>
            Number(assignment.course) ===
            Number(assignmentCourse?.id)
    );

    if (!isAdmin && !isTeacher) {
        return (
            <div className="courses-page">
                <p role="alert">
                    You do not have permission to view courses.
                </p>
            </div>
        );
    }

    if (loading) {
        return <p>Loading courses...</p>;
    }

    if (error) {
        return (
            <div className="courses-page">
                <p role="alert">{error}</p>

                <button
                    type="button"
                    onClick={fetchCourses}
                    disabled={loading}
                >
                    Retry
                </button>
            </div>
        );
    }

    return (
        <div className="courses-page">
            <h1>
                {isAdmin
                    ? 'Course Management'
                    : 'My Assigned Courses'}
            </h1>

            <p>
                {isAdmin
                    ? 'View and manage courses in the institution.'
                    : 'View your assigned courses and their enrolled students.'}
            </p>

            {/* Admin-only add/edit form */}
            {isAdmin && (
                <>
                    <form onSubmit={handleAddCourse}>
                        <label htmlFor="courseName">
                            Course Name
                        </label>

                        <input
                            id="courseName"
                            type="text"
                            value={courseName}
                            onChange={event =>
                                setCourseName(event.target.value)
                            }
                            placeholder="Enter course name"
                            required
                            disabled={saving}
                        />

                        <button
                            type="submit"
                            disabled={saving}
                        >
                            {saving
                                ? 'Saving...'
                                : editingCourse
                                    ? 'Update Course'
                                    : 'Add Course'}
                        </button>

                        {editingCourse && (
                            <button
                                type="button"
                                onClick={handleCancelEdit}
                                disabled={saving}
                            >
                                Cancel Edit
                            </button>
                        )}
                    </form>

                    {message && (
                        <p role="status">{message}</p>
                    )}
                </>
            )}

            {/* Courses table */}
            {courses.length === 0 ? (
                <p>
                    {isTeacher
                        ? 'No courses have been assigned to you yet.'
                        : 'No courses found.'}
                </p>
            ) : (
                <div className="courses-table-wrapper">
                    <table className="courses-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Course Name</th>
                                <th>Number of Students</th>
                                <th>Actions</th>
                            </tr>
                        </thead>

                        <tbody>
                            {courses.map(course => (
                                <tr key={course.id}>
                                    <td className="course-id">
                                        {course.id}
                                    </td>

                                    <td className="course-name">
                                        {course.name}
                                    </td>

                                    <td className="course-student-count">
                                        {course.student_count ??
                                            course.student?.length ??
                                            0}
                                    </td>

                                    <td>
                                        <div className="course-action-buttons">
                                            {isAdmin && (
                                                <button
                                                    type="button"
                                                    className="course-edit-btn"
                                                    onClick={() =>
                                                        handleEditCourse(course)
                                                    }
                                                    disabled={saving}
                                                >
                                                    Edit
                                                </button>
                                            )}

                                            <button
                                                type="button"
                                                className="course-view-btn"
                                                onClick={() =>
                                                    handleViewStudents(course)
                                                }
                                                disabled={studentsLoading}
                                            >
                                                {studentsLoading &&
                                                selectedCourse?.id === course.id
                                                    ? 'Loading...'
                                                    : 'View Students'}
                                            </button>

                                            {isAdmin && (
                                                <button
                                                    type="button"
                                                    className="course-teacher-btn"
                                                    onClick={() =>
                                                        handleManageTeachers(course)
                                                    }
                                                    disabled={assignmentsLoading}
                                                >
                                                    Manage Teachers
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Students panel */}
            {selectedCourse && (
                <section>
                    <h2>
                        Students in {selectedCourse.name}
                    </h2>

                    <button
                        type="button"
                        onClick={handleCloseStudents}
                        disabled={studentsLoading}
                    >
                        Close Students
                    </button>

                    {studentsLoading && (
                        <p>Loading students...</p>
                    )}

                    {studentsError && (
                        <p role="alert">{studentsError}</p>
                    )}

                    {!studentsLoading &&
                        !studentsError &&
                        students.length === 0 && (
                            <p>
                                No students enrolled in this course.
                            </p>
                        )}

                    {!studentsLoading &&
                        !studentsError &&
                        students.length > 0 && (
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>Age</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {students.map(student => (
                                        <tr key={student.id}>
                                            <td>{student.id}</td>
                                            <td>{student.Name}</td>
                                            <td>{student.Email}</td>
                                            <td>{student.Age}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                </section>
            )}

            {/* Admin-only teacher assignment panel */}
            {isAdmin && assignmentCourse && (
                <section>
                    <h2>
                        Manage Teachers — {assignmentCourse.name}
                    </h2>

                    <button
                        type="button"
                        onClick={handleCloseAssignments}
                        disabled={assignmentsLoading || assignmentSaving}
                    >
                        Close Teacher Assignment
                    </button>

                    {assignmentsLoading && (
                        <p>Loading teachers and assignments...</p>
                    )}

                    {assignmentError && (
                        <p role="alert">{assignmentError}</p>
                    )}

                    {!assignmentsLoading && (
                        <>
                            <h3>Assign a Teacher</h3>

                            {teachers.length === 0 ? (
                                <p>
                                    No active Teacher accounts were found.
                                    Create a Teacher account in User Management first.
                                </p>
                            ) : (
                                <form onSubmit={handleAssignTeacher}>
                                    <label htmlFor="teacherSelect">
                                        Select Teacher
                                    </label>

                                    <select
                                        id="teacherSelect"
                                        value={selectedTeacher}
                                        onChange={event =>
                                            setSelectedTeacher(
                                                event.target.value
                                            )
                                        }
                                        required
                                        disabled={assignmentSaving}
                                    >
                                        <option value="">
                                            Choose a teacher
                                        </option>

                                        {teachers.map(teacher => (
                                            <option
                                                key={teacher.id}
                                                value={teacher.id}
                                            >
                                                {teacher.username}
                                                {teacher.email
                                                    ? ` (${teacher.email})`
                                                    : ''}
                                            </option>
                                        ))}
                                    </select>

                                    <button
                                        type="submit"
                                        disabled={
                                            assignmentSaving ||
                                            !selectedTeacher
                                        }
                                    >
                                        {assignmentSaving
                                            ? 'Assigning...'
                                            : 'Assign Teacher'}
                                    </button>
                                </form>
                            )}

                            {assignmentMessage && (
                                <p role="status">
                                    {assignmentMessage}
                                </p>
                            )}

                            <h3>Assigned Teachers</h3>

                            {courseAssignments.length === 0 ? (
                                <p>
                                    No teachers assigned to this course yet.
                                </p>
                            ) : (
                                <ul>
                                    {courseAssignments.map(assignment => (
                                        <li key={assignment.id}>
                                            {assignment.teacher_name ||
                                                teachers.find(
                                                    teacher =>
                                                        Number(teacher.id) ===
                                                        Number(assignment.teacher)
                                                )?.username ||
                                                `Teacher ID ${assignment.teacher}`}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </>
                    )}
                </section>
            )}
        </div>
    );
}

export default Courses;
