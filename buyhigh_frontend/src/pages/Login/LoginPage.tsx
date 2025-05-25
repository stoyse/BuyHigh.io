import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { frontendLogger } from '../../frontendLogger';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the redirect path from location state or default to dashboard
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
    <div className="login-container">
      <div className="login-card">
        <h2 className="login-title">Login to BuyHigh.io</h2>
        {error && <div className="login-error">{error}</div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
              required
            />
          </div>
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Don't have an account yet?{' '}
            <button 
              onClick={() => navigate('/register')} 
              className="font-medium text-neo-amber hover:text-neo-amber-dark"
            >
              Sign up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
