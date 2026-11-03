
import { useState } from 'react';

function AddStudentForm() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [course, setCourse] = useState('');

    function handleSubmit(event) {
        event.preventDefault();

        const student = {
            name: name,
            email: email,
            course: course
        };

        console.log('Student details:', student);
        alert(`Student ${name} entered successfully!`);

        setName('');
        setEmail('');
        setCourse('');
    }

    return (
        <section>
            <h2>Add Student</h2>

            <form onSubmit={handleSubmit}>
                <label htmlFor="name">Student Name</label>
                <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    required
                />

                <label htmlFor="email">Email</label>
                <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                />

                <label htmlFor="course">Course</label>
                <select
                    id="course"
                    value={course}
                    onChange={(event) => setCourse(event.target.value)}
                    required
                >
                    <option value="">Select a course</option>
                    <option value="Data Science">Data Science</option>
                    <option value="Python">Python</option>
                    <option value="Django">Django</option>
                    <option value="React">React</option>
                </select>

                <button type="submit">Add Student</button>
            </form>
        </section>
    );
}

export default AddStudentForm;
