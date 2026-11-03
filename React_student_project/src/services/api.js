
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8001/api/',
});

// Separate instance for refreshing tokens.
// This prevents the refresh request from triggering this interceptor.
const refreshApi = axios.create({
    baseURL: 'http://127.0.0.1:8001/api/',
});

// Attach access token to API requests.
api.interceptors.request.use(
    (config) => {
        const accessToken = localStorage.getItem('accessToken');

        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// Track refresh requests to avoid refreshing multiple times simultaneously.
let isRefreshing = false;
let refreshSubscribers = [];

const subscribeTokenRefresh = (callback) => {
    refreshSubscribers.push(callback);
};

const notifySubscribers = (newAccessToken) => {
    refreshSubscribers.forEach((callback) => callback(newAccessToken));
    refreshSubscribers = [];
};

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (
            error.response?.status !== 401 ||
            !originalRequest ||
            originalRequest._retry ||
            originalRequest.url?.includes('token/refresh/') ||
            originalRequest.url?.includes('login/')
        ) {
            return Promise.reject(error);
        }

        const refreshToken = localStorage.getItem('refreshToken');

        // No refresh token: the user must log in again.
        if (!refreshToken) {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');

            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }

            return Promise.reject(error);
        }

        // If another request is already refreshing, wait for it.
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                subscribeTokenRefresh((newAccessToken) => {
                    if (!newAccessToken) {
                        reject(error);
                        return;
                    }

                    originalRequest.headers =
                        originalRequest.headers || {};

                    originalRequest.headers.Authorization =
                        `Bearer ${newAccessToken}`;

                    resolve(api(originalRequest));
                });
            });
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const response = await refreshApi.post(
                'token/refresh/',
                { refresh: refreshToken }
            );

            const newAccessToken = response.data.access;

            if (!newAccessToken) {
                throw new Error('No access token returned.');
            }

            localStorage.setItem('accessToken', newAccessToken);

            // Retry requests that were waiting for the refresh.
            notifySubscribers(newAccessToken);

            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization =
                `Bearer ${newAccessToken}`;

            return await api(originalRequest);
        } catch (refreshError) {
            // Reject all requests waiting for the token refresh.
            notifySubscribers(null);

            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('role');

            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }

            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);

export default api;
