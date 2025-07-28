// src/App.js - Updated with improved loading states and routing
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AuthPage, ProfilePage } from './pages';
import StatsDashboard from './components/StatsDashboard';
import Dashboard from './components/Dashboard';
import './index.css';

// Loading Component
const LoadingScreen = ({ message = "Loading..." }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
      <p className="mt-4 text-lg text-gray-600">{message}</p>
      <p className="mt-2 text-sm text-gray-400">Please wait while we verify your session...</p>
    </div>
  </div>
);

// Protected Route Component - Only redirects after auth check is complete
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  // Show loading while auth is being checked
  if (isLoading || !isInitialized) {
    return <LoadingScreen message="Verifying your session..." />;
  }

  // Only redirect after we're sure user is not authenticated
  if (!isAuthenticated) {
    console.log('User not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  console.log('User authenticated, rendering protected content');
  return children;
};

// Public Route Component - Only redirects after auth check is complete
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  // Show loading while auth is being checked
  if (isLoading || !isInitialized) {
    return <LoadingScreen message="Checking your session..." />;
  }

  // Only redirect if user is actually authenticated
  if (isAuthenticated) {
    console.log('User already authenticated, redirecting to dashboard');
    return <Navigate to="/stats" replace />;
  }

  console.log('User not authenticated, showing public route');
  return children;
};

// Route component that handles initial redirect logic
const InitialRoute = () => {
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  if (isLoading || !isInitialized) {
    return <LoadingScreen message="Starting application..." />;
  }

  // Redirect based on auth status
  if (isAuthenticated) {
    return <Navigate to="/stats" replace />;
  } else {
    return <Navigate to="/login" replace />;
  }
};

const AppRoutes = () => {
  return (
    <Routes>
      {/* Initial route - redirects based on auth status */}
      <Route path="/" element={<InitialRoute />} />

      {/* Public Routes - accessible only when not authenticated */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />

      {/* Protected Routes - require authentication */}
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/stats"
        element={
          <ProtectedRoute>
            <StatsDashboard />
          </ProtectedRoute>
        }
      />

      {/* Catch all - redirect to home which will handle auth redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

// Error Boundary for better error handling
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Something went wrong</h2>
            <p className="text-gray-600 mb-4">Please refresh the page to try again.</p>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <AuthProvider>
          <div className="App">
            <AppRoutes />
          </div>
        </AuthProvider>
      </Router>
    </ErrorBoundary>
  );
}

export default App;