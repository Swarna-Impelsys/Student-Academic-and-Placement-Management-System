
import api from './api';

export const getInterviews = async () => {
    const response = await api.get('interviews/');
    return response.data;
};

export const createInterview = async (interviewData) => {
    const response = await api.post('interviews/', interviewData);
    return response.data;
};

export const updateInterview = async (id, interviewData) => {
    const response = await api.patch(
        `interviews/${id}/`,
        interviewData
    );
    return response.data;
};

export const deleteInterview = async (id) => {
    const response = await api.delete(`interviews/${id}/`);
    return response.data;
};

// Admin uploads the interview shortlist Excel file.
export const uploadInterviewShortlist = async (formData) => {
    const response = await api.post(
        'interviews/upload-shortlist/',
        formData
    );
    return response.data;
};

// Registration Officer extracts the uploaded Excel file.
export const extractInterviewShortlist = async (uploadId) => {
    const response = await api.post(
        `interviews/shortlist/${uploadId}/extract/`
    );
    return response.data;
};

// Registration Officer sends notifications to selected students.
export const sendInterviewNotifications = async (uploadId, interviewIds) => {
    const response = await api.post(
        `interviews/shortlist/${uploadId}/send-notifications/`,
        {
            interview_ids: interviewIds,
        }
    );
    return response.data;
};

// Load uploaded interview shortlist files.
export const getInterviewShortlistUploads = async () => {
    const response = await api.get('interviews/upload-shortlist/');
    return response.data;
};
