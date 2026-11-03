
import api from './api';

// Get all notifications
export const getNotifications = async () => {
    const response = await api.get('notifications/');
    return response.data;
};

// Get unread notifications
export const getUnreadNotifications = async () => {
    const response = await api.get('notifications/', {
        params: {
            is_read: false,
        },
    });

    return response.data;
};

// Mark a notification as read
export const markNotificationAsRead = async (id) => {
    const response = await api.patch(`notifications/${id}/read/`);
    return response.data;
};
