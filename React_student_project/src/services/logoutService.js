
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8001/api';

export async function logoutUser(refreshToken) {
    const accessToken = localStorage.getItem('accessToken');

    try {
        if (refreshToken && accessToken) {
            await axios.post(
                `${API_BASE_URL}/logout/`,
                { refresh: refreshToken },
                {
                    headers: {
                        Authorization: `Bearer ${accessToken}`,
                    },
                }
            );
        }
    } finally {
        // Clear tokens even if the API request fails
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
         localStorage.removeItem('role');
    }
}
