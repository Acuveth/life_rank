// src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  register: (data) =>
    api.post('/auth/register', data).then(res => res.data),
  
  login: (data) =>
    api.post('/auth/login', data).then(res => res.data),
  
  googleAuth: (token) =>
    api.post('/auth/google', { token }).then(res => res.data),
  
  verifyToken: () =>
    api.post('/auth/verify-token').then(res => res.data),
};

export const userAPI = {
  getProfile: () =>
    api.get('/users/me').then(res => res.data),
  
  updateProfile: (data) =>
    api.put('/users/me', data).then(res => res.data),
  
  deactivateAccount: () =>
    api.delete('/users/me').then(res => res.data),
};

