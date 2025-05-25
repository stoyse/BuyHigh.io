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
  SellStock,
  SubmitDailyQuizAnswer,
  DailyQuizAttemptPayload,
  DailyQuizAttemptResponse
} from '../../apiService';

interface ApiTestResult {
  name: string;
  data: any;
  loading: boolean;
  error: string | null;
  url?: string;
}

const TestPage: React.FC = () => {
  // A state for each API query
  const [apiResults, setApiResults] = useState<{ [key: string]: ApiTestResult }>({
    funnyTips: { name: 'Funny Tips', data: null, loading: false, error: null },
    userInfo: { name: 'User Info', data: null, loading: false, error: null },
    portfolioData: { name: 'Portfolio', data: null, loading: false, error: null },
    transactions: { name: 'Transactions', data: null, loading: false, error: null },
    dailyQuiz: { name: 'Daily Quiz', data: null, loading: false, error: null },
    assets: { name: 'Assets', data: null, loading: false, error: null },
    stockData: { name: 'Stock Data (AAPL)', data: null, loading: false, error: null }
  });

  // Login fields
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [loginResult, setLoginResult] = useState<any>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggedInUserId, setLoggedInUserId] = useState<string | null>(null);

  // Buy/Sell stock fields
  const [symbol, setSymbol] = useState<string>('AAPL');
  const [quantity, setQuantity] = useState<number>(1);
  const [price, setPrice] = useState<number>(150);
  const [tradeResult, setTradeResult] = useState<any>(null);
  const [tradeError, setTradeError] = useState<string | null>(null);

  // Daily Quiz Attempt fields
  const [quizIdForAttempt, setQuizIdForAttempt] = useState<string>('');
  const [selectedAnswerForAttempt, setSelectedAnswerForAttempt] = useState<string>('');
  const [quizAttemptResult, setQuizAttemptResult] = useState<DailyQuizAttemptResponse | null>(null);
  const [quizAttemptError, setQuizAttemptError] = useState<string | null>(null);
  const [quizAttemptLoading, setQuizAttemptLoading] = useState<boolean>(false);

  // API query function
  const fetchApiData = async (key: string, fetchFunction: () => Promise<any>, url: string) => {
    setApiResults(prev => ({
      ...prev,
      [key]: { ...prev[key], loading: true, error: null, url } // Save the URL
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
        [key]: { ...prev[key], loading: false, error: err.message || 'An error occurred' }
      }));
    }
  };

  // Execute GET requests that do not require a user ID when the page loads
  useEffect(() => {
    fetchApiData('funnyTips', () => fetchFunnyTips(), 'https://api.stoyse.hackclub.app/funny-tips');
    fetchApiData('dailyQuiz', () => GetDailyQuiz(), 'https://api.stoyse.hackclub.app/education/daily-quiz');
    fetchApiData('assets', () => GetAssets(), 'https://api.stoyse.hackclub.app/assets');
    fetchApiData('stockData', () => GetStockData('AAPL', '1d'), 'https://api.stoyse.hackclub.app/stock-data?symbol=AAPL&range=1d');
  }, []);

  // Fetch user-specific data when loggedInUserId is available
  useEffect(() => {
    if (loggedInUserId) {
      fetchApiData('userInfo', () => GetUserInfo(loggedInUserId), `https://api.stoyse.hackclub.app/user/${loggedInUserId}`);
      fetchApiData('portfolioData', () => GetPortfolioData(loggedInUserId), `https://api.stoyse.hackclub.app/user/portfolio/${loggedInUserId}`);
      fetchApiData('transactions', () => GetRecentTransactions(loggedInUserId), `https://api.stoyse.hackclub.app/user/transactions/${loggedInUserId}`);
    }
  }, [loggedInUserId]);

  // Login function
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
        setLoginError(result.message || 'Login failed');
      }
    } catch (err: any) {
      setLoginError(err.message || 'Login failed');
    }
  };

  // Buy stock
  const handleBuyStock = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeResult(null);
    setTradeError(null);
    
    try {
      const result = await BuyStock(symbol, quantity, price);
      setTradeResult({ action: 'Buy', ...result });
    } catch (err: any) {
      setTradeError(`Buy failed: ${err.message}`);
    }
  };

  // Sell stock
  const handleSellStock = async (e: React.FormEvent) => {
    e.preventDefault();
    setTradeResult(null);
    setTradeError(null);
    
    try {
      const result = await SellStock(symbol, quantity, price);
      setTradeResult({ action: 'Sell', ...result });
    } catch (err: any) {
      setTradeError(`Sell failed: ${err.message}`);
    }
  };

  // Handle Daily Quiz Attempt Submission
  const handleQuizAttemptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuizAttemptResult(null);
    setQuizAttemptError(null);
    setQuizAttemptLoading(true);

    if (!loggedInUserId) {
      setQuizAttemptError("Please login first to attempt the quiz.");
      setQuizAttemptLoading(false);
      return;
    }
    if (!quizIdForAttempt.trim() || !selectedAnswerForAttempt.trim()) {
        setQuizAttemptError("Quiz ID and Answer cannot be empty.");
        setQuizAttemptLoading(false);
        return;
    }

    try {
      const payload: DailyQuizAttemptPayload = { 
        quiz_id: quizIdForAttempt, 
        selected_answer: selectedAnswerForAttempt 
      };
      const result = await SubmitDailyQuizAnswer(payload);
      setQuizAttemptResult(result);
      if (!result.success) {
        setQuizAttemptError(result.message || "Quiz submission failed.");
      }
    } catch (err: any) {
      setQuizAttemptError(err.message || 'An error occurred during quiz submission.');
    } finally {
      setQuizAttemptLoading(false);
    }
  };

  // Render function for an API result
  const renderApiResult = (key: string, result: ApiTestResult) => (
    <div key={key} className="api-result">
      <h3>{result.name}</h3>
      {result.url && <p><strong>URL:</strong> {result.url}</p>} {/* Show the URL */}
      {result.loading ? (
        <p>Loading...</p>
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
        <h2>Login Test</h2>
        <form onSubmit={handleLogin} className="test-form">
          <div className="form-group">
            <label>Email:</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
            />
          </div>
          <div className="form-group">
            <label>Password:</label>
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
            <h3>Login Result:</h3>
            <pre>{JSON.stringify(loginResult, null, 2)}</pre>
          </div>
        )}
        
        {loginError && <div className="error">{loginError}</div>}
      </div>

      <div className="test-section">
        <h2>Trade Test</h2>
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
            <label>Quantity:</label>
            <input 
              type="number" 
              value={quantity} 
              onChange={(e) => setQuantity(Number(e.target.value))} 
              required 
              min="1" 
            />
          </div>
          <div className="form-group">
            <label>Price:</label>
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
            <button type="button" onClick={handleBuyStock}>Buy</button>
            <button type="button" onClick={handleSellStock}>Sell</button>
          </div>
        </form>
        
        {tradeResult && (
          <div className="result-section">
            <h3>Trade Result:</h3>
            <pre>{JSON.stringify(tradeResult, null, 2)}</pre>
          </div>
        )}
        
        {tradeError && <div className="error">{tradeError}</div>}
      </div>

      <div className="test-section">
        <h2>Daily Quiz Attempt Test</h2>
        <p>Note: You must be logged in. Get a Quiz ID from the "Daily Quiz" GET request results below.</p>
        <form onSubmit={handleQuizAttemptSubmit} className="test-form">
          <div className="form-group">
            <label htmlFor="quizIdAttempt">Quiz ID:</label>
            <input 
              id="quizIdAttempt"
              type="text" 
              value={quizIdForAttempt} 
              onChange={(e) => setQuizIdForAttempt(e.target.value)} 
              placeholder="Enter Quiz ID (e.g., from GET /daily-quiz)"
              required 
            />
          </div>
          <div className="form-group">
            <label htmlFor="selectedAnswerAttempt">Your Answer:</label>
            <input 
              id="selectedAnswerAttempt"
              type="text" 
              value={selectedAnswerForAttempt} 
              onChange={(e) => setSelectedAnswerForAttempt(e.target.value)} 
              placeholder="Enter your selected answer"
              required 
            />
          </div>
          <button type="submit" disabled={quizAttemptLoading}>
            {quizAttemptLoading ? 'Submitting...' : 'Submit Quiz Answer'}
          </button>
        </form>
        
        {quizAttemptLoading && <p>Loading...</p>}
        
        {quizAttemptResult && (
          <div className="result-section">
            <h4>Quiz Attempt Result:</h4>
            <pre className="json-result">{JSON.stringify(quizAttemptResult, null, 2)}</pre>
          </div>
        )}
        
        {quizAttemptError && <div className="error">{quizAttemptError}</div>}
      </div>

      <div className="api-results">
        <h2>GET API Query Results</h2>
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
