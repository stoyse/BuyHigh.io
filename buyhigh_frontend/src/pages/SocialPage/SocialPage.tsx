import React, { useEffect, useState } from 'react';
import { getAllUsers } from '../../services/apiService'; // Adjust path as necessary
import BaseLayout from '../../components/Layout/BaseLayout';

// Define a type for the user profile data
interface UserProfile {
  id: number;
  username: string;
  level: number;
  xp: number;
  balance: number; // Assuming balance is a number
  total_profit: number; // Assuming profit is a number
  total_trades: number; // Assuming trades is a number
  profile_picture_url?: string; // Optional profile picture URL
  // Add other fields as necessary based on your BasicUser model
}

const SocialPage: React.FC = () => {
  const [profiles, setProfiles] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortOption, setSortOption] = useState<string>('level-desc');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const response = await getAllUsers();
        if (response.success) {
          // Map backend data to UserProfile, ensure all fields are covered
          const fetchedProfiles = response.users.map((user: any) => ({
            id: user.id,
            username: user.username,
            level: user.level || 0, // Default to 0 if not provided
            xp: user.xp || 0, // Default to 0
            balance: user.balance || 0, // Default to 0
            total_profit: user.total_profit || 0, // Default to 0
            total_trades: user.total_trades || 0, // Default to 0
            profile_picture_url: user.profile_picture_url || undefined, // Handle optional URL
            // Add other mappings here
          }));
          setProfiles(fetchedProfiles);
        } else {
          setError(response.message || 'Failed to load users.');
        }
      } catch (err) {
        setError('An error occurred while fetching users.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // Implement sorting and filtering logic based on sortOption and searchTerm
  const sortedAndFilteredProfiles = profiles
    .filter(profile => profile.username.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      switch (sortOption) {
        case 'level-desc':
          return b.level - a.level;
        case 'xp-desc':
          return b.xp - a.xp;
        case 'balance-desc':
          return b.balance - a.balance;
        case 'profit-desc':
          return b.total_profit - a.total_profit;
        case 'trades-desc':
          return b.total_trades - a.total_trades;
        // Add 'newest' if you have a created_at field or similar
        default:
          return 0;
      }
    });

  if (loading) {
    return (
      <BaseLayout title="Community">
        <div className="text-center p-10">Loading community...</div>
      </BaseLayout>
    );
  }

  if (error) {
    return (
      <BaseLayout title="Community">
        <div className="text-center p-10 text-red-500">Error: {error}</div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout title="Community">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">BuyHigh Community</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Connect with fellow financial adventurers</p>
      </div>

      {/* Filter and Sort Controls */}
      <div className="flex flex-wrap items-center justify-between mb-6 gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Sort by:</span>
          <select 
            id="sort-users" 
            value={sortOption}
            onChange={(e) => setSortOption(e.target.value)}
            className="bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 text-sm rounded-lg focus:ring-neo-purple focus:border-neo-purple p-2.5"
          >
            <option value="level-desc">Highest Level</option>
            <option value="xp-desc">Most XP</option>
            <option value="balance-desc">Highest Balance</option>
            <option value="profit-desc">Most Profitable</option>
            <option value="trades-desc">Most Active</option>
            {/* <option value="newest">Newest Members</option> */}
          </select>
        </div>
        
        <div className="relative">
          <input 
            type="text" 
            id="search-users" 
            placeholder="Search users by name" 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 text-sm rounded-lg w-full sm:w-64 focus:ring-neo-purple focus:border-neo-purple p-2.5"
          />
          <svg className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>
      </div>

      {/* User Grid */}
      {sortedAndFilteredProfiles.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sortedAndFilteredProfiles.map((profile, index) => (
            <div 
              key={profile.id} 
              className="bg-white dark:bg-gray-800 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all duration-300"
              style={{ animationDelay: `${index * 0.05}s` }} // Basic animation stagger
            >
              {/* User Header with Background */}
              <div className="relative h-24 bg-gradient-to-r from-purple-500 to-blue-500 opacity-80 dark:opacity-60">
                {/* Level Badge */}
                <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm text-white px-2.5 py-1 rounded-full text-xs font-bold flex items-center">
                  <svg className="w-4 h-4 mr-1 text-yellow-400" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path></svg>
                  Level {profile.level}
                </div>
                {/* You can add Admin/Member/Guest tags here if that data is available */}
              </div>

              {/* User Avatar */}
              <div className="flex justify-center -mt-12">
                <div className="relative w-24 h-24 rounded-full overflow-hidden border-4 border-white dark:border-gray-800 bg-gray-100 dark:bg-gray-700">
                  {profile.profile_picture_url ? (
                    <img src={profile.profile_picture_url} alt={profile.username} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-3xl font-bold text-gray-500 dark:text-gray-400">
                      {profile.username.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
              </div>

              {/* User Info */}
              <div className="px-6 pt-2 pb-6 text-center">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">{profile.username}</h2>
                {/* XP and other stats can be added here */}
                <p className="text-sm text-gray-600 dark:text-gray-400">XP: {profile.xp}</p>
                 <p className="text-sm text-gray-600 dark:text-gray-400">Balance: ${profile.balance.toLocaleString()}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Profit: ${profile.total_profit.toLocaleString()}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">Trades: {profile.total_trades}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-full p-4 inline-block mb-4">
            <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
            </svg>
          </div>
          <h3 className="text-xl font-medium text-gray-900 dark:text-gray-100 mb-1">No users found</h3>
          <p className="text-gray-600 dark:text-gray-400">
            {searchTerm ? 'No users match your search.' : 'Looks like everyone is busy losing money elsewhere.'}
          </p>
        </div>
      )}
    </BaseLayout>
  );
};

export default SocialPage;
