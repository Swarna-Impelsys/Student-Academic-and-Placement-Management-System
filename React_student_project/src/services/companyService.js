
import api from './api';

export const getCompanies = async () => {
    const response = await api.get('companies/');
    return response.data;
};

export const createCompany = async (formData) => {
    const response = await api.post('companies/', formData);
    return response.data;
};

export const updateCompany = async (id, formData) => {
    const response = await api.patch(`companies/${id}/`, formData);
    return response.data;
};

export const deleteCompany = async (id) => {
    const response = await api.delete(`companies/${id}/`);
    return response.data;
};
