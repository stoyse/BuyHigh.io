import React, { useState, useEffect } from 'react';
import { logoutUser, GetUserInfo } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';
import BaseLayout from '../../components/Layout/BaseLayout'; // Added import
import { getAuth, sendPasswordResetEmail } from "firebase/auth"; // Firebase import

const SettingsPage: React.FC = () => {
  const [userInfo, setUserInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState('security');
  const [resetPasswordMessage, setResetPasswordMessage] = useState<string | null>(null); // For password reset feedback
  const [resetPasswordError, setResetPasswordError] = useState<string | null>(null); // For password reset error

  const { user: authUser, loading: authLoading, logout } = useAuth();

  useEffect(() => {
    const fetchPageData = async () => {
      if (!authUser || !authUser.id) {
        console.warn("[SettingsPage] No authUser or no authUser.id present!", authUser);
        setError('User not authenticated. Please login.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const userId = authUser.id.toString();

        console.log("[SettingsPage] Attempting to call GetUserInfo with userId:", userId);

        const data = await GetUserInfo(userId); 

        if (data && data.success) {
          setUserInfo(data.user || data.data || data); 
        } else {
          const errorMessage = data?.message || 'Failed to fetch user information (API request not successful).';
          setError(errorMessage);
          console.warn("[SettingsPage] GetUserInfo was not successful or data malformed:", data);
        }
      } catch (err: any) {
        const errorMessage = err.message || 'An unexpected error occurred while fetching user information.';
        setError(errorMessage);
        console.error("[SettingsPage] Error in fetchPageData:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (!authLoading) {
      fetchPageData();
    }

  }, [authUser, authLoading]);

  const handleLogout = async () => {
    try {
      await logoutUser();
      logout();
      console.log('User logged out successfully');
    } catch (error) {
      console.error('Logout failed:', error);
      logout();
    }
  };

  const handlePasswordReset = async () => {
    if (!authUser || !authUser.email) {
      setResetPasswordError("User email not found. Please ensure you are logged in.");
      return;
    }
    const auth = getAuth();
    try {
      await sendPasswordResetEmail(auth, authUser.email);
      setResetPasswordMessage("Password reset email sent. Please check your inbox.");
      setResetPasswordError(null);
    } catch (error: any) {
      console.error("Error sending password reset email:", error);
      setResetPasswordError(error.message || "Error sending password reset email.");
      setResetPasswordMessage(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="glass-card p-8 rounded-2xl text-center">
          <div className="w-8 h-8 mx-auto mb-4 rounded-full border-4 border-neo-purple border-t-transparent"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="glass-card p-8 rounded-2xl text-center border-neo-red/20">
          <div className="w-12 h-12 mx-auto mb-4 bg-neo-red/10 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-neo-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
          </div>
          <p className="text-neo-red font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <BaseLayout title="Account Settings"> {/* Added BaseLayout wrapper and title prop */}
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header Section */}
        <div className="glass-card mb-6 p-6 rounded-2xl border border-gray-200/10 dark:border-gray-700/20 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-neo-purple rounded-full opacity-10 blur-3xl animate-pulse-slow"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="w-16 h-16 bg-gradient-to-br from-neo-purple to-neo-blue rounded-xl flex items-center justify-center">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                  </svg>
                </div>
                <div>
                  {/* The h1 is removed here because BaseLayout will render it via title prop */}
                  <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your account preferences and security</p>
                </div>
              </div>
            </div>
            
            {/* Navigation Tabs */}
            <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl">
              {[
                { id: 'profile', label: 'Profile', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z', disabled: true },
                { id: 'security', label: 'Security', icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z' },
                { id: 'preferences', label: 'Preferences', icon: 'M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01', disabled: true },
                { id: 'danger', label: 'Danger Zone', icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveSection(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    activeSection === tab.id 
                      ? 'bg-white dark:bg-gray-700 shadow-sm text-neo-purple' 
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                  disabled={tab.disabled} // Disable button if tab.disabled is true
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={tab.icon}></path>
                  </svg>
                  <span className="hidden sm:inline">{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Sections */}
        <div className="space-y-6">
          {/* Profile Section */}
          {activeSection === 'profile' && (
            <div className="glass-card p-6 rounded-2xl border border-gray-200/10 dark:border-gray-700/20 relative overflow-hidden">
              <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-neo-blue rounded-full opacity-10 blur-3xl animate-pulse-slow"></div>
              <div className="relative z-10">
                <h2 className="text-xl font-semibold mb-6 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-neo-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                  </svg>
                  Profile Information
                </h2>
                
                <form className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Username</label>
                      <input 
                        type="text" 
                        defaultValue={authUser?.username || ''} 
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-neo-blue focus:border-transparent transition-all duration-200"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Email</label>
                      <input 
                        type="email" 
                        defaultValue={authUser?.email || ''} 
                        className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-neo-blue focus:border-transparent transition-all duration-200"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Bio</label>
                    <textarea 
                      rows={3} 
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-neo-blue focus:border-transparent transition-all duration-200"
                      placeholder="Tell us about yourself..."
                    ></textarea>
                  </div>
                  
                  <button type="submit" className="neo-button bg-neo-blue/80 hover:bg-neo-blue text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                    Save Changes
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* Security Section */}
          {activeSection === 'security' && (
            <div className="space-y-6">
              <div className="glass-card p-6 rounded-2xl border border-gray-200/10 dark:border-gray-700/20 relative overflow-hidden">
                <div className="absolute -top-20 -right-20 w-40 h-40 bg-neo-purple rounded-full opacity-10 blur-3xl animate-pulse-slow"></div>
                <div className="relative z-10">
                  <h2 className="text-xl font-semibold mb-6 flex items-center">
                    Password
                  </h2>
                  
                  {(!authUser?.firebase_provider || authUser?.firebase_provider === 'password') ? (
                    <div>
                      <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Click the button below to receive an email to reset your password.
                      </p>
                      <button 
                        onClick={handlePasswordReset}
                        className="neo-button bg-neo-purple/80 hover:bg-neo-purple text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H5v-2H3v-2H1v-4a6 6 0 016-6h4a6 6 0 016 6zM15 7V5a2 2 0 00-2-2H9a2 2 0 00-2 2v2"></path>
                        </svg>
                        Send Password Reset Email
                      </button>
                      {resetPasswordMessage && (
                        <p className="mt-4 text-sm text-neo-emerald">{resetPasswordMessage}</p>
                      )}
                      {resetPasswordError && (
                        <p className="mt-4 text-sm text-neo-red">{resetPasswordError}</p>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                        </svg>
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">
                        Password changes are managed by your social login provider ({authUser?.firebase_provider}).
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Preferences Section */}
          {activeSection === 'preferences' && (
            <div className="glass-card p-6 rounded-2xl border border-gray-200/10 dark:border-gray-700/20 relative overflow-hidden">
              <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-neo-emerald rounded-full opacity-10 blur-3xl animate-pulse-slow"></div>
              <div className="relative z-10">
                <h2 className="text-xl font-semibold mb-6 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-neo-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path>
                  </svg>
                  Appearance & Preferences
                </h2>
                
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Theme</label>
                    <div className="grid grid-cols-3 gap-3">
                      {['System', 'Light', 'Dark'].map((theme) => (
                        <button
                          key={theme}
                          className="p-4 rounded-lg border-2 border-gray-200 dark:border-gray-700 hover:border-neo-emerald transition-all duration-200 text-center"
                        >
                          <div className="w-8 h-8 mx-auto mb-2 rounded-full bg-gradient-to-br from-gray-300 to-gray-500"></div>
                          <span className="text-sm font-medium">{theme}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div>
                        <h3 className="font-medium">Email Notifications</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Receive trading alerts via email</p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-neo-emerald transition-colors">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-6"></span>
                      </button>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div>
                        <h3 className="font-medium">Push Notifications</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">Get instant browser notifications</p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-300 transition-colors">
                        <span className="inline-block h-4 w-4 transform rounded-full bg-white transition translate-x-1"></span>
                      </button>
                    </div>
                  </div>
                  
                  <button className="neo-button bg-neo-emerald/80 hover:bg-neo-emerald text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200">
                    Save Preferences
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Danger Zone */}
          {activeSection === 'danger' && (
            <div className="glass-card p-6 rounded-2xl border border-neo-red/30 dark:border-neo-red/40 relative overflow-hidden">
              <div className="absolute -top-20 -right-20 w-40 h-40 bg-neo-red/20 rounded-full opacity-20 blur-3xl animate-pulse-slow"></div>
              <div className="relative z-10">
                <h2 className="text-xl font-semibold text-neo-red mb-6 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                  </svg>
                  Danger Zone
                </h2>
                
                <div className="space-y-4">
                  <div className="bg-neo-red/5 dark:bg-neo-red/10 border border-neo-red/20 rounded-lg p-4">
                    <h3 className="font-semibold text-neo-red mb-2">Delete Account</h3>
                    <p className="text-sm text-neo-red/80 dark:text-neo-red/90 mb-4">
                      Permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                    <button 
                      onClick={(e) => {
                        e.preventDefault();
                        if (window.confirm('Are you absolutely sure you want to permanently delete your account? This action cannot be undone.')) {
                          // Call delete account API
                        }
                      }}
                      className="neo-button bg-neo-red/80 hover:bg-neo-red text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd"></path>
                      </svg>
                      Delete Account
                    </button>
                  </div>
                  
                  <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 className="font-semibold mb-2">Sign Out</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      Sign out of your account on this device.
                    </p>
                    <button 
                      onClick={handleLogout}
                      className="neo-button bg-gray-500/80 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                      </svg>
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </BaseLayout>
  );
};

export default SettingsPage;
