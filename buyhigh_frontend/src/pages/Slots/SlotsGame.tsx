import React, { useState, useEffect } from 'react';
import { playSlots, GetUserInfo } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';
import BaseLayout from '../../components/Layout/BaseLayout';
import './SlotsGame.css';

interface GameResult {
  symbols: string[];
  multiplier: number;
  won: boolean;
  bet: number;
  profit: number;
  payout: number;
}

const SlotsGame: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [bet, setBet] = useState<number>(10);
  const [balance, setBalance] = useState<number>(0);
  const [gameResult, setGameResult] = useState<GameResult | null>(null);
  const [isSpinning, setIsSpinning] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Slots symbols with their display values
  const SYMBOL_DISPLAY = {
    "🍒": "Cherry",
    "🍋": "Lemon", 
    "🍊": "Orange",
    "🍇": "Grapes",
    "⭐": "Star",
    "💎": "Diamond"
  };

  const SYMBOL_MULTIPLIERS = {
    "🍒": 2,
    "🍋": 3,
    "🍊": 4, 
    "🍇": 5,
    "⭐": 8,
    "💎": 20
  };

  useEffect(() => {
    const fetchUserBalance = async () => {
      if (isAuthenticated && user?.id) {
        try {
          const userInfo = await GetUserInfo(String(user.id));
          // Handle nested user structure from backend API
          if (userInfo && userInfo.success && userInfo.user && userInfo.user.balance !== undefined) {
            setBalance(userInfo.user.balance);
          } else if (userInfo && userInfo.balance !== undefined) {
            // Fallback for direct balance access
            setBalance(userInfo.balance);
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };
    fetchUserBalance();
  }, [isAuthenticated, user]);

  const handleSpin = async () => {
    if (bet <= 0) {
      setError('Bet must be positive');
      return;
    }

    if (bet > balance) {
      setError('Insufficient balance');
      return;
    }

    setIsLoading(true);
    setIsSpinning(true);
    setError('');
    setMessage('');
    setGameResult(null);

    try {
      const response = await playSlots(bet);
      
      if (response.status === 'success' && response.game_result) {
        // Create a properly typed GameResult object
        const gameResult: GameResult = {
          symbols: response.game_result.symbols,
          multiplier: response.game_result.multiplier,
          won: response.game_result.won,
          bet: bet,
          profit: response.game_result.won ? response.game_result.payout - bet : -bet,
          payout: response.game_result.payout
        };
        
        setGameResult(gameResult);
        setBalance(response.new_balance || balance);
        
        if (gameResult.won) {
          setMessage(`🎉 You won ${gameResult.payout} credits! (${gameResult.multiplier}x multiplier)`);
        } else {
          setMessage(`😢 You lost ${bet} credits. Better luck next time!`);
        }

        // Refresh balance by fetching updated user info
        if (isAuthenticated && user?.id) {
          try {
            const userInfo = await GetUserInfo(String(user.id));
            if (userInfo && userInfo.success && userInfo.user && userInfo.user.balance !== undefined) {
              setBalance(userInfo.user.balance);
            } else if (userInfo && userInfo.balance !== undefined) {
              setBalance(userInfo.balance);
            }
          } catch (refreshError) {
            console.error('Error refreshing user balance:', refreshError);
          }
        }
      } else {
        setError(response.message || 'Game failed');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while playing');
    } finally {
      setIsLoading(false);
      setTimeout(() => setIsSpinning(false), 1000); // Keep spinning animation for a bit
    }
  };

  const handleBetChange = (newBet: number) => {
    setBet(Math.max(1, Math.min(newBet, balance)));
    setError('');
  };

  const setBetPercentage = (percentage: number) => {
    const newBet = Math.floor(balance * percentage);
    handleBetChange(newBet);
  };

  return (
    <BaseLayout title="Slot Machine - BuyHigh.io">
      <div className="slots-container">
        <div className="slots-card">
          <h1>🎰 Slot Machine</h1>
          
          <div className="balance-display">
            <h3>Your Balance: {balance.toLocaleString()} credits</h3>
          </div>

          <div className="bet-section">
            <label htmlFor="bet-input">Bet Amount:</label>
            <input
              id="bet-input"
              type="number"
              min="1"
              max={balance}
              value={bet}
              onChange={(e) => handleBetChange(parseInt(e.target.value) || 1)}
              disabled={isLoading}
            />
          </div>

          <div className="bet-quick-buttons">
            <button onClick={() => setBetPercentage(0.25)} disabled={isLoading} className="bet-percentage-btn">
              25%
            </button>
            <button onClick={() => setBetPercentage(0.5)} disabled={isLoading} className="bet-percentage-btn">
              50%
            </button>
            <button onClick={() => setBetPercentage(0.75)} disabled={isLoading} className="bet-percentage-btn">
              75%
            </button>
            <button onClick={() => setBetPercentage(1)} disabled={isLoading} className="bet-percentage-btn">
              Max
            </button>
          </div>

          <div className="slots-machine">
            <div className="slots-display">
              <div className="slots-reels">
                {gameResult ? (
                  gameResult.symbols.map((symbol, index) => (
                    <div key={index} className={`slot-reel ${isSpinning ? 'spinning' : ''}`}>
                      <div className="slot-symbol">{symbol}</div>
                    </div>
                  ))
                ) : (
                  [0, 1, 2].map((index) => (
                    <div key={index} className={`slot-reel ${isSpinning ? 'spinning' : ''}`}>
                      <div className="slot-symbol">🎰</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="game-controls">
              <button
                onClick={handleSpin}
                disabled={isLoading || bet > balance || bet <= 0}
                className={`spin-button ${isLoading ? 'spinning' : ''}`}
              >
                {isLoading ? 'Spinning...' : '🎰 SPIN'}
              </button>
            </div>
          </div>

          {message && (
            <div className={`message ${gameResult?.won ? 'win-message' : 'lose-message'}`}>
              {message}
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {gameResult && (
            <div className="game-result">
              <h4>Game Result:</h4>
              <div className="result-details">
                <div className="result-symbols">
                  {gameResult.symbols.map((symbol, index) => (
                    <span key={index} className="result-symbol">
                      {symbol} {SYMBOL_DISPLAY[symbol as keyof typeof SYMBOL_DISPLAY]}
                    </span>
                  ))}
                </div>
                {gameResult.won && (
                  <div className="win-details">
                    <p>Multiplier: {gameResult.multiplier}x</p>
                    <p>Payout: {gameResult.payout} credits</p>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="paytable">
            <h3>Paytable</h3>
            <div className="paytable-grid">
              {Object.entries(SYMBOL_MULTIPLIERS).map(([symbol, multiplier]) => (
                <div key={symbol} className="paytable-row">
                  <span className="paytable-symbol">{symbol}</span>
                  <span className="paytable-name">{SYMBOL_DISPLAY[symbol as keyof typeof SYMBOL_DISPLAY]}</span>
                  <span className="paytable-multiplier">{multiplier}x / {(multiplier * 0.5).toFixed(1)}x</span>
                </div>
              ))}
            </div>
            <p className="paytable-note">
              Win by getting 2 or 3 matching symbols!<br/>
              3 symbols = full multiplier, 2 symbols = half multiplier
            </p>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default SlotsGame;
