import React, { useState, useEffect } from 'react';
import { GetUserInfo } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';
import BaseLayout from '../../components/Layout/BaseLayout';

interface UserProfile {
  id: number;
  username: string;
  email: string;
  created_at: string;
  level?: number;
  xp?: number;
  balance?: number;
  total_investment?: number;
  total_trades?: number;
  profile_picture?: string;
}

const ProfilePage: React.FC = () => {
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingPicture, setUploadingPicture] = useState(false);
  
  const { user: authUser, loading: authLoading } = useAuth();

  // Calculate XP progress
  const calculateXPProgress = (currentXP: number = 0, level: number = 1) => {
    const xpForCurrentLevel = (level - 1) * 1000; // 1000 XP per level
    const xpForNextLevel = level * 1000;
    const progressXP = currentXP - xpForCurrentLevel;
    const neededXP = xpForNextLevel - xpForCurrentLevel;
    return {
      current: progressXP,
      needed: neededXP,
      percentage: (progressXP / neededXP) * 100
    };
  };

  useEffect(() => {
    const fetchUserProfile = async () => {
      if (!authUser || !authUser.id) {
        console.warn("[ProfilePage] No authUser or no authUser.id present!", authUser);
        setError('User not authenticated. Please login.');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const userId = authUser.id.toString();

        console.log("[ProfilePage] Fetching user profile for userId:", userId);

        const data = await GetUserInfo(userId);

        if (data && data.success) {
          setUserProfile(data.user || data.data || data);
        } else {
          const errorMessage = data?.message || 'Failed to fetch user profile.';
          setError(errorMessage);
          console.warn("[ProfilePage] GetUserInfo was not successful:", data);
        }
      } catch (err: any) {
        const errorMessage = err.message || 'An unexpected error occurred while fetching user profile.';
        setError(errorMessage);
        console.error("[ProfilePage] Error in fetchUserProfile:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (!authLoading) {
      fetchUserProfile();
    }
  }, [authUser, authLoading]);

  const handleProfilePictureUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Basic validation
    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      alert('File size must be less than 5MB');
      return;
    }

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    setUploadingPicture(true);
    try {
      // For now, just simulate upload - you'd implement actual upload logic here
      console.log('Uploading profile picture:', file.name);
      // TODO: Implement actual file upload to backend
      alert('Profile picture upload functionality to be implemented');
    } catch (error) {
      console.error('Error uploading profile picture:', error);
      alert('Failed to upload profile picture');
    } finally {
      setUploadingPicture(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  };

  const getUserType = (user: UserProfile) => {
    if (user.username.includes('guest_')) {
      return { label: 'Guest User', className: 'bg-gray-500/30' };
    } else if (user.id <= 2) {
      return { label: 'Administrator', className: 'bg-neo-amber/40' };
    } else {
      return { label: 'Member', className: 'bg-neo-blue/30' };
    }
  };

  const getMoodPetEmoji = () => {
    // Simple mood calculation based on balance/level
    const balance = userProfile?.balance || 0;
    if (balance > 10000) return '😎';
    if (balance > 5000) return '😊';
    if (balance > 1000) return '🙂';
    if (balance > 0) return '😐';
    return '😢';
  };

  if (isLoading) {
    return (
      <BaseLayout title="Your Profile">
        <div className="flex items-center justify-center min-h-screen">
          <div className="glass-card p-8 rounded-2xl text-center">
            <div className="w-8 h-8 mx-auto mb-4 rounded-full border-4 border-neo-purple border-t-transparent animate-spin"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading your profile...</p>
          </div>
        </div>
      </BaseLayout>
    );
  }

  if (error) {
    return (
      <BaseLayout title="Your Profile">
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
      </BaseLayout>
    );
  }

  if (!userProfile) {
    return (
      <BaseLayout title="Your Profile">
        <div className="flex items-center justify-center min-h-screen">
          <div className="glass-card p-8 rounded-2xl text-center">
            <p className="text-gray-600 dark:text-gray-400">No profile data available</p>
          </div>
        </div>
      </BaseLayout>
    );
  }

  const userType = getUserType(userProfile);
  const xpProgress = calculateXPProgress(userProfile.xp, userProfile.level);

  return (
    <BaseLayout title="Your Profile">
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Your Profile</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Your personal investment journey</p>
        </div>

        <div className="glass-card rounded-2xl overflow-hidden border border-white/10 dark:border-gray-700/30 hover:shadow-neo transition-all duration-300 animate-blur-in">
          {/* User Header with Background */}
          <div className="relative h-48 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-neo-purple to-neo-blue opacity-20"></div>
            
            {/* Level Badge */}
            <div className="absolute top-6 right-6 bg-black/30 backdrop-blur-sm text-white px-4 py-2 rounded-full text-base font-bold flex items-center">
              <svg className="w-6 h-6 mr-2 text-neo-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
              </svg>
              Level {userProfile.level || 1}
            </div>

            {/* User Type Badge */}
            <div className={`absolute top-6 left-6 ${userType.className} backdrop-blur-sm text-white px-4 py-2 rounded-full text-base font-medium`}>
              {userType.label}
            </div>
          </div>

          {/* User Avatar */}
          <div className="flex justify-center -mt-24 relative">
            <div className="relative w-48 h-48 rounded-full overflow-hidden bg-gradient-to-br from-neo-purple to-neo-blue p-1">
              <div className="absolute inset-0 bg-gradient-neo opacity-30 animate-gradient"></div>
              <div className="w-full h-full rounded-full bg-white dark:bg-gray-800 flex items-center justify-center relative z-10">
                {userProfile.profile_picture ? (
                  <img 
                    src={userProfile.profile_picture} 
                    alt="Profile" 
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <div className="text-6xl font-bold text-neo-purple">
                    {userProfile.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              
              {/* Profile Picture Upload Button */}
              <div 
                className="absolute bottom-2 right-16 w-10 h-10 rounded-full bg-white/90 dark:bg-gray-800/90 shadow-lg cursor-pointer border-2 border-neo-purple flex items-center justify-center hover:bg-neo-purple/20 transition-all duration-300 z-[100]"
                onClick={() => document.getElementById('profile-picture-input')?.click()}
              >
                {uploadingPicture ? (
                  <div className="w-4 h-4 border-2 border-neo-purple border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5 text-neo-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                  </svg>
                )}
              </div>
                
              {/* Mood Pet Indicator */}
              <div className="absolute bottom-3 right-3 w-16 h-16 rounded-full bg-white dark:bg-gray-700 border-4 border-white dark:border-gray-800 flex items-center justify-center">
                <span className="text-2xl">{getMoodPetEmoji()}</span>
              </div>
            </div>

            {/* Hidden file input */}
            <input 
              type="file" 
              id="profile-picture-input" 
              className="hidden" 
              accept="image/*"
              onChange={handleProfilePictureUpload}
            />
          </div>

          {/* User Info */}
          <div className="px-8 pt-4 pb-8">
            <div className="text-center mb-8">
              <h2 className="font-bold text-3xl text-gray-800 dark:text-gray-200 mb-2">{userProfile.username}</h2>
              <p className="text-md text-gray-600 dark:text-gray-400 mb-1">{userProfile.email}</p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Member since {formatDate(userProfile.created_at)}
              </p>
            </div>

            {/* XP Progress Bar */}
            <div className="mb-8 max-w-lg mx-auto">
              <div className="flex justify-between text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                <span>Level {userProfile.level || 1}</span>
                <span>{xpProgress.current} / {xpProgress.needed} XP</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-neo-purple to-neo-blue h-3 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(xpProgress.percentage, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
              {/* Financial Stats */}
              <div className="glass-card rounded-xl p-6 border border-white/10 dark:border-gray-700/30">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-neo-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                  </svg>
                  Financial
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Balance</span>
                    <span className="font-medium text-neo-emerald">${(userProfile.balance || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Investment</span>
                    <span className="font-medium">${(userProfile.total_investment || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              {/* Trading Stats */}
              <div className="glass-card rounded-xl p-6 border border-white/10 dark:border-gray-700/30">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-neo-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                  Trading
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Trades</span>
                    <span className="font-medium">{userProfile.total_trades || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Success Rate</span>
                    <span className="font-medium text-neo-emerald">--%</span>
                  </div>
                </div>
              </div>
              
              {/* Achievement Stats */}
              <div className="glass-card rounded-xl p-6 border border-white/10 dark:border-gray-700/30">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-neo-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
                  </svg>
                  Achievements
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Badges Earned</span>
                    <span className="font-medium">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Rank</span>
                    <span className="font-medium text-neo-purple">Novice</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap justify-center gap-4">
              <button className="neo-button bg-neo-blue/80 hover:bg-neo-blue text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                </svg>
                Edit Profile
              </button>
              <button className="neo-button bg-neo-purple/80 hover:bg-neo-purple text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 flex items-center">
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"></path>
                </svg>
                Share Profile
              </button>
            </div>
          </div>
        </div>

        {/* Easter Eggs Section */}
        <div className="container mx-auto px-4 py-8 max-w-5xl">
          <div className="glass-card rounded-2xl overflow-hidden border border-white/10 dark:border-gray-700/30 hover:shadow-neo transition-all duration-300 animate-blur-in">
            {/* Hidden comment with easter egg */}
            {/* Finding all the easter eggs? You're a detective! Use code "STONKS" for more credits! */}
            
            {/* Hidden div with easter egg */}
            <div 
              style={{ height: '1px', overflow: 'hidden', color: 'transparent', userSelect: 'none' }}
              onMouseOver={(e) => {
                e.currentTarget.style.height = '20px';
                e.currentTarget.style.color = '#8b5cf6';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.height = '1px';
                e.currentTarget.style.color = 'transparent';
              }}
            >
              Secret message: Use code APESSTRONG for bonus credits!
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default ProfilePage;
