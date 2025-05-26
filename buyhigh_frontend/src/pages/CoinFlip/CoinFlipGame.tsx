import React, { useState, useEffect } from 'react';
import { recordCoinFlip, CoinFlipRequestData, CoinFlipResponseData, GetUserInfo } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';
import './CoinFlipGame.css';

const CoinFlipGame: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const [betAmount, setBetAmount] = useState<number>(10);
  const [selectedSide, setSelectedSide] = useState<'heads' | 'tails'>('heads');
  const [gameResult, setGameResult] = useState<'heads' | 'tails' | null>(null);
  const [gameWon, setGameWon] = useState<boolean | null>(null);
  const [isFlipping, setIsFlipping] = useState<boolean>(false);
  const [gameResponse, setGameResponse] = useState<CoinFlipResponseData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [userBalance, setUserBalance] = useState<number>(0);

  // Check if user is logged in and get balance
  useEffect(() => {
    const fetchUserBalance = async () => {
      if (isAuthenticated && user?.id) {
        try {
          const userInfo = await GetUserInfo(String(user.id));
          // Fix: Handle nested user structure from backend API
          if (userInfo && userInfo.success && userInfo.user && userInfo.user.balance !== undefined) {
            setUserBalance(userInfo.user.balance);
          } else if (userInfo && userInfo.balance !== undefined) {
            // Fallback for direct balance access
            setUserBalance(userInfo.balance);
          }
        } catch (error) {
          console.error('Error fetching user info:', error);
        }
      }
    };
    fetchUserBalance();
  }, [isAuthenticated, user]);

  const flipCoin = async () => {
    if (!isAuthenticated || !user?.id) {
      setError('Please log in to play the coin flip game');
      return;
    }

    if (betAmount <= 0) {
      setError('Bet amount must be greater than 0');
      return;
    }

    if (betAmount > userBalance) {
      setError('Insufficient balance for this bet');
      return;
    }

    setIsFlipping(true);
    setError(null);
    setGameResponse(null);

    // Simulate coin flip animation delay
    setTimeout(async () => {
      try {
        // Generate random result
        const result: 'heads' | 'tails' = Math.random() < 0.5 ? 'heads' : 'tails';
        const won = result === selectedSide;
        
        setGameResult(result);
        setGameWon(won);

        // Prepare API call data
        const coinFlipData: CoinFlipRequestData = {
          Success: won,
          bet: betAmount,
          profit: won ? betAmount : -betAmount // If won: +bet, if lost: -bet
        };

        // Call API to record the result
        const response = await recordCoinFlip(coinFlipData);
        setGameResponse(response);

        // Update local balance if the API call was successful
        if (response.balance_updated && response.new_balance !== undefined) {
          setUserBalance(response.new_balance);
        }

      } catch (error: any) {
        setError(error.message || 'An error occurred during the game');
        console.error('Coin flip error:', error);
      } finally {
        setIsFlipping(false);
      }
    }, 2000); // 2 second animation
  };

  const resetGame = () => {
    setGameResult(null);
    setGameWon(null);
    setGameResponse(null);
    setError(null);
  };

  if (!isAuthenticated || !user?.id) {
    return (
      <div className="coinflip-container">
        <div className="coinflip-card">
          <h1>🪙 Coin Flip Game</h1>
          <p>Please log in to play the coin flip game.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="coinflip-container">
      <div className="coinflip-card">
        <h1>🪙 Coin Flip Game</h1>
        
        <div className="balance-display">
          <h3>Your Balance: ${userBalance.toFixed(2)}</h3>
        </div>

        <div className="bet-section">
          <label htmlFor="bet-amount">Bet Amount:</label>
          <input
            id="bet-amount"
            type="number"
            value={betAmount}
            onChange={(e) => setBetAmount(Number(e.target.value))}
            min="1"
            max={userBalance}
            disabled={isFlipping}
          />
        </div>

        <div className="side-selection">
          <h3>Choose Your Side:</h3>
          <div className="side-buttons">
            <button
              className={`side-btn ${selectedSide === 'heads' ? 'selected' : ''}`}
              onClick={() => setSelectedSide('heads')}
              disabled={isFlipping}
            >
              👑 Heads
            </button>
            <button
              className={`side-btn ${selectedSide === 'tails' ? 'selected' : ''}`}
              onClick={() => setSelectedSide('tails')}
              disabled={isFlipping}
            >
              🦅 Tails
            </button>
          </div>
        </div>

        <div className="coin-display">
          <div className={`coin ${isFlipping ? 'flipping' : ''}`}>
            {isFlipping ? (
              '🪙'
            ) : gameResult ? (
              gameResult === 'heads' ? '👑' : '🦅'
            ) : (
              '🪙'
            )}
          </div>
        </div>

        {gameResult && !isFlipping && (
          <div className={`result ${gameWon ? 'win' : 'lose'}`}>
            <h2>{gameWon ? '🎉 You Won!' : '😔 You Lost!'}</h2>
            <p>The coin landed on: <strong>{gameResult}</strong></p>
            {gameWon ? (
              <p>You won ${betAmount}!</p>
            ) : (
              <p>You lost ${betAmount}</p>
            )}
          </div>
        )}

        {gameResponse && (
          <div className="game-response">
            <h4>Game Summary:</h4>
            <p>Old Balance: ${gameResponse.old_balance?.toFixed(2)}</p>
            <p>New Balance: ${gameResponse.new_balance?.toFixed(2)}</p>
            <p>Status: {gameResponse.status}</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="game-controls">
          {!isFlipping && !gameResult && (
            <button
              className="flip-btn"
              onClick={flipCoin}
              disabled={betAmount <= 0 || betAmount > userBalance}
            >
              Flip Coin!
            </button>
          )}

          {gameResult && !isFlipping && (
            <div className="post-game-controls">
              <button className="play-again-btn" onClick={resetGame}>
                Play Again
              </button>
            </div>
          )}

          {isFlipping && (
            <div className="flipping-message">
              <p>🪙 Flipping coin... 🪙</p>
            </div>
          )}
        </div>

        <div className="game-rules">
          <h4>Game Rules:</h4>
          <ul>
            <li>Choose heads or tails</li>
            <li>Enter your bet amount</li>
            <li>If you win, you get your bet amount as profit</li>
            <li>If you lose, you lose your bet amount</li>
            <li>Minimum bet: $1</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default CoinFlipGame;
