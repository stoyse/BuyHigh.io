import { 
  fetchFunnyTips, 
  GetUserInfo, 
  GetPortfolioData, 
  GetRecentTransactions, 
  loginUser, 
  BuyStock, 
  SellStock,
  GetDailyQuiz,
  SubmitDailyQuizAnswer,
  DailyQuizAttemptPayload,
  DailyQuizAttemptResponse,
  GetAssets,
  GetStockData,
  CoinFlipRequestData,
  recordCoinFlip,
  CoinFlipResponseData,
  callChatbotApi, // Import the new chatbot API function
} from '../../apiService';
import TopNavBar from '../../components/Navbar/TopNavBar';
import './TestPage.css';
import React, { useState, useEffect } from 'react';

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

  // Coin Flip fields
  const [coinFlipSuccess, setCoinFlipSuccess] = useState<boolean>(true);
  const [coinFlipBet, setCoinFlipBet] = useState<number>(10);
  const [coinFlipProfit, setCoinFlipProfit] = useState<number>(5);
  const [coinFlipResult, setCoinFlipResult] = useState<CoinFlipResponseData | null>(null);
  const [coinFlipError, setCoinFlipError] = useState<string | null>(null);
  const [coinFlipLoading, setCoinFlipLoading] = useState<boolean>(false);

  // Chatbot fields
  const [chatbotPrompt, setChatbotPrompt] = useState<string>('What are the risks of options trading?');
  const [chatbotResult, setChatbotResult] = useState<any>(null);
  const [chatbotError, setChatbotError] = useState<string | null>(null);
  const [chatbotLoading, setChatbotLoading] = useState<boolean>(false);

  // Props for TopNavBar
  const [user, setUser] = useState<any>(null); // Mock user, replace with actual user state
  const [darkMode, setDarkMode] = useState<boolean>(false);

  const handleLogout = () => {
    // Implement logout logic
    setUser(null);
    console.log("User logged out");
  };

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

  // Handle Chatbot API call
  const handleChatbotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setChatbotResult(null);
    setChatbotError(null);
    setChatbotLoading(true);

    if (!loggedInUserId) {
      setChatbotError("Please login first to use the chatbot.");
      setChatbotLoading(false);
      return;
    }

    try {
      const result = await callChatbotApi(chatbotPrompt);
      setChatbotResult(result);
    } catch (err: any) {
      setChatbotError(`Chatbot request failed: ${err.message}`);
    } finally {
      setChatbotLoading(false);
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

  // Handle Coin Flip Submission
  const handleCoinFlipSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCoinFlipResult(null);
    setCoinFlipError(null);
    setCoinFlipLoading(true);

    if (!loggedInUserId) {
      setCoinFlipError("Please login first to record coin flip.");
      setCoinFlipLoading(false);
      return;
    }

    try {
      const payload: CoinFlipRequestData = { 
        Success: coinFlipSuccess, 
        bet: coinFlipBet,
        profit: coinFlipProfit
      };
      const result = await recordCoinFlip(payload);
      setCoinFlipResult(result);
    } catch (err: any) {
      setCoinFlipError(err.message || 'An error occurred during coin flip recording.');
    } finally {
      setCoinFlipLoading(false);
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
      <TopNavBar user={user} handleLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} />
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

      <div className="test-section">
        <h2>Coin Flip Test</h2>
        <form onSubmit={handleCoinFlipSubmit} className="test-form">
          <div className="form-group">
            <label>Success:</label>
            <select 
              value={coinFlipSuccess ? 'true' : 'false'} 
              onChange={(e) => setCoinFlipSuccess(e.target.value === 'true')}
              required
            >
              <option value="true">True</option>
              <option value="false">False</option>
            </select>
          </div>
          <div className="form-group">
            <label>Bet:</label>
            <input 
              type="number" 
              value={coinFlipBet} 
              onChange={(e) => setCoinFlipBet(Number(e.target.value))} 
              required 
              min="1" 
            />
          </div>
          <div className="form-group">
            <label>Profit:</label>
            <input 
              type="number" 
              value={coinFlipProfit} 
              onChange={(e) => setCoinFlipProfit(Number(e.target.value))} 
              required 
              step="0.01"
              min="0.01" 
            />
          </div>
          <button type="submit" disabled={coinFlipLoading}>
            {coinFlipLoading ? 'Recording...' : 'Record Coin Flip'}
          </button>
        </form>
        
        {coinFlipResult && (
          <div className="result-section">
            <h3>Coin Flip Result:</h3>
            <pre>{JSON.stringify(coinFlipResult, null, 2)}</pre>
          </div>
        )}
        
        {coinFlipError && <div className="error">{coinFlipError}</div>}
      </div>

      <div className="api-test-section">
        {/* Chatbot API Test */}
        <div className="api-test-form">
          <h3>Chatbot API Test</h3>
          <form onSubmit={handleChatbotSubmit}>
            <div>
              <label>Prompt:</label>
              <input 
                type="text" 
                value={chatbotPrompt} 
                onChange={(e) => setChatbotPrompt(e.target.value)} 
                placeholder="Enter your prompt"
              />
            </div>
            <button type="submit" disabled={chatbotLoading || !loggedInUserId}>
              {chatbotLoading ? 'Loading...' : 'Send to Chatbot'}
            </button>
            {!loggedInUserId && <p style={{ color: 'orange', fontSize: '12px' }}>Login required to use chatbot.</p>}
          </form>
          {chatbotError && <div className="error-message">{chatbotError}</div>}
          {chatbotResult && (
            <div className="api-result">
              <h4>Chatbot Response:</h4>
              <pre>{JSON.stringify(chatbotResult, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* Daily Quiz Attempt */}
        <div className="api-test-form">
          <h3>Daily Quiz Attempt</h3>
          <form onSubmit={handleQuizAttemptSubmit}>
            <div>
              <label>Quiz ID:</label>
              <input 
                type="text" 
                value={quizIdForAttempt} 
                onChange={(e) => setQuizIdForAttempt(e.target.value)} 
                placeholder="Enter Quiz ID"
                required
              />
            </div>
            <div>
              <label>Your Answer:</label>
              <input 
                type="text" 
                value={selectedAnswerForAttempt} 
                onChange={(e) => setSelectedAnswerForAttempt(e.target.value)} 
                placeholder="Enter your answer"
                required
              />
            </div>
            <button type="submit" disabled={quizAttemptLoading}>
              {quizAttemptLoading ? 'Submitting...' : 'Submit Answer'}
            </button>
          </form>
          {quizAttemptError && <div className="error-message">{quizAttemptError}</div>}
          {quizAttemptResult && (
            <div className="api-result">
              <h4>Quiz Attempt Result:</h4>
              <pre>{JSON.stringify(quizAttemptResult, null, 2)}</pre>
            </div>
          )}
        </div>
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
        
        .form-group input, .form-group select {
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
