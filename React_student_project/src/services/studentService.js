
import api from './api';


export async function getStudents(query = '') {
    const response = await api.get(`students/${query}`);
    return response.data;
}


export async function getStudentById(studentId) {
    const response = await api.get(`students/${studentId}/`);
    return response.data;
}

export async function createStudent(studentData) {
    const response = await api.post('students/', studentData);
    return response.data;
}

export async function updateStudent(studentId, studentData) {
    const response = await api.patch(
        `students/${studentId}/`,
        studentData
    );
    return response.data;
}

export async function getCourses() {
    const response = await api.get('students/courses/');
    return response.data;
}

export async function getSubjects() {
    const response = await api.get('students/subjects/');
    return response.data;
}

export async function getSkills() {
    const response = await api.get('skills/');
    return response.data;
}

export async function deleteStudent(studentId) {
    const response = await api.delete(`students/${studentId}/`);
    return response.data;
}


export async function getAcademicRecords() {
    const response = await api.get('academic-records/');
    return response.data;
}

export async function createAcademicRecord(payload) {
    const response = await api.post('academic-records/', payload);
    return response.data;
}

export async function getAcademicRecordById(id) {
    const response = await api.get(`academic-records/${id}/`);
    return response.data;
}

export async function updateAcademicRecord(id, payload) {
    const response = await api.patch(`academic-records/${id}/`, payload);
    return response.data;
}

export async function deleteAcademicRecord(id) {
    const response = await api.delete(`academic-records/${id}/`);
    return response.data;
}
// ================= SKILLS =================
export async function createSkill(payload) {
    const response = await api.post('skills/', payload);
    return response.data;
}

export async function updateSkill(id, payload) {
    const response = await api.patch(`skills/${id}/`, payload);
    return response.data;
}

export async function deleteSkill(id) {
    const response = await api.delete(`skills/${id}/`);
    return response.data;
}

// ================= CERTIFICATIONS =================

export async function getCertifications() {
    const response = await api.get('certifications/');
    return response.data;
}

export async function createCertification(payload) {
    const response = await api.post('certifications/', payload);
    return response.data;
}

export async function updateCertification(id, payload) {
    const response = await api.patch(`certifications/${id}/`, payload);
    return response.data;
}

export async function deleteCertification(id) {
    const response = await api.delete(`certifications/${id}/`);
    return response.data;
}


 // ================= STUDENT PERSONAL SKILLS =================

export async function getMySkills() {
    const response = await api.get('my-skills/');
    return response.data;
}

export async function createMySkill(payload) {
    const response = await api.post('my-skills/', payload);
    return response.data;
}

export async function updateMySkill(id, payload) {
    const response = await api.patch(`my-skills/${id}/`, payload);
    return response.data;
}

export async function deleteMySkill(id) {
    const response = await api.delete(`my-skills/${id}/`);
    return response.data;
}

