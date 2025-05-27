import React, { useState, useEffect } from 'react';
import { logoutUser, GetUserInfo } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';

const SettingsPage: React.FC = () => {
  const [userInfo, setUserInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { user: authUser, loading: authLoading } = useAuth(); // Get user and loading state from AuthContext

  useEffect(() => {
    const fetchUserInfo = async () => {
      if (authLoading) { // Wait for auth state to be determined
        return;
      }

      // Corrected check for authUser and authUser.id
      if (!authUser || authUser.id === undefined || authUser.id === null) {
        setError('User not authenticated. Please login.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true); // Set loading true before fetching
        const userId = authUser.id.toString();
        const data = await GetUserInfo(userId); 
        if (data && data.success) {
          setUserInfo(data.user || data.data || data); // Adjust based on actual API response structure
        } else {
          setError(data.message || 'Failed to fetch user information.');
        }
      } catch (err) {
        setError('Failed to fetch user information.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserInfo();
  }, [authUser, authLoading]); // Depend on authUser and authLoading

  const handleLogout = async () => {
    try {
      await logoutUser();
      // Redirect to login page or update app state
      console.log('User logged out successfully');
    } catch (error) {
      console.error('Logout failed:', error);
      // Handle logout error (e.g., show a notification)
    }
  };

  // TODO: Implement theme change, password change, and delete account functionalities

  if (isLoading) {
    return <div className="container mx-auto px-4 py-6 text-center">Loading settings...</div>;
  }

  if (error) {
    return <div className="container mx-auto px-4 py-6 text-center text-red-500">{error}</div>;
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-full">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-medium gradient-text mb-2 flex justify-center items-center">
          <svg className="w-8 h-8 mr-2 animate-pulse-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400 text-sm max-w-2xl mx-auto">
          Customize your BuyHigh.io experience to your liking
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Theme Settings Card */}
        <div className="settings-section glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 relative overflow-hidden animate-float" style={{ animationDelay: '0.1s' }}>
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-neo-purple rounded-full opacity-10 blur-3xl"></div>
          <h2 className="text-xl font-medium text-gray-800 dark:text-gray-100 mb-6 flex items-center">
            {/* SVG Icon for Design Settings */}
            Design Settings
          </h2>
          {/* Form for theme settings will go here */}
          <form className="space-y-6">
            <input type="hidden" name="form_type" value="theme_settings" />
            {/* Theme selection options */}
          </form>
        </div>

        {/* Change Password Card */}
        <div className="settings-section glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 relative overflow-hidden animate-float" style={{ animationDelay: '0.3s' }}>
          <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-neo-blue rounded-full opacity-10 blur-3xl"></div>
          <h2 className="text-xl font-medium text-gray-800 dark:text-gray-100 mb-6 flex items-center">
            {/* SVG Icon for Change Password */}
            Change Password
          </h2>
          {/* Conditional rendering for password change form based on auth provider */}
          {/* {(!g.user.get('firebase_provider') || g.user.get('firebase_provider') === 'password') ? (
            <form id="passwordChangeForm" className="space-y-6">
              
            </form>
          ) : (
            <p>Password changes are managed by your social login provider.</p>
          )} */}
        </div>
      </div>

      {/* Delete Account Card */}
      <div className="mt-8 settings-section glass-card shadow-neo border border-neo-red/20 rounded-2xl p-6 relative overflow-hidden animate-float" style={{ animationDelay: '0.5s' }}>
        <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-neo-red/30 rounded-full opacity-20 blur-3xl"></div>
        <h2 className="text-xl font-medium text-neo-red mb-6 flex items-center">
          {/* SVG Icon for Delete Account */}
          Delete Account
        </h2>
        <div className="glass-card p-5 rounded-xl mb-6 border border-neo-red/20">
          {/* Warning message about account deletion */}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); if (window.confirm('Are you absolutely sure you want to permanently delete your account? This action cannot be undone.')) { /* Call delete account API */ } }}>
          <input type="hidden" name="form_type" value="delete_account" />
          {/* Input fields for account deletion confirmation if needed */}
          <button type="submit" className="btn-danger">
            Delete My Account
          </button>
        </form>
      </div>
      <button onClick={handleLogout} className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
        Logout
      </button>
    </div>
  );
};

export default SettingsPage;
