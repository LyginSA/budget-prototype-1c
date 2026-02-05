import axios from 'axios';

// Базовый URL API (Render) или локально
const API_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
    baseURL: API_URL,
});

export default api;
