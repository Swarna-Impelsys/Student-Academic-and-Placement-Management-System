import { useState, useCallback } from 'react';

function getApiErrorMessage(error) {
    const data = error.response?.data;

    if (typeof data?.detail === 'string') {
        return data.detail;
    }

    if (typeof data?.error === 'string') {
        return data.error;
    }

    if (data && typeof data === 'object') {
        const firstValue = Object.values(data)[0];

        if (Array.isArray(firstValue) && firstValue.length > 0) {
            return String(firstValue[0]);
        }

        if (typeof firstValue === 'string') {
            return firstValue;
        }
    }

    if (error.code === 'ERR_NETWORK') {
        return 'Cannot connect to the server. Check whether Django is running.';
    }

    return error.message || 'Something went wrong. Please try again.';
}

export default function useApi() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const execute = useCallback(async (apiFunction) => {
        setLoading(true);
        setError('');

        try {
            return await apiFunction();
        } catch (err) {
            const message = getApiErrorMessage(err);
            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        setError,
        execute,
    };
}