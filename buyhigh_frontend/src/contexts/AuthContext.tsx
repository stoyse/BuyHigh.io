import React, { createContext, useState, useContext, useEffect } from 'react';
// Ensure you have firebase initialized and auth imported
// For example, if you have a firebase.ts: import firebase from './firebase';
// Or directly:
import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, signInAnonymously, signOut, Auth, User as FirebaseUser } from 'firebase/auth';

import { loginUser, logoutUser, loginWithGoogleToken, loginAnonymouslyWithFirebase } from '../apiService'; 
import axios from 'axios';

// Firebase configuration loaded from environment variables
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_WEB_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  databaseURL: process.env.REACT_APP_FIREBASE_DATABASE_URL, // Added from .env
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || "YOUR_STORAGE_BUCKET", // Add to .env if needed
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || "YOUR_MESSAGING_SENDER_ID", // Add to .env if needed
  appId: process.env.REACT_APP_FIREBASE_APP_ID || "YOUR_APP_ID" // Add to .env if needed
};

console.log("Firebase Config being used:", firebaseConfig); // DEBUGGING LINE

let app: FirebaseApp;
// Initialize Firebase only if it hasn't been initialized yet
if (getApps().length === 0) {
  app = initializeApp(firebaseConfig);
} else {
  app = getApp();
}

const auth: Auth = getAuth(app);

interface User {
  id: string | number;
  firebase_uid?: string;
  email?: string;
  username?: string;
  isGuest?: boolean;
  firebase_provider?: string; // Add this line
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  loginWithGoogle: (idToken: string) => Promise<boolean>;
  loginAsGuest: () => Promise<boolean>; 
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkAuthStatus = () => {
      const storedUser = localStorage.getItem('user');
      const storedToken = localStorage.getItem('authToken');
      if (storedUser && storedToken) {
        try {
          const parsedUser: User = JSON.parse(storedUser);
          setUser(parsedUser);
          setToken(storedToken);
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          setIsAuthenticated(true);
        } catch (e) {
          console.error("Failed to parse stored user:", e);
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
        let emailFromToken = email; 
        if (response.id_token.split('.').length === 3) { // Check if it's a JWT
          try {
            const payloadBase64Url = response.id_token.split('.')[1];
            let payloadBase64 = payloadBase64Url.replace(/-/g, '+').replace(/_/g, '/');
            switch (payloadBase64.length % 4) {
              case 2: payloadBase64 += '=='; break;
              case 3: payloadBase64 += '='; break;
            }
            const decodedPayload = JSON.parse(atob(payloadBase64));
            emailFromToken = decodedPayload.email || email;
          } catch (e) {
            console.error("Failed to decode token or get email from token:", e);
          }
        }

        const userData: User = { 
          id: response.userId, 
          firebase_uid: response.firebase_uid, 
          email: emailFromToken,
          username: response.username,
          isGuest: response.isGuest || false
        };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.id_token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.id_token}`;
        
        setUser(userData);
        setToken(response.id_token);
        setIsAuthenticated(true);
        return true;
      }
      setIsAuthenticated(false); // Ensure this is set on failure paths
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
      const response = await loginWithGoogleToken(idToken); 

      if (response.success && response.id_token) {
        const userData: User = {
          id: response.userId, 
          firebase_uid: response.firebase_uid,
          email: response.email,
          username: response.username,
          isGuest: response.isGuest || false
        };
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('authToken', response.id_token); 
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.id_token}`;
        
        setUser(userData);
        setToken(response.id_token);
        setIsAuthenticated(true);
        return true;
      }
      setIsAuthenticated(false);
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

  const loginAsGuest = async (): Promise<boolean> => {
    setLoading(true);
    try {
      if (!getApps().length) {
         console.error("Firebase not initialized. Guest login cannot proceed.");
         throw new Error("Firebase not initialized.");
      }

      const firebaseUserCredential = await signInAnonymously(auth);
      if (firebaseUserCredential.user) {
        const idToken = await firebaseUserCredential.user.getIdToken();
        const backendResponse = await loginAnonymouslyWithFirebase(idToken);

        if (backendResponse.success && backendResponse.id_token) {
          const userData: User = {
            id: backendResponse.userId,
            firebase_uid: backendResponse.firebase_uid,
            email: backendResponse.email,
            username: backendResponse.username,
            isGuest: true, 
          };
          localStorage.setItem('user', JSON.stringify(userData));
          localStorage.setItem('authToken', backendResponse.id_token);
          axios.defaults.headers.common['Authorization'] = `Bearer ${backendResponse.id_token}`;
          
          setUser(userData);
          setToken(backendResponse.id_token);
          setIsAuthenticated(true);
          return true;
        } else {
          await signOut(auth);
          throw new Error(backendResponse.message || 'Guest login failed at backend.');
        }
      } else {
        throw new Error('Firebase anonymous sign-in did not return a user.');
      }
    } catch (error) {
      console.error('Guest Login failed:', error);
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
    const currentFirebaseUser: FirebaseUser | null = auth.currentUser;
    try {
      if (currentFirebaseUser) {
        if (currentFirebaseUser.isAnonymous) {
          await signOut(auth);
          console.log("Firebase anonymous user signed out.");
        } else {
          await signOut(auth);
          console.log("Firebase regular user signed out.");
        }
      }
    } catch (error) {
      console.error("Firebase sign-out or API logout failed, proceeding with client-side cleanup:", error);
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
    <AuthContext.Provider value={{ isAuthenticated, user, token, login, loginWithGoogle, loginAsGuest, logout, loading }}>
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
