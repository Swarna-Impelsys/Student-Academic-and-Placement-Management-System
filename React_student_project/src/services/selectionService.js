
import api from './api';

export const getSelections = async () => {
    const response = await api.get('selections/');
    return response.data;
};

export const createSelection = async (selectionData) => {
    const response = await api.post('selections/', selectionData);
    return response.data;
};

export const updateSelection = async (id, selectionData) => {
    const response = await api.patch(`selections/${id}/`, selectionData);
    return response.data;
};

export const deleteSelection = async (id) => {
    const response = await api.delete(`selections/${id}/`);
    return response.data;
};

export const uploadSelectionResults = async (
    file,
    jobId,
    confirmCompleteFinalList
) => {
    const formData = new FormData();

    formData.append('file', file);
    formData.append('job_id', jobId);
    formData.append(
        'confirm_complete_final_list',
        confirmCompleteFinalList
    );

    const response = await api.post(
        'selections/upload-results/',
        formData
    );

    return response.data;
};
