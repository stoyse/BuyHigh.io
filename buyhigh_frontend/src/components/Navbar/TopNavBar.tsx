import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface TopNavBarProps {
  user: any; // Passen Sie den Typ entsprechend Ihrer User-Struktur an
  handleLogout: () => void;
  darkMode: boolean;
  setDarkMode: (value: React.SetStateAction<boolean>) => void;
}

const TopNavBar: React.FC<TopNavBarProps> = ({ user, handleLogout, darkMode, setDarkMode }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  return (
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
              <Link to="/dashboard" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-neo-purple/20">Dashboard</Link>
              <Link to="/trade" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-neo-purple/20">Trade</Link>
              <Link to="/casino" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-neo-purple/20">Casino</Link>
              <Link to="/news" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-neo-purple/20">News</Link>
              <Link to="/social" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-neo-purple/20">Social</Link>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {user && user.user ? (
              <>
                <div className="hidden sm:block dropdown">
                  <div 
                    className="glass-card py-1 px-3 rounded-full cursor-pointer flex items-center"
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                  >
                    <div className="relative w-8 h-8 rounded-full overflow-hidden mr-2 bg-gradient-to-br from-neo-purple to-neo-blue p-0.5">
                      <div className="absolute inset-0 bg-gradient-neo opacity-30 animate-gradient"></div>
                      <div className="w-full h-full rounded-full bg-white dark:bg-gray-800 flex items-center justify-center relative z-10">
                        <span className="font-medium text-sm text-neo-purple">{user.user.username ? user.user.username[0].toUpperCase() : 'U'}</span>
                      </div>
                    </div>
                    <span className="text-sm font-medium">{user.user.username}</span>
                    <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                  </div>
                  
                  {dropdownOpen && user && user.user && (
                    <div className="dropdown-content glass-card rounded-xl shadow-neo-lg overflow-hidden border border-gray-200/20 dark:border-gray-700/30 block opacity-100 transform-none">
                      <div className="p-4 border-b border-gray-200/20 dark:border-gray-700/30">
                        <p className="font-medium text-sm text-gray-800 dark:text-gray-200">{user.user.username}</p>
                        <p className="text-xs text-gray-600 dark:text-gray-300">{user.user.email}</p>
                      </div>
                      
                      <div className="p-2">
                        <Link to="/settings" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-cyan" onClick={() => setDropdownOpen(false)}>
                          <svg className="w-5 h-5 text-neo-cyan/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                          </svg>
                          <span>Settings</span>
                        </Link>
                        <Link to="/profile" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-purple" onClick={() => setDropdownOpen(false)}>
                          <svg className="w-5 h-5 text-neo-purple/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                          </svg>
                          <span>My Profile</span>
                        </Link>
                        <Link to="/badges" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-amber" onClick={() => setDropdownOpen(false)}>
                          <svg className="w-5 h-5 text-neo-amber/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                          </svg>
                          <span>Trader Badges</span>
                        </Link>
                        <Link to="/transactions" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-neo-blue" onClick={() => setDropdownOpen(false)}>
                          <svg className="w-5 h-5 text-neo-blue/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                          </svg>
                          <span>Transaction History</span>
                        </Link>
                        {user.is_dev && (
                          <Link to="/dev" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-green-500" onClick={() => setDropdownOpen(false)}>
                            <svg className="w-5 h-5 text-green-500/70" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                            </svg>
                            <span>Dev Center</span>
                          </Link>
                        )}
                      </div>
                      
                      <div className="p-2 border-t border-gray-200/10 dark:border-gray-700/20">
                        <a href="#" className="dropdown-item flex items-center space-x-3 p-2 rounded-lg text-sm font-medium text-neo-red hover:bg-neo-red/5" onClick={(e) => { e.preventDefault(); handleLogout(); setDropdownOpen(false); }}>
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
                  onClick={() => navigate('/login')}
                  className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-neo-blue/10 text-neo-blue border border-neo-blue/20 hover:bg-neo-blue hover:text-white transition-all duration-300 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path>
                  </svg>
                  Login
                </button>
                <button 
                  className="neo-button rounded-lg px-4 py-2 text-sm font-medium bg-neo-emerald/10 text-neo-emerald border border-neo-emerald/20 hover:bg-neo-emerald hover:text-white transition-all duration-300 flex items-center"
                  onClick={() => navigate('/register')}
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"></path>
                  </svg>
                  Register
                </button>
              </>
            )}
            
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
        
        {mobileMenuOpen && (
          <div className="glass-card m-2 p-2 rounded-xl shadow-glass">
            {user ? (
              <>
                <Link to="/dashboard" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Dashboard</Link>
                <Link to="/trade" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Trade</Link>
                <Link to="/casino" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Casino</Link>
                <Link to="/news" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>News</Link>
                <Link to="/social" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Social</Link>
                { user.user && (
                    <>
                        <Link to="/profile" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>My Profile</Link>
                        <Link to="/settings" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Settings</Link>
                    </>
                )}
                <button 
                  onClick={() => { handleLogout(); setMobileMenuOpen(false); }}
                  className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-500 hover:bg-red-500/20"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Login</Link>
                <Link to="/register" className="block px-3 py-2 rounded-md text-base font-medium hover:bg-neo-purple/20" onClick={() => setMobileMenuOpen(false)}>Register</Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default TopNavBar;
