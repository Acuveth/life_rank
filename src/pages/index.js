import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginForm, RegisterForm } from '../components/LoginForm';
import { UserProfile } from '../components/UserProfile';
import Dashboard from '../components/Dashboard'; // Changed to default import

// Auth Page Component
export const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);

  return isLogin ? (
    <LoginForm onSwitchToRegister={() => setIsLogin(false)} />
  ) : (
    <RegisterForm onSwitchToLogin={() => setIsLogin(true)} />
  );
};

// Profile Page Component
export const ProfilePage = () => {
  const navigate = useNavigate();

  const handleContinue = () => {
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-extrabold text-gray-900">
            Complete Your Profile
          </h1>
          <p className="mt-2 text-lg text-gray-600">
            Help us personalize your Life Rank experience
          </p>
        </div>

        <UserProfile />

        <div className="mt-8 text-center">
          <button
            onClick={handleContinue}
            className="bg-indigo-600 text-white px-8 py-3 rounded-md text-lg font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export { Dashboard };