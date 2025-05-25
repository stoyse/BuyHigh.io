import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/Login/LoginPage';
import Dashboard from './pages/Dashboard/Dashboard';
import TestPage from './pages/TestPage/TestPage';
import Home from './pages/Home/Home';
import Casino from './pages/Casino';
import Trade from './pages/Trade/Trade';
import NewsPage from './pages/News/NewsPage'; // Import der NewsPage Komponente
import { frontendLogger } from './frontendLogger';
// Import other pages as needed

function App() {
  useEffect(() => {
    frontendLogger.info('Frontend-App gestartet', {
      time: new Date().toISOString(),
      userAgent: navigator.userAgent,
    });
  }, []);

  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/test" 
            element={
              <ProtectedRoute>
                <TestPage />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
          />
          <Route path="/casino" element={
            <ProtectedRoute>
              <Casino />
            </ProtectedRoute>
          } />
          <Route path="/trade" element={
            <ProtectedRoute>
              <Trade />
            </ProtectedRoute>
          } />
          <Route path="/news" element={
            <ProtectedRoute>
            <NewsPage />
            </ProtectedRoute>} />
          {/* Add more routes as needed */}
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
