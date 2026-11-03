
import api from './api';

// Get all jobs
export const getJobs = async () => {
    const response = await api.get('jobs/');
    return response.data;
};

// Create a new job
export const createJob = async (data) => {
    const response = await api.post('jobs/', data);
    return response.data;
};

// Update an existing job
export const updateJob = async (id, data) => {
    const response = await api.patch(`jobs/${id}/`, data);
    return response.data;
};

// Delete a job
export const deleteJob = async (id) => {
    const response = await api.delete(`jobs/${id}/`);
    return response.data;
};

// Get eligible students who have not applied for a job
export const getEligibleStudents = async (jobId) => {
    const response = await api.get('eligible-students/', {
        params: {
            job: Number(jobId),
        },
    });

    return response.data;
};

// Get applications submitted for a specific job
export const getApplicationsByJob = async (jobId) => {
    const response = await api.get('applications/', {
        params: {
            job: Number(jobId),
        },
    });

    return response.data;
};

// Send job details to eligible students who have not applied
export const sendEligibleJobNotification = async (jobId, studentIds) => {
    const response = await api.post(
        'notifications/send-eligible-job/',
        {
            job: Number(jobId),
            student_ids: studentIds.map(Number),
        }
    );

    return response.data;
};
