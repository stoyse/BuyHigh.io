import React, { useEffect, useState } from 'react';
import {
  loginUser,
  fetchFunnyTips,
  GetUserInfo,
  GetPortfolioData,
  GetRecentTransactions,
  GetDailyQuiz,
  GetAssets,
  GetStockData,
  BuyStock,
  SellStock
} from '../../apiService';

interface ApiTestResult {
  name: string;
  data: any;
  loading: boolean;
  error: string | null;
}

const TestPage: React.FC = () => {
  // Ein Zustand für jede API-Abfrage
  const [apiResults, setApiResults] = useState<{ [key: string]: ApiTestResult }>({
    funnyTips: { name: 'Lustige Tipps', data: null, loading: false, error: null },
    userInfo: { name: 'Benutzerinfo', data: null, loading: false, error: null },
    portfolioData: { name: 'Portfolio', data: null, loading: false, error: null },
    transactions: { name: 'Transaktionen', data: null, loading: false, error: null },
    dailyQuiz: { name: 'Tägliches Quiz', data: null, loading: false, error: null },
    assets: { name: 'Vermögenswerte', data: null, loading: false, error: null },
    stockData: { name: 'Aktiendaten (AAPL)', data: null, loading: false, error: null }
  });

  // Login-Felder
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loginResult, setLoginResult] = useState<any>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggedInUserId, setLoggedInUserId] = useState<string | null>(null);

  // Aktien kaufen/verkaufen Felder
  const [symbol, setSymbol] = useState<string>('AAPL');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(150);
  const [tradeResult, setTradeResult] = useState<any>(null);
  const [tradeError, setTradeError] = useState<string | null>(null);

  // API-Abfrage-Funktion
  const fetchApiData = async (key: string, fetchFunction: () => Promise<any>) => {
    setApiResults(prev => ({
      ...prev,
      [key]: { ...prev[key], loading: true, error: null }
    }));

    try {
      const data = await fetchFunction();
      setApiResults(prev => ({
        ...prev,
        [key]: { ...prev[key], data, loading: false }
      }));
    } catch (err: any) {
      setApiResults(prev => ({
        ...prev,
        [key]: { ...prev[key], loading: false, error: err.message || 'Ein Fehler ist aufgetreten' }
      }));
    }
  };

  // Beim Laden der Seite die GET-Anfragen ausführen, die keine Benutzer-ID benötigen
  useEffect(() => {
    fetchApiData('funnyTips', () => fetchFunnyTips());
    fetchApiData('dailyQuiz', () => GetDailyQuiz());
    fetchApiData('assets', () => GetAssets());
    fetchApiData('stockData', () => GetStockData('AAPL', '1d'));
  }, []);

  // Benutzer-spezifische Daten abrufen, wenn loggedInUserId verfügbar ist
  useEffect(() => {
    if (loggedInUserId) {
      fetchApiData('userInfo', () => GetUserInfo(loggedInUserId));
      fetchApiData('portfolioData', () => GetPortfolioData(loggedInUserId));
      fetchApiData('transactions', () => GetRecentTransactions(loggedInUserId));
    }
  }, [loggedInUserId]);

  // Login-Funktion
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginResult(null);
    setLoginError(null);
    setLoggedInUserId(null); // Reset user ID on new login attempt
    
    try {
      const result = await loginUser(email, password);
      setLoginResult(result);
      if (result && result.success && result.userId) {
        setLoggedInUserId(result.userId.toString()); // Store user ID from login response
      } else if (result && !result.success) {
        setLoginError(result.message || 'Login fehlgeschlagen');
      }
    } catch (err: any) {
      setLoginError(err.message || 'Login fehlgeschlagen');
    }
  };

  // Aktie kaufen
  const handleBuyStock = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeResult(null);
    setTradeError(null);
    
    try {
      const result = await BuyStock(symbol, quantity, price);
      setTradeResult({ action: 'Kauf', ...result });
    } catch (err: any) {
      setTradeError(`Kauf fehlgeschlagen: ${err.message}`);
    }
  };

  // Aktie verkaufen
  const handleSellStock = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeResult(null);
    setTradeError(null);
    
    try {
      const result = await SellStock(symbol, quantity, price);
      setTradeResult({ action: 'Verkauf', ...result });
    } catch (err: any) {
      setTradeError(`Verkauf fehlgeschlagen: ${err.message}`);
    }
  };

  // Render-Funktion für ein API-Ergebnis
  const renderApiResult = (key: string, result: ApiTestResult) => (
    <div key={key} className="api-result">
      <h3>{result.name}</h3>
      {result.loading ? (
        <p>Lädt...</p>
      ) : result.error ? (
        <div className="error">{result.error}</div>
      ) : (
        <pre className="json-result">{JSON.stringify(result.data, null, 2)}</pre>
      )}
    </div>
  );

  return (
    <div className="test-page">
      <h1>API Test Dashboard</h1>

      <div className="test-section">
        <h2>Login-Test</h2>
        <form onSubmit={handleLogin} className="test-form">
          <div className="form-group">
            <label>E-Mail:</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
            />
          </div>
          <div className="form-group">
            <label>Passwort:</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
            />
          </div>
          <button type="submit">Login</button>
        </form>
        
        {loginResult && (
          <div className="result-section">
            <h3>Login-Ergebnis:</h3>
            <pre>{JSON.stringify(loginResult, null, 2)}</pre>
          </div>
        )}
        
        {loginError && <div className="error">{loginError}</div>}
      </div>

      <div className="test-section">
        <h2>Handel-Test</h2>
        <form className="test-form">
          <div className="form-group">
            <label>Symbol:</label>
            <input 
              type="text" 
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value)} 
              required 
            />
          </div>
          <div className="form-group">
            <label>Menge:</label>
            <input 
              type="number" 
              value={quantity} 
              onChange={(e) => setQuantity(Number(e.target.value))} 
              required 
              min="1" 
            />
          </div>
          <div className="form-group">
            <label>Preis:</label>
            <input 
              type="number" 
              value={price} 
              onChange={(e) => setPrice(Number(e.target.value))} 
              required 
              step="0.01"
              min="0.01" 
            />
          </div>
          <div className="button-group">
            <button type="button" onClick={handleBuyStock}>Kaufen</button>
            <button type="button" onClick={handleSellStock}>Verkaufen</button>
          </div>
        </form>
        
        {tradeResult && (
          <div className="result-section">
            <h3>Handel-Ergebnis:</h3>
            <pre>{JSON.stringify(tradeResult, null, 2)}</pre>
          </div>
        )}
        
        {tradeError && <div className="error">{tradeError}</div>}
      </div>

      <div className="api-results">
        <h2>GET API Abfrageergebnisse</h2>
        {Object.entries(apiResults).map(([key, result]) => renderApiResult(key, result))}
      </div>

      <style>{`
        .test-page {
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
          font-family: Arial, sans-serif;
        }
        
        .test-section {
          margin-bottom: 30px;
          padding: 20px;
          border: 1px solid #ddd;
          border-radius: 8px;
          background-color: #f9f9f9;
        }
        
        .test-form {
          display: flex;
          flex-direction: column;
          gap: 15px;
          margin-bottom: 20px;
        }
        
        .form-group {
          display: flex;
          align-items: center;
        }
        
        .form-group label {
          width: 100px;
          text-align: right;
          margin-right: 15px;
        }
        
        .form-group input {
          flex: 1;
          padding: 8px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }
        
        .button-group {
          display: flex;
          gap: 10px;
        }
        
        button {
          padding: 8px 16px;
          background-color: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        
        button:hover {
          background-color: #45a049;
        }
        
        .button-group button:nth-child(2) {
          background-color: #f44336;
        }
        
        .button-group button:nth-child(2):hover {
          background-color: #d32f2f;
        }
        
        .error {
          color: #d32f2f;
          background-color: #ffebee;
          padding: 10px;
          border-radius: 4px;
          margin-top: 10px;
        }
        
        .api-results {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        
        .api-result {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 15px;
          background-color: #f9f9f9;
        }
        
        .json-result {
          background-color: #f5f5f5;
          padding: 10px;
          border-radius: 4px;
          overflow: auto;
          max-height: 300px;
          font-size: 12px;
        }
        
        @media (max-width: 768px) {
          .api-results {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default TestPage;
