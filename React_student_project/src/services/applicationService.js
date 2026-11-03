
import api from './api';

// Get applications visible to the logged-in user.
export const getApplications = async () => {
    const response = await api.get('applications/');
    return response.data;
};

// Apply for a job.
//
// Admin/Teacher: Provide studentId and jobId.
// Student: Provide null (or an empty value) for studentId.
// The backend must automatically assign the logged-in Student's record.
export const createApplication = async (studentId, jobId) => {
    const numericJobId = Number(jobId);

    if (!jobId || !Number.isInteger(numericJobId) || numericJobId <= 0) {
        throw new Error('Please provide a valid job ID.');
    }

    const payload = {
        job: numericJobId,
    };

    // Include student ID only when one is provided.
    if (
        studentId !== null &&
        studentId !== undefined &&
        studentId !== ''
    ) {
        const numericStudentId = Number(studentId);

        if (
            !Number.isInteger(numericStudentId) ||
            numericStudentId <= 0
        ) {
            throw new Error('Please provide a valid student ID.');
        }

        payload.student = numericStudentId;
    }

    const response = await api.post('applications/', payload);
    return response.data;
};

// Update an application's status.
export const updateApplicationStatus = async (applicationId, status) => {
    const response = await api.patch(
        `applications/${applicationId}/`,
        { status }
    );

    return response.data;
};
