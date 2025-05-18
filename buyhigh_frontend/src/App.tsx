import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Casino from './pages/Casino';
import Home from './pages/Home';

function App() {
  // Dark Mode Zustand
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true' || 
           window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  // Dark Mode-Effekt
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  return (
    <Router>
      <Routes>
        <Route path="/casino" element={<Casino />} />
        <Route path="/" element={<Home />} />
      </Routes>
    </Router>
  );
}

export default App;
