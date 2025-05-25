import React, { createContext, useState, useContext, useEffect } from 'react';
import { loginUser, logoutUser } from '../apiService';
import axios from 'axios';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  token: string | null; // Added token
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(null); // Added token state
  const [loading, setLoading] = useState<boolean>(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuthStatus = () => {
      const storedUser = localStorage.getItem('user');
      const storedToken = localStorage.getItem('authToken');
      if (storedUser && storedToken) {
        setUser(JSON.parse(storedUser));
        setToken(storedToken); // Set token state
        axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
        setIsAuthenticated(true);
      }
      setLoading(false);
    };

    checkAuthStatus();
  }, []);

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await loginUser(email, password);
      
      if (response.success && response.id_token) {
        const userData = { email, id: response.userId || JSON.parse(atob(response.id_token.split('.')[1])).uid };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.id_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.id_token}`;
        
        setUser(userData);
        setToken(response.id_token); // Set token state
        setIsAuthenticated(true);
        return true;
      }
      if (response.success) {
        console.warn("Login successful but no id_token received.");
        // Assuming if login is successful but no id_token, we might not have a token
        // or it's handled differently. For now, set token to null or handle as per app logic.
        const userData = { email, id: response.userId };
        localStorage.setItem('user', JSON.stringify(userData));
        // If there's no token, ensure it's cleared or handled
        localStorage.removeItem('authToken'); 
        delete axios.defaults.headers.common['Authorization'];
        
        setUser(userData);
        setToken(null); // Explicitly set token to null if not present
        setIsAuthenticated(true);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      localStorage.removeItem('user');
      localStorage.removeItem('authToken');
      delete axios.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      setUser(null);
      setToken(null); // Clear token state on error
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.error("API logout failed, proceeding with client-side cleanup:", error);
    } finally {
      localStorage.removeItem('user');
      localStorage.removeItem('authToken');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
      setToken(null); // Clear token state on logout
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
