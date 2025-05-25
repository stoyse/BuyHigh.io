import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { GoogleOAuthProvider } from '@react-oauth/google';

const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

if (!googleClientId) {
  console.error("REACT_APP_GOOGLE_CLIENT_ID is not set. Google OAuth will not work.");
  // Optional: Du könntest hier eine deutlichere Fehlermeldung im UI anzeigen oder die App blockieren.
}

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    {googleClientId ? (
      <GoogleOAuthProvider clientId={googleClientId}>
        <App />
      </GoogleOAuthProvider>
    ) : (
      // Fallback-UI oder Fehlermeldung, wenn die ClientID nicht vorhanden ist
      <div>
        <h1>Configuration Error</h1>
        <p>Google Client ID is missing. Please contact support.</p>
      </div>
    )}
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
