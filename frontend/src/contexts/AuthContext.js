// src/contexts/AuthContext.js - Improved with better persistent login
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authAPI, userAPI } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  const isAuthenticated = !!user;

  // Clear auth data from storage and state
  const clearAuth = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('token_expires_at');
    setUser(null);
  }, []);

  // Set auth data in storage and state
  const setAuth = useCallback((tokenData) => {
    localStorage.setItem('access_token', tokenData.access_token);
    localStorage.setItem('user', JSON.stringify(tokenData.user));
    
    // Calculate and store token expiration time
    const expiresAt = Date.now() + (30 * 60 * 1000); // 30 minutes from now
    localStorage.setItem('token_expires_at', expiresAt.toString());
    
    setUser(tokenData.user);
  }, []);

  // Check if token is expired
  const isTokenExpired = useCallback(() => {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;
    
    return Date.now() > parseInt(expiresAt);
  }, []);

  // Refresh user data from server
  const refreshUser = useCallback(async () => {
    try {
      const userData = await userAPI.getProfile();
      const updatedUser = { ...user, ...userData };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      return updatedUser;
    } catch (error) {
      console.error('Failed to refresh user data:', error);
      // Don't clear auth on profile fetch failure
      return user;
    }
  }, [user]);

  // Check authentication status on app initialization
  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      
      if (!token || !savedUser) {
        console.log('No token or user data found');
        return false;
      }

      // Check if token is expired (client-side check)
      if (isTokenExpired()) {
        console.log('Token expired (client-side check)');
        clearAuth();
        return false;
      }

      try {
        // Verify token with server
        await authAPI.verifyToken();
        
        // Parse and set user data
        const userData = JSON.parse(savedUser);
        setUser(userData);
        
        console.log('Authentication restored successfully');
        return true;
      } catch (error) {
        console.log('Token verification failed:', error.response?.status);
        
        // If token is invalid (401/403), clear auth data
        if (error.response?.status === 401 || error.response?.status === 403) {
          clearAuth();
          return false;
        }
        
        // For other errors (network issues), keep user logged in but show warning
        const userData = JSON.parse(savedUser);
        setUser(userData);
        console.warn('Token verification failed due to network issues, keeping user logged in');
        return true;
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      clearAuth();
      return false;
    }
  }, [clearAuth, isTokenExpired]);

  // Initialize authentication on app start
  useEffect(() => {
    let isMounted = true;

    const initializeAuth = async () => {
      console.log('Initializing authentication...');
      
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth initialization failed:', error);
      } finally {
        if (isMounted) {
          setIsLoading(false);
          setIsInitialized(true);
          console.log('Authentication initialization complete');
        }
      }
    };

    initializeAuth();

    return () => {
      isMounted = false;
    };
  }, [checkAuth]);

  // Set up token refresh interval
  useEffect(() => {
    if (!isAuthenticated) return;

    const checkTokenExpiry = () => {
      if (isTokenExpired()) {
        console.log('Token expired, logging out');
        logout();
      }
    };

    // Check token expiry every minute
    const interval = setInterval(checkTokenExpiry, 60000);

    return () => clearInterval(interval);
  }, [isAuthenticated, isTokenExpired]);

  // Set up visibility change listener to check auth when tab becomes visible
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('Tab became visible, checking auth status');
        checkAuth();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, checkAuth]);

  const login = async (email, password) => {
    try {
      setIsLoading(true);
      const response = await authAPI.login({ email, password });
      setAuth(response);
      console.log('Login successful');
    } catch (error) {
      console.error('Login failed:', error);
      throw new Error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data) => {
    try {
      setIsLoading(true);
      const response = await authAPI.register(data);
      setAuth(response);
      console.log('Registration successful');
    } catch (error) {
      console.error('Registration failed:', error);
      throw new Error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const googleLogin = async (token) => {
    try {
      setIsLoading(true);
      const response = await authAPI.googleAuth(token);
      setAuth(response);
      console.log('Google login successful');
    } catch (error) {
      console.error('Google login failed:', error);
      throw new Error(error.response?.data?.detail || 'Google login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = useCallback(() => {
    console.log('Logging out');
    clearAuth();
    
    // Redirect to login page
    window.location.href = '/login';
  }, [clearAuth]);

  const updateUser = async (data) => {
    try {
      const updatedUser = await userAPI.updateProfile(data);
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      console.log('User profile updated');
      return updatedUser;
    } catch (error) {
      console.error('Profile update failed:', error);
      throw new Error(error.response?.data?.detail || 'Update failed');
    }
  };

  const value = {
    user,
    isLoading,
    isAuthenticated,
    isInitialized, // New: indicates if auth check is complete
    login,
    register,
    googleLogin,
    logout,
    updateUser,
    refreshUser,
    checkAuth, // Expose for manual auth checks
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};