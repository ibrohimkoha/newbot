// src/api.ts

import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

// Tokenni har bir so‘rovga dinamik qo‘shamiz
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token'); // yoki contextdan ol
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.request.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
)

export default api;
