
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8001/api';

export async function loginUser(username, password) {
    const response = await axios.post(
        `${API_BASE_URL}/login/`,
        {
            username: username,
            password: password
        }
    );

    return response.data;
}
