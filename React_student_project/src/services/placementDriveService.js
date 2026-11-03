
import api from './api';

export const getPlacementDrives = async () => {
    const response = await api.get('placement-drives/');
    return response.data;
};

export const createPlacementDrive = async (data) => {
    const response = await api.post('placement-drives/', data);
    return response.data;
};

export const updatePlacementDrive = async (id, data) => {
    const response = await api.patch(`placement-drives/${id}/`, data);
    return response.data;
};

export const deletePlacementDrive = async (id) => {
    const response = await api.delete(`placement-drives/${id}/`);
    return response.data;
};
