import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { frontendLogger } from '../../frontendLogger';
import BaseLayout from '../../components/Layout/BaseLayout';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    frontendLogger.info('Login attempt', { email });

    if (!email || !password) {
      setError('Please enter both email and password');
      frontendLogger.warn('Login failed: fields empty', { email });
      return;
    }
    
    try {
      const success = await login(email, password);
      if (success) {
        frontendLogger.info('Login successful', { email });
        navigate(from, { replace: true });
      } else {
        setError('Invalid email or password');
        frontendLogger.warn('Login failed: wrong credentials', { email });
      }
    } catch (err) {
      setError('An error occurred during login. Please try again.');
      frontendLogger.error('Login error', { email, error: err instanceof Error ? err.message : String(err) });
      console.error('Login error:', err);
    }
  };

  return (
    <BaseLayout title="Login - BuyHigh.io">
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background-light via-background-light to-background-accent-light dark:from-background-dark dark:via-background-dark dark:to-background-accent-dark py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 glass-card shadow-neo-lg border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-8 md:p-10">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold gradient-text">
              Sign in to your Account
            </h2>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                <strong className="font-bold">Error: </strong>
                <span className="block sm:inline">{error}</span>
              </div>
            )}
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="email-address" className="sr-only">
                  Email address
                </label>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white/5 dark:bg-gray-800/40 rounded-t-md focus:outline-none focus:ring-neo-amber focus:border-neo-amber focus:z-10 sm:text-sm"
                  placeholder="Email address"
                />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white/5 dark:bg-gray-800/40 rounded-b-md focus:outline-none focus:ring-neo-amber focus:border-neo-amber focus:z-10 sm:text-sm"
                  placeholder="Password"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-neo-amber hover:bg-neo-amber-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neo-amber-dark disabled:opacity-50 transition-colors duration-150 ease-in-out"
              >
                {loading ? (
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  'Sign In'
                )}
              </button>
            </div>
          </form>
          <div className="text-sm text-center">
            <p className="text-gray-600 dark:text-gray-400">
              Don't have an account yet?{' '}
              <button 
                onClick={() => navigate('/register')} 
                className="font-medium text-neo-amber hover:text-neo-amber-dark ml-1"
                disabled={loading}
              >
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default LoginPage;
