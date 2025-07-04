import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/Login/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage_old'; // Import RegisterPage
import Dashboard from './pages/Dashboard/Dashboard';
import TestPage from './pages/TestPage/TestPage';
import Home from './pages/Home/Home';
import Casino from './pages/Casino';
import Trade from './pages/Trade/Trade';
import NewsPage from './pages/News/NewsPage';
import CoinFlipGame from './pages/CoinFlip/CoinFlipGame';
import SlotsGame from './pages/Slots/SlotsGame';
import { frontendLogger } from './frontendLogger';
// Import other pages as needed
import SocialPage from './pages/SocialPage/SocialPage'; // Import SocialPage
import SettingsPage from './pages/SettingsPage/SettingsPage';
import ProfilePage from './pages/ProfilePage/ProfilePage';
import TraderBadgesPage from './pages/TraderBadges/TraderBadgesPage';
import TransactionsPage from './pages/TransactionsPage/TransactionsPage';
import ChatbotPage from './pages/Chatbot/ChatbotPage';
import MrStonksPage from './pages/MrStonksPage/MrStonksPage';
function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} /> 
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
          <Route path="/coinflip" element={
            <ProtectedRoute>
              <CoinFlipGame />
            </ProtectedRoute>
          } />
          <Route path="/slots" element={
            <ProtectedRoute>
              <SlotsGame />
            </ProtectedRoute>
          } />
          <Route path="/social" element={
            <ProtectedRoute>
              <SocialPage />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          } />
          <Route path="/profile" element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          } />
          <Route path="/badges" element={
            <ProtectedRoute>
              <TraderBadgesPage />
            </ProtectedRoute>
          } />
          <Route path="/transactions" element={
            <ProtectedRoute>
              <TransactionsPage />
            </ProtectedRoute>
          } />
          <Route path="/mr-stonks" element={
            <ProtectedRoute>
              <MrStonksPage />
            </ProtectedRoute>
          } />
          <Route path="/chatbot" element={
            <ProtectedRoute>
              <ChatbotPage />
            </ProtectedRoute>
          } />
          {/* Redirect all other paths to the home page */}
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
