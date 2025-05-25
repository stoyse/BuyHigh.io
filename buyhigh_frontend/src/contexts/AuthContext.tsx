import React, { createContext, useState, useContext, useEffect } from 'react';
import { loginUser, logoutUser, loginWithGoogleToken } from '../apiService'; // Import loginWithGoogleToken
import axios from 'axios';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  loginWithGoogle: (idToken: string) => Promise<boolean>; // Added loginWithGoogle
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuthStatus = () => {
      const storedUser = localStorage.getItem('user');
      const storedToken = localStorage.getItem('authToken');
      if (storedUser && storedToken) {
        try {
          const parsedUser = JSON.parse(storedUser);
          setUser(parsedUser);
          setToken(storedToken); 
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          setIsAuthenticated(true);
        } catch (e) {
          console.error("Failed to parse stored user:", e);
          // Clear invalid stored data
          localStorage.removeItem('user');
          localStorage.removeItem('authToken');
        }
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
        let emailFromToken = email; // Fallback to input email
        try {
          const payloadBase64Url = response.id_token.split('.')[1];
          if (payloadBase64Url) {
            let payloadBase64 = payloadBase64Url.replace(/-/g, '+').replace(/_/g, '/');
            // Add padding if necessary
            switch (payloadBase64.length % 4) {
              case 2: payloadBase64 += '=='; break;
              case 3: payloadBase64 += '='; break;
            }
            const decodedPayload = JSON.parse(atob(payloadBase64));
            emailFromToken = decodedPayload.email || email;
          }
        } catch (e) {
          console.error("Failed to decode token or get email from token:", e);
          // Keep using the input email as a fallback
        }

        const userData = { 
          id: response.userId, // local DB ID
          firebase_uid: response.firebase_uid, // Firebase UID
          email: emailFromToken
        };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.id_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.id_token}`;
        
        setUser(userData);
        setToken(response.id_token);
        setIsAuthenticated(true);
        return true;
      }
      if (response.success) {
        console.warn("Login successful but no id_token received.");
        const userData = { email, id: response.userId };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.removeItem('authToken'); 
        delete axios.defaults.headers.common['Authorization'];
        
        setUser(userData);
        setToken(null);
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
      setToken(null);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (idToken: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await loginWithGoogleToken(idToken); // Call apiService function

      if (response.success && response.id_token) {
        // Backend's /auth/google-login returns: userId, firebase_uid, email, username, id_token
        // LoginResponse already defines these fields directly.
        const userData = {
          id: response.userId, 
          firebase_uid: response.firebase_uid,
          email: response.email, // Directly from response
        };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.id_token); 
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.id_token}`;
        
        setUser(userData);
        setToken(response.id_token);
        setIsAuthenticated(true);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Google Login failed in AuthContext:', error);
      localStorage.removeItem('user');
      localStorage.removeItem('authToken');
      delete axios.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      setUser(null);
      setToken(null);
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
      setToken(null);
      setIsAuthenticated(false);
    }
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, token, login, loginWithGoogle, logout, loading }}>
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
