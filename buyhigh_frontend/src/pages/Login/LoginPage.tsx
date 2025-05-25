import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { frontendLogger } from '../../frontendLogger';
import BaseLayout from '../../components/Layout/BaseLayout';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';

const GOOGLE_REDIRECT_URI = process.env.REACT_APP_GOOGLE_REDIRECT_URI || 'http://localhost:3000';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loginWithGoogle, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const from = location.state?.from?.pathname || '/dashboard';

  useEffect(() => {
    if (!process.env.REACT_APP_GOOGLE_REDIRECT_URI) {
      console.warn('REACT_APP_GOOGLE_REDIRECT_URI is not set. Defaulting to http://localhost:3000');
    }
  }, []);

  // Ensure the environment variable is logged for debugging purposes
  frontendLogger.info('Google Redirect URI', { redirectUri: process.env.REACT_APP_GOOGLE_REDIRECT_URI || 'http://localhost:3000' });

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

  const handleGoogleLoginSuccess = async (credentialResponse: CredentialResponse) => {
    setError('');
    frontendLogger.info('Google login attempt');
    if (credentialResponse.credential) {
      try {
        const success = await loginWithGoogle(credentialResponse.credential);
        if (success) {
          frontendLogger.info('Google login successful, redirecting to dashboard');
          navigate('/dashboard', { replace: true });
        } else {
          setError('Google login failed. Please try again.');
          frontendLogger.warn('Google login failed: backend or token issue');
        }
      } catch (err) {
        setError('An error occurred during Google login. Please try again.');
        frontendLogger.error('Google login error', { error: err instanceof Error ? err.message : String(err) });
        console.error('Google login error:', err);
      }
    } else {
      setError('Google login failed: No credential received.');
      frontendLogger.warn('Google login failed: no credential');
    }
  };

  const handleGoogleLoginError = () => {
    setError('Google login failed. Please ensure pop-ups are enabled and try again.');
    frontendLogger.error('Google login error: onError callback triggered');
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
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
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

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300 dark:border-gray-600" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-background-light dark:bg-background-dark text-gray-500 dark:text-gray-400">
                  Or continue with
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-3">
              <div>
                <GoogleLogin
                  onSuccess={handleGoogleLoginSuccess}
                  onError={handleGoogleLoginError}
                  useOneTap
                  theme="outline"
                  size="large"
                  width="100%"
                  containerProps={{ style: { width: '100%' } }}
                />
              </div>
            </div>
          </div>

          <div className="text-sm text-center mt-6">
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
