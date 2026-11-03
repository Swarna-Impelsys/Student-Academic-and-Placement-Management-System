
function StudentList() {
    const students = [
        { id: 1, name: 'Swarna', course: 'Data Science' },
        { id: 2, name: 'Rahul', course: 'Python' },
        { id: 3, name: 'Anu', course: 'Django' },
        { id: 4, name: 'Priya', course: 'React' }
    ];

    return (
        <section>
            <h2>Student List</h2>

            <div className="student-list">
                {students.map((student) => (
                    <div className="dashboard-card" key={student.id}>
                        <h3>{student.name}</h3>
                        <p>Course: {student.course}</p>
                    </div>
                ))}
            </div>
        </section>
    );
}

export default StudentList;
