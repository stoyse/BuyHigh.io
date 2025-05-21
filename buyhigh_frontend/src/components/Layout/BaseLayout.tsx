import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import './BaseLayout.css';
import { GetUserInfo, logoutUser } from '../../apiService';

interface BaseLayoutProps {
  children: React.ReactNode;
  title?: string;
}

const BaseLayout: React.FC<BaseLayoutProps> = ({ children, title = "BuyHigh.io" }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true' || 
           window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [user, setUser] = useState<any>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();
  
  const location = useLocation();

  // Darkmode toggle handler
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  // Simulate user fetch
  useEffect(() => {
    // Placeholder for user authentication
    // In a real app, you'd fetch user data from an API or context
    const checkAuth = async () => {
      // Mock user data for demonstration
      const mockUser = {
        username: 'TraderJoe',
        email: 'trader@buyhigh.io',
        isAuthenticated: true,
        is_dev: true
      };
      
      // Simulating authenticated user
      setUser(mockUser);
    };
    
    checkAuth();
  }, []);

  const [userData, setUserData] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const data = await GetUserInfo('1'); // Beispiel-User-ID
        setUserData(data);
      } catch (err) {
        setError('Fehler beim Abrufen der Benutzerdaten.');
        console.error(err);
      }
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const data = await GetUserInfo('1');
        setUser(data);
      } catch (err) {
        setError('Fehler beim Abrufen der Benutzerdaten.');
        console.error(err);
      }
    };

    fetchUserData();
  }, []);

  // Logout function
  const handleLogout = async () => {
    try {
      await logoutUser();
      setUser(null);
      // Redirect to login page after successful logout
      navigate('/login');
    } catch (err) {
      console.error('Error during logout:', err);
      // Still clear the user state even if the API call fails
      setUser(null);
      navigate('/login');
    }
  };

  return (
    <div className="bg-gray-50 text-gray-800 dark:bg-gray-900 dark:text-gray-200 neo-grid transition-colors duration-300 min-h-screen flex flex-col">
      {/* Ambient background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-500 rounded-full opacity-10 blur-[100px] animate-pulse-slow"></div>
        <div className="absolute bottom-1/3 left-1/5 w-80 h-80 bg-blue-500 rounded-full opacity-10 blur-[100px] animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
        <div className="absolute top-2/3 right-1/3 w-72 h-72 bg-pink-500 rounded-full opacity-10 blur-[100px] animate-pulse-slow" style={{ animationDelay: '3s' }}></div>
      </div>
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 glass-nav border-b border-purple-500/20 dark:border-purple-500/10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex-shrink-0 flex items-center group">
                <div className="relative h-10 w-10 rounded-xl flex items-center justify-center bg-neo-purple/10 backdrop-blur-sm overflow-hidden neon-border group-hover:shadow-neo transition-all duration-500">
                  <div className="absolute inset-0 bg-gradient-neo opacity-30 animate-gradient"></div>
                  <span className="font-pixel text-neo-purple text-sm relative z-10 group-hover:text-white transition-colors">B</span>
                </div>
                <span className="ml-2 font-pixel text-xl bg-clip-text text-transparent bg-gradient-to-r from-neo-purple to-neo-blue">BuyHigh.io</span>
              </Link>
              
              <div className="hidden sm:ml-10 sm:flex items-baseline space-x-4">
                {user && (
                  <>
                    <Link to="/dashboard" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/dashboard' ? 'bg-neo-purple/10 text-neo-purple' : 'text-gray-700 dark:text-gray-300 hover:bg-neo-purple/10 hover:text-neo-purple dark:hover:text-neo-purple'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-neo-purple/70 group-hover:text-neo-purple transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                      </svg>
                      Dashboard
                    </Link>
                    <Link to="/trade" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/trade' ? 'bg-neo-blue/10 text-neo-blue' : 'text-gray-700 dark:text-gray-300 hover:bg-neo-blue/10 hover:text-neo-blue dark:hover:text-neo-blue'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-neo-blue/70 group-hover:text-neo-blue transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      Trade
                    </Link>
                    <Link to="/news" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/news' ? 'bg-neo-amber/10 text-neo-amber' : 'text-gray-700 dark:text-gray-300 hover:bg-neo-amber/10 hover:text-neo-amber dark:hover:text-neo-amber'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-neo-amber/70 group-hover:text-neo-amber transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path>
                      </svg>
                      News
                    </Link>
                    <Link to="/casino" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/casino' ? 'bg-pink-500/10 text-pink-500' : 'text-gray-700 dark:text-gray-300 hover:bg-pink-500/10 hover:text-pink-500 dark:hover:text-pink-400'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-pink-500/70 group-hover:text-pink-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      Casino
                    </Link>
                    <Link to="/roadmap" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/roadmap' ? 'bg-neo-cyan/10 text-neo-cyan' : 'text-gray-700 dark:text-gray-300 hover:bg-neo-cyan/10 hover:text-neo-cyan dark:hover:text-neo-cyan'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-neo-cyan/70 group-hover:text-neo-cyan transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
                      </svg>
                      Roadmap
                    </Link>
                    <Link to="/social" className={`px-3 py-2 rounded-lg text-sm font-medium ${location.pathname === '/social' ? 'bg-neo-emerald/10 text-neo-emerald' : 'text-gray-700 dark:text-gray-300 hover:bg-neo-emerald/10 hover:text-neo-emerald dark:hover:text-neo-emerald'} transition-all duration-200 flex items-center group`}>
                      <svg className="w-5 h-5 mr-1.5 text-neo-emerald/70 group-hover:text-neo-emerald transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                      </svg>
                      Social
                    </Link>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <div className="hidden sm:block dropdown">
                    <div 
                      className="glass-card py-1 px-3 rounded-full cursor-pointer flex items-center"
                      onClick={() => setDropdownOpen(!dropdownOpen)}
                    >
                      <div className="relative w-8 h-8 rounded-full overflow-hidden mr-2 bg-gradient-to-br from-neo-purple to-neo-blue p-0.5">
                        <div className="absolute inset-0 bg-gradient-neo opacity-30 animate-gradient"></div>
                        <div className="w-full h-full rounded-full bg-white dark:bg-gray-800 flex items-center justify-center relative z-10">
                          <span className="font-medium text-sm text-neo-purple">{user.username ? user.username[0].toUpperCase() : 'U'}</span>
                        </div>
                      </div>
                      <span className="text-sm font-medium">{user.username}</span>
                      <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                      </svg>
                    </div>
                    
                    {/* Dropdown Menu */}
                    {dropdownOpen && (
                      <div className="dropdown-content glass-card rounded-xl shadow-neo-lg overflow-hidden border border-gray-200/20 dark:border-gray-700/30 block opacity-100 transform-none">
                        <div className="p-4 border-b border-gray-200/20 dark:border-gray-700/30">
                          <p className="font-medium text-sm text-gray-800 dark:text-gray-200">{user.username}</p>
                          <p className="text-xs text-gray-600 dark:text-gray-300">{user.email}</p>
                        </div>
                        
                        <div className="p-2">
                          <Link to="/settings" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-cyan">
                            <svg className="w-5 h-5 text-neo-cyan/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <span>Settings</span>
                          </Link>
                          <Link to="/profile" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-purple">
                            <svg className="w-5 h-5 text-neo-purple/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                            </svg>
                            <span>My Profile</span>
                          </Link>
                          <Link to="/badges" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-amber">
                            <svg className="w-5 h-5 text-neo-amber/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                            </svg>
                            <span>Trader Badges</span>
                          </Link>
                          <Link to="/transactions" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-blue">
                            <svg className="w-5 h-5 text-neo-blue/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            <span>Transaction History</span>
                          </Link>
                          {user.is_dev && (
                            <Link to="/dev" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-green-500">
                              <svg className="w-5 h-5 text-green-500/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                              </svg>
                              <span>Dev Center</span>
                            </Link>
                          )}
                        </div>
                        
                        <div className="p-2 border-t border-gray-200/10 dark:border-gray-700/20">
                          <a href="#" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-neo-red hover:bg-neo-red/5" onClick={handleLogout}>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                            </svg>
                            <span>Logout</span>
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <button 
                    onClick={handleLogout} 
                    className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-neo-red/10 text-neo-red border border-neo-red/20 hover:bg-neo-red hover:text-white transition-all duration-300 flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>
                    </svg>
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <button 
                    onClick={() => setUser({ username: 'GuestUser', email: 'guest@buyhigh.io', isAuthenticated: true })}
                    className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-neo-blue/10 text-neo-blue border border-neo-blue/20 hover:bg-neo-blue hover:text-white transition-all duration-300 flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>
                    </svg>
                    Login
                  </button>
                  <button 
                    className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-gray-200/60 text-gray-700 border border-gray-300/40 hover:bg-gray-400 hover:text-white transition-all duration-300 flex items-center ml-2"
                    onClick={() => setUser({ username: 'GuestUser', email: 'guest@buyhigh.io', isAuthenticated: true })}
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <circle cx="12" cy="12" r="10" strokeWidth="2"></circle>
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 16v.01M12 8v4"></path>
                    </svg>
                    Guest
                  </button>
                  <button 
                    className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-neo-emerald/10 text-neo-emerald border border-neo-emerald/20 hover:bg-neo-emerald hover:text-white transition-all duration-300 flex items-center"
                    onClick={() => setUser({ username: 'NewUser', email: 'new@buyhigh.io', isAuthenticated: true })}
                  >
                    <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path>
                    </svg>
                    Register
                  </button>
                </>
              )}
              
              {/* Dark mode toggle */}
              <button 
                onClick={() => setDarkMode(!darkMode)} 
                className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800"
              >
                {darkMode ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" fillRule="evenodd"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"></path>
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
        
        {/* Mobile menu button */}
        <div className="sm:hidden">
          <button 
            type="button" 
            className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:text-neo-purple hover:bg-neo-purple/10 focus:outline-none"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <svg className="h-6 w-6" stroke="currentColor" fill="none" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          {/* Mobile menu */}
          {mobileMenuOpen && (
            <div className="glass-card m-2 p-2 rounded-xl shadow-glass">
              {user && (
                <>
                  <Link to="/dashboard" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-neo-purple/10 hover:text-neo-purple" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
                  <Link to="/trade" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-neo-blue/10 hover:text-neo-blue" onClick={() => setMobileMenuOpen(false)}>Trade</Link>
                  <Link to="/news" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-neo-amber/10 hover:text-neo-amber" onClick={() => setMobileMenuOpen(false)}>News</Link>
                  <Link to="/casino" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-pink-500/10 hover:text-pink-500" onClick={() => setMobileMenuOpen(false)}>Casino</Link>
                  <Link to="/settings" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-neo-cyan/10 hover:text-neo-cyan" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
                  <Link to="/social" className="block px-3 py-2 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-neo-emerald/10 hover:text-neo-emerald" onClick={() => setMobileMenuOpen(false)}>Social</Link>
                </>
              )}
            </div>
          )}
        </div>
      </nav>
      
      <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-grow relative animate-blur-in">
        {/* Main Content */}
        <main className="relative glass-card backdrop-blur-xl border border-white/5 dark:border-gray-700/30 rounded-2xl shadow-glass overflow-hidden">
          {/* Ambient elements inside container */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-60">
            <div className="absolute -top-40 -right-40 w-80 h-80 bg-neo-purple rounded-full opacity-10 blur-[80px]"></div>
            <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-neo-blue rounded-full opacity-10 blur-[80px]"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full h-40 bg-gray-900/10 dark:bg-white/5 blur-[100px]"></div>
          </div>
          
          {/* Content with relative position */}
          <div className="relative z-10 p-6">
            {/* Page title as needed */}
            {title !== "BuyHigh.io" && (
              <h1 className="text-3xl font-bold mb-6 text-gray-800 dark:text-gray-100">{title}</h1>
            )}
            
            {/* Page content */}
            {children}
          </div>
        </main>
      </div>
      
      <footer className="mt-auto border-t border-gray-200 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center mb-4 md:mb-0">
              <div className="h-8 w-8 rounded-lg flex items-center justify-center bg-neo-purple/10 mr-2">
                <span className="font-pixel text-neo-purple text-xs">B</span>
              </div>
              <span className="font-pixel text-neo-purple text-sm">BuyHigh.io</span>
            </div>
            
            <div className="flex space-x-6 mb-4 md:mb-0">
              <a href="#" className="text-gray-500 hover:text-neo-purple transition-colors">
                <span className="sr-only">Twitter</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-500 hover:text-neo-purple transition-colors">
                <span className="sr-only">GitHub</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/>
                </svg>
              </a>
              <a href="#" className="text-gray-500 hover:text-neo-purple transition-colors">
                <span className="sr-only">Discord</span>
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M20.317 4.492c-1.53-.69-3.17-1.2-4.885-1.49a.075.075 0 0 0-.079.036c-.21.39-.444.898-.608 1.296a19.82 19.82 0 0 0-5.69 0 12.28 12.28 0 0 0-.617-1.296.077.077 0 0 0-.079-.036A20.29 20.29 0 0 0 3.475 4.49C.7 8.966.272 13.331.756 17.632a.083.083 0 0 0 .031.056 20.03 20.03 0 0 0 6.297 3.159.077.077 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.21 13.21 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.39 12.39 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.96 19.96 0 0 0 6.3-3.159.077.077 0 0 0 .032-.055c.578-5.027-.937-9.349-3.957-13.142zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" clipRule="evenodd"/>
                </svg>
              </a>
            </div>
            
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
              &copy; 2025 BuyHigh.io - Buy High, Sell Low
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default BaseLayout;
