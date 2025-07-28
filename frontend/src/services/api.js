// src/services/api.js - Updated with improved token handling and persistence
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Token management utilities
const TokenManager = {
  getToken: () => localStorage.getItem('access_token'),
  
  setToken: (token) => {
    localStorage.setItem('access_token', token);
    // Update default header for future requests
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  },
  
  removeToken: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('token_expires_at');
    delete api.defaults.headers.common['Authorization'];
  },
  
  isTokenExpired: () => {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;
    return Date.now() > parseInt(expiresAt);
  }
};

// Set initial token if available
const initialToken = TokenManager.getToken();
if (initialToken && !TokenManager.isTokenExpired()) {
  api.defaults.headers.common['Authorization'] = `Bearer ${initialToken}`;
}

// Request interceptor - Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = TokenManager.getToken();
    
    if (token && !TokenManager.isTokenExpired()) {
      config.headers.Authorization = `Bearer ${token}`;
    } else if (token && TokenManager.isTokenExpired()) {
      // Token is expired, remove it
      console.log('Token expired during request, removing');
      TokenManager.removeToken();
      
      // If this is not a login/register request, redirect to login
      if (!config.url.includes('/auth/')) {
        window.location.href = '/login';
        return Promise.reject(new Error('Token expired'));
      }
    }
    
    // Add request timestamp for debugging
    config.metadata = { startTime: new Date() };
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - Handle token expiration and errors
api.interceptors.response.use(
  (response) => {
    // Log response time for debugging
    if (response.config.metadata) {
      const endTime = new Date();
      const duration = endTime - response.config.metadata.startTime;
      console.log(`API ${response.config.method.toUpperCase()} ${response.config.url}: ${duration}ms`);
    }
    
    return response;
  },
  (error) => {
    const originalRequest = error.config;
    
    // Handle different error scenarios
    if (error.response) {
      const { status, data } = error.response;
      
      console.error(`API Error ${status}:`, {
        url: originalRequest.url,
        method: originalRequest.method,
        message: data?.detail || error.message
      });
      
      // Handle authentication errors
      if (status === 401 || status === 403) {
        console.log('Authentication error, clearing tokens');
        TokenManager.removeToken();
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          // Small delay to prevent immediate redirect during app initialization
          setTimeout(() => {
            window.location.href = '/login';
          }, 100);
        }
      }
      
      // Handle server errors
      if (status >= 500) {
        console.error('Server error, please try again later');
        // Could show a toast notification here
      }
      
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message);
      // Could show network error notification
    } else {
      console.error('Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Enhanced API functions with better error handling
export const authAPI = {
  register: async (data) => {
    try {
      const response = await api.post('/auth/register', data);
      console.log('Registration successful');
      return response.data;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  },
  
  login: async (data) => {
    try {
      const response = await api.post('/auth/login', data);
      console.log('Login successful');
      
      // Store token and set expiration
      if (response.data.access_token) {
        TokenManager.setToken(response.data.access_token);
        const expiresAt = Date.now() + (30 * 60 * 1000); // 30 minutes
        localStorage.setItem('token_expires_at', expiresAt.toString());
      }
      
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  },
  
  googleAuth: async (token) => {
    try {
      const response = await api.post('/auth/google', { token });
      console.log('Google auth successful');
      
      // Store token and set expiration
      if (response.data.access_token) {
        TokenManager.setToken(response.data.access_token);
        const expiresAt = Date.now() + (30 * 60 * 1000); // 30 minutes
        localStorage.setItem('token_expires_at', expiresAt.toString());
      }
      
      return response.data;
    } catch (error) {
      console.error('Google auth failed:', error);
      throw error;
    }
  },
  
  verifyToken: async () => {
    try {
      const response = await api.post('/auth/verify-token');
      console.log('Token verification successful');
      return response.data;
    } catch (error) {
      console.error('Token verification failed:', error);
      throw error;
    }
  },
};

export const userAPI = {
  getProfile: async () => {
    try {
      const response = await api.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('Failed to get profile:', error);
      throw error;
    }
  },
  
  updateProfile: async (data) => {
    try {
      const response = await api.put('/users/me', data);
      console.log('Profile updated successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  },
  
  deactivateAccount: async () => {
    try {
      const response = await api.delete('/users/me');
      console.log('Account deactivated');
      return response.data;
    } catch (error) {
      console.error('Failed to deactivate account:', error);
      throw error;
    }
  },
};

// Chat API functions with retry logic
export const chatAPI = {
  sendMessage: async (message, retries = 3) => {
    try {
      const response = await api.post('/chat/send', { message });
      return response.data;
    } catch (error) {
      if (retries > 0 && error.response?.status >= 500) {
        console.log(`Retrying chat message, ${retries} attempts left`);
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
        return chatAPI.sendMessage(message, retries - 1);
      }
      console.error('Failed to send chat message:', error);
      throw error;
    }
  },
  
  getChatHistory: async (limit = 50) => {
    try {
      const response = await api.get(`/chat/history?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get chat history:', error);
      throw error;
    }
  },
  
  getUserStats: async () => {
    try {
      const response = await api.get('/chat/stats');
      return response.data;
    } catch (error) {
      console.error('Failed to get user stats:', error);
      throw error;
    }
  },
  
  updateUserStats: async (stats) => {
    try {
      const response = await api.post('/chat/stats/update', stats);
      return response.data;
    } catch (error) {
      console.error('Failed to update user stats:', error);
      throw error;
    }
  },
  
  createGoal: async (goalData) => {
    try {
      const response = await api.post('/chat/goals', goalData);
      console.log('Goal created successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to create goal:', error);
      throw error;
    }
  },
  
  updateGoal: async (goalId, updateData) => {
    try {
      const response = await api.put(`/chat/goals/${goalId}`, updateData);
      console.log('Goal updated successfully');
      return response.data;
    } catch (error) {
      console.error('Failed to update goal:', error);
      throw error;
    }
  },
  
  getCoachingSuggestions: async () => {
    try {
      const response = await api.post('/chat/coach/suggest');
      return response.data;
    } catch (error) {
      console.error('Failed to get coaching suggestions:', error);
      throw error;
    }
  },
};

// Utility function to check API health
export const healthAPI = {
  checkHealth: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },
  
  checkMCPStatus: async () => {
    try {
      const response = await api.get('/mcp/status');
      return response.data;
    } catch (error) {
      console.error('MCP status check failed:', error);
      throw error;
    }
  },
};

// Export token manager for direct use if needed
export { TokenManager };