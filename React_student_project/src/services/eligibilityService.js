import api from './api';

export const checkEligibility = async (studentId, jobId) => {
    const response = await api.post('eligibility/check/', {
        student: Number(studentId),
        job: Number(jobId),
    });

    return response.data;
};

export const getEligibilityChecks = async (params = {}) => {
    const response = await api.get('eligibility/', { params });

    return response.data;
};