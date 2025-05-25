import React, { useEffect, useState } from 'react';
import BaseLayout from '../../components/Layout/BaseLayout';
import { GetUserInfo, GetPortfolioData, GetRecentTransactions, GetDailyQuiz, SubmitDailyQuizAnswer, GetDailyQuizAttemptToday, DailyQuizAttemptResponse } from '../../apiService';
import './Dashboard.css';
import { useAuth } from '../../contexts/AuthContext'; // Import useAuth

// Define TypeScript interfaces for our data structures
interface User {
  balance: number;
  profit_loss: number;
  profit_loss_percentage: number | null;
  total_trades: number;
  pet_energy: number;
  is_meme_mode: boolean;
  xp: number;
  level: number;
}

interface PortfolioItem {
  symbol: string;
  quantity: number;
  type: string; // Hinzugefügt
  performance: number; // Hinzugefügt
  // Füge hier weitere Eigenschaften hinzu, falls vorhanden
}

interface PortfolioData {
  success: boolean;
  portfolio: PortfolioItem[];
  best_performer: string; // Hinzugefügt
  best_performer_pct: number; // Hinzugefügt
  // Füge hier weitere Eigenschaften hinzu, falls vorhanden
}

interface AssetAllocation {
  symbol: string;
  name: string;
  percentage: number;
}

interface Transaction {
  transaction_type: string;
  asset_symbol: string;
  quantity: number;
  price_per_unit: number;
  timestamp: string;
}

interface Quiz {
  id: string;
  question: string;
  explanation?: string;
  possible_answer_1: string;
  possible_answer_2: string;
  possible_answer_3: string;
  attempted: boolean;
  selected_answer?: string;
  is_correct?: boolean;
  correct_answer_text?: string; // Ensure this is populated from the attempt or quiz details
}

interface Level {
  level: number;
  xp_required: number;
}

const Dashboard: React.FC = () => {
  // State declarations
  const [user, setUser] = useState<User | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [portfolioTotalValue, setPortfolioTotalValue] = useState<number>(0);
  const [assetAllocation, setAssetAllocation] = useState<AssetAllocation[]>([]);
  const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [dailyQuizAttempt, setDailyQuizAttempt] = useState<DailyQuizAttemptResponse | null>(null); // To store attempt details
  const [currentUserLevel, setCurrentUserLevel] = useState<number>(1);
  const [currentUserXp, setCurrentUserXp] = useState<number>(0);
  const [xpPercentage, setXpPercentage] = useState<number>(0);
  const [levels, setLevels] = useState<Level[]>([
    { level: 1, xp_required: 100 },
    { level: 2, xp_required: 300 },
    { level: 3, xp_required: 600 },
    { level: 4, xp_required: 1000 },
    { level: 5, xp_required: 2000 }
  ]);
  const [dogMessage, setDogMessage] = useState<string>('Hello trader! Remember: Buy high, sell higher! Diamond hands only! 💎🙌');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [quizSubmitting, setQuizSubmitting] = useState<boolean>(false); // To disable buttons during submission

  const { user: authUser, loading: authLoading, token } = useAuth(); // Get user and token from AuthContext

  useEffect(() => {
    console.log("[Dashboard] useEffect triggered");
    console.log("[Dashboard] authUser:", authUser);
    console.log("[Dashboard] authLoading:", authLoading);
    const fetchAllData = async () => {
      if (!authUser || !authUser.id) {
        console.warn("[Dashboard] No authUser or no authUser.id present!", authUser);
        setLoading(false);
        if (!authLoading) { // Check if auth is not loading to prevent premature error
          setError("User not authenticated. Please login.");
        }
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const userId = authUser.id.toString();

        // User Info & XP Calculation
        console.log("[Dashboard] Calling GetUserInfo...");
        const userInfoResponse = await GetUserInfo(userId);
        console.log("[Dashboard] GetUserInfo result:", userInfoResponse);

        let finalUserData: User | null = null;

        if (userInfoResponse && userInfoResponse.success && userInfoResponse.user) {
            finalUserData = userInfoResponse.user;
        } else if (userInfoResponse && userInfoResponse.success && userInfoResponse.data) {
            finalUserData = userInfoResponse.data;
        } else if (userInfoResponse && 
                   typeof userInfoResponse.balance !== 'undefined' &&
                   typeof userInfoResponse.profit_loss !== 'undefined' &&
                   typeof userInfoResponse.total_trades !== 'undefined' &&
                   typeof userInfoResponse.pet_energy !== 'undefined' &&
                   typeof userInfoResponse.is_meme_mode !== 'undefined' &&
                   typeof userInfoResponse.xp !== 'undefined' &&
                   typeof userInfoResponse.level !== 'undefined') {
            // Fallback for when the response is already the flat user object
            finalUserData = userInfoResponse as User;
        } else {
            console.error("[Dashboard] GetUserInfo call failed, returned unsuccessful status, or data was not in expected format:", userInfoResponse);
            setError(userInfoResponse?.message || "Failed to fetch user information.");
            // finalUserData remains null
        }

        if (finalUserData) {
            setUser(finalUserData);
            setCurrentUserLevel(finalUserData.level);
            setCurrentUserXp(finalUserData.xp);

            // XP calculation logic using finalUserData
            const userLvl = finalUserData.level;
            const userXP = finalUserData.xp;

            const currentLevelData = levels.find(l => l.level === userLvl);
            // XP required to *reach* userLvl (i.e., XP at the start of userLvl)
            // This is the xp_required of the (userLvl - 1). For L1, this is 0.
            const xpFromPreviousLevels = (userLvl === 1) ? 0 : (levels.find(l => l.level === userLvl - 1)?.xp_required || 0);

            if (currentLevelData) {
                // xp_required for currentLevelData.level is the total XP needed to *complete* this level.
                const xpToCompleteCurrentLevel = currentLevelData.xp_required; 
                
                const xpSpanOfCurrentLevel = xpToCompleteCurrentLevel - xpFromPreviousLevels;
                const xpEarnedInCurrentLevel = userXP - xpFromPreviousLevels;

                if (xpSpanOfCurrentLevel > 0) {
                    let percent = (xpEarnedInCurrentLevel / xpSpanOfCurrentLevel) * 100;
                    percent = Math.max(0, Math.min(percent, 100)); // Clamp percentage
                    console.log(`[Dashboard] XP Calc: UserLvl=${userLvl}, UserXP=${userXP}, PrevLvlXP=${xpFromPreviousLevels}, CurrLvlTargetXP=${xpToCompleteCurrentLevel}, Span=${xpSpanOfCurrentLevel}, EarnedInCurrLvl=${xpEarnedInCurrentLevel}, Percent=${percent}`);
                    setXpPercentage(percent);
                } else {
                    // This handles cases like max level (if currentLevelData is the last level and xp_required is its end)
                    // or if data is such that span is 0 (e.g. first level starts at 0, and its xp_required is also 0, which is unlikely for good data)
                    // If userXP is at or beyond the requirement for this level, it's 100%.
                    setXpPercentage(userXP >= xpToCompleteCurrentLevel ? 100 : 0);
                    console.log(`[Dashboard] XP Calc: Span is 0 or less. UserXP=${userXP}, CurrLvlTargetXP=${xpToCompleteCurrentLevel}. Setting percentage based on completion.`);
                }
            } else {
                console.error(`[Dashboard] XP Calc: Could not find level data for level ${userLvl}.`);
                setXpPercentage(0); // Reset if level data is missing
            }
        } else {
            // Error or no valid user data from API
            setUser(null);
            setCurrentUserLevel(1); // Reset to default
            setCurrentUserXp(0);   // Reset to default
            setXpPercentage(0);    // Reset XP percentage
            console.warn("[Dashboard] User data processing failed. States reset, XP percentage set to 0.");
        }

        // Portfolio
        console.log("[Dashboard] Calling GetPortfolioData...");
        const portfolio = await GetPortfolioData(userId);
        console.log("[Dashboard] GetPortfolioData result:", portfolio);
        setPortfolioData(portfolio);
        if (portfolio && portfolio.success) {
          const totalValue = portfolio.portfolio.reduce((sum: number, item: PortfolioItem) => {
            const value = item.quantity * 100; // Placeholder
            console.log(`[Dashboard] Portfolio item:`, item, "Value:", value);
            return sum + value;
          }, 0);
          setPortfolioTotalValue(totalValue);
          console.log(`[Dashboard] Portfolio total value: ${totalValue}`);

          const totalQuantity = portfolio.portfolio.reduce((sum: number, item: PortfolioItem) => sum + item.quantity, 0);
          const allocation = portfolio.portfolio.map((item: PortfolioItem) => ({
            symbol: item.symbol,
            name: item.symbol,
            percentage: totalQuantity > 0 ? (item.quantity / totalQuantity) * 100 : 0
          }));
          setAssetAllocation(allocation);
          console.log("[Dashboard] Asset allocation:", allocation);
        }

        // Transactions
        console.log("[Dashboard] Calling GetRecentTransactions...");
        const transactionsResponse = await GetRecentTransactions(userId);
        console.log("[Dashboard] GetRecentTransactions result:", transactionsResponse);
        if (transactionsResponse && transactionsResponse.success && Array.isArray(transactionsResponse.transactions)) {
          setRecentTransactions(transactionsResponse.transactions);
        } else if (Array.isArray(transactionsResponse)) { 
            console.warn("[Dashboard] GetRecentTransactions returned a direct array. Assuming it's the transaction list.");
            setRecentTransactions(transactionsResponse);
        } else {
          console.warn("[Dashboard] GetRecentTransactions did not return a successful response or transactions array:", transactionsResponse);
          setRecentTransactions([]); 
        }

        // Quiz
        console.log("[Dashboard] Initiating Quiz Logic...");
        if (token) {
          console.log("[Dashboard] Token found, proceeding to fetch daily quiz.");
          const dailyQuizResponse = await GetDailyQuiz();
          console.log("[Dashboard] GetDailyQuiz (for structure and content) result:", dailyQuizResponse);

          if (dailyQuizResponse && dailyQuizResponse.success && dailyQuizResponse.quiz) {
            const todaysQuizStructure = dailyQuizResponse.quiz;
            console.log("[Dashboard] Successfully fetched quiz structure:", todaysQuizStructure);

            console.log("[Dashboard] Calling GetDailyQuizAttemptToday...");
            const attemptTodayResponse = await GetDailyQuizAttemptToday();
            console.log("[Dashboard] GetDailyQuizAttemptToday result:", attemptTodayResponse);
            setDailyQuizAttempt(attemptTodayResponse); // Store the raw attempt response

            if (attemptTodayResponse && attemptTodayResponse.success && 
                typeof attemptTodayResponse.selected_answer !== 'undefined' && 
                attemptTodayResponse.quiz_id === todaysQuizStructure.id) {
              console.log("[Dashboard] User has an attempt for today's quiz. Setting quiz state as attempted.");
              setQuiz({
                id: todaysQuizStructure.id,
                question: todaysQuizStructure.question,
                possible_answer_1: todaysQuizStructure.possible_answer_1,
                possible_answer_2: todaysQuizStructure.possible_answer_2,
                possible_answer_3: todaysQuizStructure.possible_answer_3,
                attempted: true,
                selected_answer: attemptTodayResponse.selected_answer,
                is_correct: attemptTodayResponse.is_correct,
                correct_answer_text: attemptTodayResponse.correct_answer,
                explanation: attemptTodayResponse.explanation || todaysQuizStructure.explanation,
              });
            } else {
              console.log("[Dashboard] No valid attempt for today's quiz, or attempt is for a different quiz. Setting quiz as fresh.");
              setQuiz({
                id: todaysQuizStructure.id,
                question: todaysQuizStructure.question,
                possible_answer_1: todaysQuizStructure.possible_answer_1,
                possible_answer_2: todaysQuizStructure.possible_answer_2,
                possible_answer_3: todaysQuizStructure.possible_answer_3,
                attempted: false,
                explanation: todaysQuizStructure.explanation,
                selected_answer: undefined,
                is_correct: undefined,
                correct_answer_text: undefined,
              });
            }
          } else {
            let warningMessage = "[Dashboard] No daily quiz available or fetch failed. ";
            if (!dailyQuizResponse) {
              warningMessage += "The response from GetDailyQuiz was null or undefined.";
            } else if (!dailyQuizResponse.success) {
              warningMessage += `API call GetDailyQuiz was not successful. Message: ${dailyQuizResponse.message || 'No specific error message provided by API.'}`;
            } else if (!dailyQuizResponse.quiz) {
              warningMessage += "API call GetDailyQuiz was successful, but no quiz data was included in the response.";
            } else {
              // This case should ideally not be reached if the main if condition is structured correctly
              warningMessage += "Unexpected issue with the daily quiz response structure.";
            }
            console.warn(warningMessage, "Full response for GetDailyQuiz:", dailyQuizResponse);
            setQuiz(null); // No quiz available for today
          }
        } else {
          console.warn("[Dashboard] No token available. Quiz will not be fetched.");
          setQuiz(null); 
        }

        setLoading(false);
        console.log("[Dashboard] All data loaded!");
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
        setQuiz(prevQuiz => prevQuiz ? { ...prevQuiz, attempted: false } : null);
        setLoading(false);
      }
    };
    if (!authLoading) {
      fetchAllData();
    }
  }, [authUser, authLoading, token, levels]); 

  // Logging for render phases
  useEffect(() => {
    console.log("[Dashboard] Render: user=", user);
    console.log("[Dashboard] Render: portfolioData=", portfolioData);
    console.log("[Dashboard] Render: recentTransactions=", recentTransactions);
    console.log("[Dashboard] Render: quiz=", quiz);
    console.log("[Dashboard] Render: dailyQuizAttempt=", dailyQuizAttempt); 
    console.log("[Dashboard] Render: error=", error);
    console.log("[Dashboard] Render: loading=", loading);
  }, [user, portfolioData, recentTransactions, quiz, dailyQuizAttempt, error, loading]);

  const handleQuizSubmit = async (quizId: string, answer: string) => {
    if (!token || quizSubmitting || quiz?.attempted) return;

    setQuizSubmitting(true);
    setError(null);

    try {
      const payload = { quiz_id: quizId, selected_answer: answer };
      const result = await SubmitDailyQuizAnswer(payload);
      if (result.success) {
        setQuiz(prevQuiz => {
          if (!prevQuiz) return null;
          return {
            ...prevQuiz,
            attempted: true,
            selected_answer: result.selected_answer,
            is_correct: result.is_correct,
            correct_answer_text: result.correct_answer,
            explanation: result.explanation || prevQuiz.explanation,
          };
        });
        if (result.xp_gained && result.xp_gained > 0 && user) {
          setUser(prevUser => prevUser ? { ...prevUser, xp: prevUser.xp + (result.xp_gained || 0) } : null);
        }
      } else {
        setError(result.message || 'Failed to submit quiz answer.');
        setQuiz(prevQuiz => prevQuiz ? { ...prevQuiz, attempted: true, selected_answer: answer, is_correct: false } : null);
      }
    } catch (err: any) {
      console.error('Error submitting quiz answer:', err);
      setError(err.message || 'An unexpected error occurred while submitting your answer.');
      setQuiz(prevQuiz => prevQuiz ? { ...prevQuiz, selected_answer: answer, attempted: false } : null); 
    } finally {
      setQuizSubmitting(false);
    }
  };

  const toggleMemeMode = async () => {
    if (!user) return;
    
    try {
      setUser({ ...user, is_meme_mode: !user.is_meme_mode });
    } catch (err) {
      console.error('Error toggling meme mode:', err);
      setError('Failed to toggle meme mode. Please try again.');
    }
  };

  if (loading) {
    return (
      <BaseLayout title="Loading Dashboard - BuyHigh.io">
        <div className="container mx-auto flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-neo-purple border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading your investment data...</p>
          </div>
        </div>
      </BaseLayout>
    );
  }

  if (error) {
    return (
      <BaseLayout title="Dashboard Error - BuyHigh.io">
        <div className="container mx-auto flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-red-500">{error}</p>
            <button 
              className="mt-4 px-4 py-2 bg-neo-purple text-white rounded-lg hover:bg-neo-purple-dark transition-colors"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout title="Dashboard - BuyHigh.io">
      <div className="container mx-auto">
        {/* Dashboard Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-pixel gradient-text mb-2">Command Center</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm max-w-2xl mx-auto">
            Welcome to your investment hub. Monitor performance, check balances, and make strategic decisions.
          </p>
        </header>
        
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Balance Card */}
          <div className="glass-card p-5 rounded-2xl stat-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-neo-purple/10 rounded-full blur-xl"></div>
            <div className="relative">
              <div className="flex items-center mb-3">
                <div className="bg-neo-purple/10 p-2 rounded-lg mr-3">
                  <svg className="w-6 h-6 text-neo-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300">Current Balance</h3>
              </div>
              <div className="ml-11">
                <div className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-end space-x-1">
                  <span className="counter">${(user?.balance ?? 0).toFixed(2)}</span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Available for trading
                </p>
              </div>
            </div>
          </div>
          
          {/* Profit/Loss Card */}
          <div className="glass-card p-5 rounded-2xl stat-card relative overflow-hidden">
            <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 ${user && user.profit_loss >= 0 ? 'bg-neo-emerald/10' : 'bg-neo-red/10'} rounded-full blur-xl`}></div>
            <div className="relative">
              <div className="flex items-center mb-3">
                <div className={`${user && user.profit_loss >= 0 ? 'bg-neo-emerald/10' : 'bg-neo-red/10'} p-2 rounded-lg mr-3`}>
                  <svg 
                    className={`w-6 h-6 ${user && user.profit_loss >= 0 ? 'text-neo-emerald' : 'text-neo-red'}`} 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24" 
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth="2" 
                      d={user && user.profit_loss >= 0 
                        ? 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' 
                        : 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6'}
                    ></path>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300">Profit/Loss</h3>
              </div>
              <div className="ml-11">
                <div className={`text-2xl font-bold ${user && user.profit_loss >= 0 ? 'text-neo-emerald' : 'text-neo-red'} flex items-end space-x-1`}>
                  <span className="counter">€{(user?.profit_loss ?? 0).toFixed(2)}</span>
                  <span className="text-sm">
                    {user && typeof user.profit_loss_percentage === 'number' ? (
                      user.profit_loss >= 0 
                        ? `(+${user.profit_loss_percentage.toFixed(1)}%)` 
                        : `(${user.profit_loss_percentage.toFixed(1)}%)`
                    ) : '(N/A)'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {user && user.profit_loss >= 0 ? 'Up since first trade' : 'Down since first trade'}
                </p>
              </div>
            </div>
          </div>
          
          {/* Trades Card */}
          <div className="glass-card p-5 rounded-2xl stat-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-neo-blue/10 rounded-full blur-xl"></div>
            <div className="relative">
              <div className="flex items-center mb-3">
                <div className="bg-neo-blue/10 p-2 rounded-lg mr-3">
                  <svg className="w-6 h-6 text-neo-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300">Total Trades</h3>
              </div>
              <div className="ml-11">
                <div className="text-2xl font-bold text-gray-800 dark:text-gray-100 counter">{user?.total_trades || 0}</div>
                <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div 
                    className="bg-neo-blue h-1.5 rounded-full" 
                    style={{width: `${user && user.total_trades > 100 ? 100 : user?.total_trades || 0}%`}}
                  ></div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {user?.total_trades || 0} of 100 for next level
                </p>
              </div>
            </div>
          </div>
          
          {/* XP Level Card */}
          <div className="glass-card p-5 rounded-2xl stat-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-neo-amber/10 rounded-full blur-xl"></div>
            <div className="relative">
              <div className="flex items-center mb-3">
                <div className="bg-neo-amber/10 p-2 rounded-lg mr-3">
                  <svg className="w-6 h-6 text-neo-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300">Trader Level</h3>
              </div>
              <div className="ml-11">
                <div className="text-2xl font-bold text-gray-800 dark:text-gray-100 counter">{currentUserLevel}</div>
                <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                  <div className="bg-neo-amber h-1.5 rounded-full" style={{width: `${xpPercentage}%`}}></div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {currentUserXp} XP / {
                    levels.find(l => l.level === currentUserLevel + 1)?.xp_required || 'N/A'
                  } XP
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Main Dashboard Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Portfolio & Activity */}
          <div className="lg:col-span-2 space-y-8">
            {/* Portfolio Card */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-200/10 dark:border-gray-700/20 glow-effect">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold flex items-center text-gray-800 dark:text-gray-100">
                    <svg className="w-6 h-6 mr-2 text-neo-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                    </svg>
                    Portfolio
                    <span className="ml-2 text-xs font-medium text-neo-blue bg-neo-blue/10 px-2 py-0.5 rounded-full">
                      Assets: {portfolioData?.portfolio?.length || 0}
                    </span>
                  </h2>
                  <a href="/trade" className="neo-button px-3 py-1 rounded-lg text-xs font-medium bg-neo-blue/10 text-neo-blue border border-neo-blue/20 hover:bg-neo-blue hover:text-white flex items-center">
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                    Trade Now
                  </a>
                </div>

                {portfolioData && portfolioData.success && portfolioData.portfolio.length > 0 ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      {/* Asset distribution stats */}
                      <div className="glass-card p-4 rounded-xl backdrop-blur-sm">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Total Assets Value</span>
                        <p className="text-2xl font-bold text-gray-800 dark:text-gray-200 mt-1 counter" id="portfolio-total-value">
                          €{portfolioTotalValue.toFixed(2)}
                        </p>
                      </div>
                      <div className="glass-card p-4 rounded-xl backdrop-blur-sm">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Best Performer</span>
                        <p className="text-lg font-bold text-neo-emerald mt-1">
                          {portfolioData.best_performer || 'N/A'}
                        </p>
                        <span className="text-xs text-neo-emerald">
                          +{(portfolioData.best_performer_pct || 0).toFixed(2)}%
                        </span>
                      </div>
                      <div className="glass-card p-4 rounded-xl backdrop-blur-sm">
                        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Asset Allocation</span>
                        
                        <div className="flex gap-1 mt-2">
                          {assetAllocation && assetAllocation.length > 0 ? (
                            assetAllocation.map((asset, index) => {
                              const colors = ['bg-neo-blue', 'bg-neo-purple', 'bg-neo-emerald', 'bg-neo-amber', 'bg-neo-pink'];
                              const percentage = Math.round((asset.percentage || 0) * 10) / 10;
                              return percentage >= 3 ? (
                                <div 
                                  key={asset.symbol || `asset-key-${index}`}
                                  className={`h-2 rounded-full ${colors[index % colors.length]}`} 
                                  style={{width: `${percentage}%`}}
                                  title={`${asset.name || 'Unknown Asset'}: ${percentage}%`}
                                  data-symbol={asset.symbol || 'unknown'}
                                ></div>
                              ) : null;
                            })
                          ) : (
                            <div className="h-2 rounded-full bg-gray-300 dark:bg-gray-600" style={{width: '100%'}}></div>
                          )}
                        </div>
                        
                        <div className="flex gap-1 mt-1 w-full">
                          {assetAllocation && assetAllocation.length > 0 ? (
                            assetAllocation.map((asset) => {
                              const percentage = Math.round((asset.percentage || 0) * 10) / 10;
                              return percentage >= 3 ? (
                                <div 
                                  key={`label-${asset.symbol || 'unknown'}`} 
                                  className="text-xxs text-center overflow-hidden text-ellipsis" 
                                  style={{width: `${percentage}%`}}
                                >
                                  {asset.symbol || ''} 
                                </div>
                              ) : null;
                            })
                          ) : (
                            <span className="text-xxs">No Assets</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Portfolio List */}
                    <div className="overflow-hidden">
                      <div className="max-h-[280px] overflow-y-auto pr-1 space-y-2">
                        {portfolioData.portfolio.map((item, index) => (
                          <div key={`portfolio-${index}`} className="glass-card hover:shadow-neo transition-all duration-300 rounded-xl p-3 flex justify-between items-center">
                            <div className="flex items-center">
                              <div className="bg-neo-blue/10 dark:bg-neo-blue/20 p-2 rounded-lg mr-3">
                                <span className="font-medium text-neo-blue">{(item.symbol && item.symbol[0]) || 'X'}</span>
                              </div>
                              <div>
                                <h4 className="font-medium text-sm text-gray-800 dark:text-gray-200">{item.symbol || 'Unknown'}</h4>
                                <p className="text-xs text-gray-500">{item.type || 'Asset'}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-semibold text-gray-800 dark:text-gray-200">{(item.quantity ?? 0).toFixed(2)} units</p>
                              <p className={`text-xs ${(item.performance || 0) > 0 ? 'text-neo-emerald' : 'text-neo-red'}`}>
                                {(item.performance || 0) > 0 ? '+' : ''}{(item.performance || 0).toFixed(2)}%
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="glass-card p-8 rounded-xl flex flex-col items-center justify-center backdrop-blur-sm">
                    <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">Your Portfolio is Empty</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-4">Start building your portfolio by making your first trade</p>
                    <a href="/trade" className="neo-button px-4 py-2 rounded-lg text-sm font-medium bg-neo-emerald/10 text-neo-emerald border border-neo-emerald/20 hover:bg-neo-emerald hover:text-white flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                      </svg>
                      Start Trading
                    </a>
                  </div>
                )}
              </div>
            </div>
            
            {/* Recent Activities Card */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-200/10 dark:border-gray-700/20">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold flex items-center text-gray-800 dark:text-gray-100">
                    <svg className="w-6 h-6 mr-2 text-neo-pink" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Recent Activities
                  </h2>
                  <span className="text-xs font-medium text-neo-pink bg-neo-pink/10 px-2 py-0.5 rounded-full">Last 7 days</span>
                </div>
                
                {recentTransactions && recentTransactions.length > 0 ? (
                  <div className="max-h-[300px] overflow-y-auto pr-1 space-y-3">
                    {recentTransactions.map((tx, index) => {
                      const txDate = new Date(tx.timestamp);
                      const formattedDate = `${txDate.toLocaleString('en', { month: 'short' })} ${txDate.getDate()}, ${txDate.getHours()}:${String(txDate.getMinutes()).padStart(2, '0')}`;
                      
                      return (
                        <div 
                          key={`tx-${index}`} 
                          className={`glass-card hover:shadow-neo transition-all duration-300 rounded-xl p-3 flex items-center justify-between ${index === 0 ? 'animate-pulse-slow' : ''}`}
                        >
                          <div className="flex items-center">
                            <div className={`${tx.transaction_type === 'buy' ? 'bg-neo-emerald/10' : 'bg-neo-red/10'} p-2 rounded-lg mr-3`}>
                              <svg 
                                className={`w-5 h-5 ${tx.transaction_type === 'buy' ? 'text-neo-emerald' : 'text-neo-red'}`} 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24" 
                                xmlns="http://www.w3.org/2000/svg"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth="2" 
                                  d={tx.transaction_type === 'buy' 
                                    ? 'M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z' 
                                    : 'M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z'}
                                ></path>
                              </svg>
                            </div>
                            <div>
                              <div className="flex items-center">
                                <span className="font-medium text-sm text-gray-700 dark:text-gray-300">{tx.asset_symbol}</span>
                                <span className={`ml-2 px-2 py-0.5 rounded-full ${tx.transaction_type === 'buy' ? 'bg-neo-emerald/10 text-neo-emerald' : 'bg-neo-red/10 text-neo-red'} text-xxs`}>
                                  {tx.transaction_type === 'buy' ? 'Bought' : 'Sold'}
                                </span>
                              </div>
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {tx.quantity.toFixed(0)} units @ ${tx.price_per_unit.toFixed(2)}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {formattedDate}
                            </p>
                            <p className={`text-xs font-medium ${tx.transaction_type === 'buy' ? 'text-neo-emerald' : 'text-neo-red'}`}>
                              {tx.transaction_type === 'buy' ? '+' : '-'}${(tx.price_per_unit * tx.quantity).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="glass-card p-8 rounded-xl flex flex-col items-center justify-center backdrop-blur-sm">
                    <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                      <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-600 dark:text-gray-300 mb-2">No Recent Activities</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 text-center">Your transaction history will appear here</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Companion and Status */}
          <div className="space-y-8">
            {/* Pet Companion Card */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-200/10 dark:border-gray-700/20 glow-effect">
              <div className="p-6">
                <div className="flex justify-between items-center mb-5">
                  <h2 className="text-xl font-semibold flex items-center text-gray-800 dark:text-gray-100">
                    <svg className="w-6 h-6 mr-2 text-neo-amber animate-bounce-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    Your Companion
                  </h2>
                </div>
                
                <div className="text-center mb-6">
                  {/* Bull Avatar - SVG implementation for guaranteed availability */}
                  <div className="w-32 h-32 mx-auto bg-gradient-to-br from-neo-amber/20 to-neo-blue/20 rounded-full flex items-center justify-center mb-3 shadow-neo relative overflow-hidden">
                    {/* Bull Character SVG */}
                    <div className="w-28 h-28 relative">
                      {/* Face and Features */}
                      <div className="absolute inset-0">
                        {/* Bull Face */}
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" className={`w-full h-full ${user?.is_meme_mode ? 'meme-spin' : ''}`}>
                          {/* Bull Head */}
                          <circle cx="50" cy="50" r="40" fill="#794928" />
                          
                          {/* Bull Nose */}
                          <ellipse cx="50" cy="65" rx="15" ry="10" fill="#594020" />
                          <circle cx="45" cy="65" r="4" fill="#000" className="animate-pulse-slow" style={{animationDelay: '1.2s'}} />
                          <circle cx="55" cy="65" r="4" fill="#000" className="animate-pulse-slow" style={{animationDelay: '2.3s'}} />
                          
                          {/* Bull Eyes with Sunglasses */}
                          <rect x="25" y="30" width="50" height="15" rx="5" fill="#000" />
                          <rect x="20" y="30" width="15" height="15" rx="5" transform="rotate(-10 20 30)" />
                          <rect x="65" y="30" width="15" height="15" rx="5" transform="rotate(10 65 30)" />
                          <line x1="50" y1="30" x2="50" y2="45" stroke="#333" strokeWidth="1" />
                          <ellipse cx="35" cy="37" rx="7" ry="5" fill="#1c84ff" className="animate-pulse-slow" style={{animationDelay: '1s'}} />
                          <ellipse cx="65" cy="37" rx="7" ry="5" fill="#1c84ff" className="animate-pulse-slow" style={{animationDelay: '0.5s'}} />
                          
                          {/* Bull Horns */}
                          <path d="M15 30 Q 10 10, 30 15" stroke="#d8c27a" strokeWidth="8" fill="none" />
                          <path d="M85 30 Q 90 10, 70 15" stroke="#d8c27a" strokeWidth="8" fill="none" />
                          
                          {/* Bull Ears */}
                          <circle cx="25" cy="35" r="7" fill="#593920" />
                          <circle cx="75" cy="35" r="7" fill="#593920" />
                        </svg>
                      </div>
                      
                      {!user?.is_meme_mode && (
                        // Business Accessories - only show if Meme Mode is OFF
                        <div className="absolute -bottom-8 -left-4 -right-4">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40">
                            {/* Suit Jacket */}
                            <path d="M40 0 L60 0 L80 0 L75 15 L70 25 L60 40 L50 25 L45 15 Z" fill="#1e293b" />
                            
                            {/* Suit Lapels */}
                            <path d="M52 0 L50 10 L55 18 L60 22 L65 18 L70 10 L68 0" fill="#141c2b" />
                            
                            {/* Shirt */}
                            <path d="M55 0 L57 12 L60 20 L63 12 L65 0" fill="#f8fafc" />
                            
                            {/* Tie */}
                            <path d="M60 0 L58 5 L57 10 L60 20 L63 10 L62 5 L60 0 Z" fill="#e63946" />
                            <path d="M58 5 L60 7 L62 5 L61 4 L59 4 Z" fill="#c1121f" />
                            
                            {/* Tie Knot */}
                            <path d="M59 4 L60 6 L61 4 Z" fill="#f1faee" stroke="#c1121f" strokeWidth="0.2" />
                            
                            {/* Tie Bottom */}
                            <path d="M57 10 L60 20 L63 10 L60 13 Z" fill="#c1121f" />
                            
                            {/* Jacket Edges/Highlights */}
                            <path d="M45 15 L50 25 L52 15" stroke="#0f172a" strokeWidth="0.3" fill="none" />
                            <path d="M75 15 L70 25 L68 15" stroke="#0f172a" strokeWidth="0.3" fill="none" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="relative">
                    <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200">Mr. Stonks</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Your trading advisor</p>
                    
                    {/* Status Badge */}
                    <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-neo-emerald/10 text-neo-emerald">
                      <span className="relative flex h-2 w-2 mr-1">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neo-emerald opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-neo-emerald"></span>
                      </span>
                      Bullish Mode
                    </div>
                  </div>
                </div>
                
                {/* Including the dog message component */}
                <div className="glass-card p-4 rounded-xl backdrop-blur-sm mb-5">
                  <div className="flex space-x-2">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-neo-amber/20 flex items-center justify-center">
                      <span className="text-sm">🐂</span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-700 dark:text-gray-300">{dogMessage}</p>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4 mx-4 md:mx-8">
                  {/* Energy Bar */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Energy</span>
                      <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{user?.pet_energy || 0}/100</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-neo-amber h-2 rounded-full transition-all duration-1000" 
                        style={{width: `${user?.pet_energy || 0}%`}}
                      ></div>
                    </div>
                  </div>
                  
                  {/* Meme Mode Toggle */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Meme Mode</span>
                    <div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          className="sr-only peer" 
                          checked={user?.is_meme_mode || false}
                          onChange={toggleMemeMode}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-neo-amber"></div>
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Daily Quiz Card */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-200/10 dark:border-gray-700/20 glow-effect">
              <div className="p-6">
                <div className="flex justify-between items-center mb-5">
                  <h2 className="text-xl font-semibold flex items-center text-gray-800 dark:text-gray-100">
                    <svg className="w-6 h-6 mr-2 text-neo-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.79 4 4s-1.79 4-4 4c-1.742 0-3.223-.835-3.772-2H1v-4h7.228zM19 11H12M12 11V4M12 11v7"></path></svg>
                    Daily Quiz
                  </h2>
                  {quiz?.attempted && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${quiz.is_correct ? 'bg-neo-emerald/20 text-neo-emerald' : 'bg-neo-red/20 text-neo-red'}`}>
                      {quiz.is_correct ? 'Correct!' : 'Incorrect'}
                    </span>
                  )}
                </div>

                {quiz ? (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-600 dark:text-gray-300">{quiz.question}</p>
                    <div className="space-y-2">
                      {([quiz.possible_answer_1, quiz.possible_answer_2, quiz.possible_answer_3]).map((answer, index) => {
                        if (!answer) return null; 
                        
                        let buttonClass = "w-full text-left px-4 py-2 rounded-lg border transition-all duration-150 text-sm ";
                        if (quiz.attempted) {
                          if (answer === quiz.correct_answer_text) {
                            buttonClass += "bg-neo-emerald/30 border-neo-emerald text-neo-emerald dark:text-white"; 
                          } else if (answer === quiz.selected_answer) {
                            buttonClass += "bg-neo-red/30 border-neo-red text-neo-red dark:text-white"; 
                          } else {
                            buttonClass += "bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"; 
                          }
                        } else {
                          buttonClass += "bg-gray-50 dark:bg-gray-700/50 border-gray-300 dark:border-gray-600 hover:bg-neo-blue/10 hover:border-neo-blue dark:hover:bg-neo-blue/20"; 
                        }

                        return (
                          <button
                            key={index}
                            onClick={() => handleQuizSubmit(quiz.id, answer)}
                            disabled={quiz.attempted || quizSubmitting}
                            className={buttonClass}
                          >
                            {answer}
                          </button>
                        );
                      })}
                    </div>
                    {quiz.attempted && quiz.explanation && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-xs text-gray-600 dark:text-gray-300">
                        <strong>Explanation:</strong> {quiz.explanation}
                      </div>
                    )}
                    {error && quizSubmitting === false && <p className="text-xs text-neo-red mt-2">{error}</p>}
                  </div>
                ) : (
                  <div className="text-center py-6">
                    <svg className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.79 4 4s-1.79 4-4 4c-1.742 0-3.223-.835-3.772-2H1v-4h7.228zM19 11H12M12 11V4M12 11v7"></path></svg>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Daily quiz not available or already completed.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Player Status Card */}
            <div className="glass-card rounded-2xl overflow-hidden border border-gray-200/10 dark:border-gray-700/20">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold flex items-center text-gray-800 dark:text-gray-100">
                    <svg className="w-6 h-6 mr-2 text-neo-purple animate-pulse-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                    </svg>
                    Player Status
                  </h2>
                </div>
                
                {/* Level Progress */}
                <div className="mb-8">
                  <div className="flex justify-between items-end mb-2">
                    <div>
                      <span className="block text-xs text-gray-500 dark:text-gray-400">Trader Level</span>
                      <span className="text-3xl font-bold text-neo-purple">{currentUserLevel}</span>
                    </div>
                    <div className="text-right">
                      <span className="block text-xs text-gray-500 dark:text-gray-400">Next Level</span>
                      <span className="text-lg font-medium text-gray-600 dark:text-gray-300">{currentUserLevel+1}</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-1">
                    <div className="bg-neo-purple h-2.5 rounded-full" style={{width: `${xpPercentage}%`}}></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{currentUserXp} XP</span>
                    <span>
                      {levels.find(l => l.level === currentUserLevel + 1)?.xp_required || 'N/A'} XP
                    </span>
                  </div>
                  <div className="mt-2 text-xxs text-neo-emerald flex items-center">
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                    </svg>
                    +50 XP on next trade!
                  </div>
                </div>
                
                {/* Badges */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center">
                    <svg className="w-4 h-4 mr-1 text-neo-amber" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
                    </svg>
                    Trader Badges
                  </h3>
                  
                  <div className="flex flex-wrap gap-2">
                    {/* First Trade Badge */}
                    <div className="relative group">
                      <div className="w-12 h-12 bg-gradient-to-br from-yellow-300 to-yellow-600 rounded-full flex items-center justify-center transition-transform group-hover:scale-110">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                        </svg>
                      </div>
                      <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-neo-blue rounded-full flex items-center justify-center border-2 border-white dark:border-gray-800">
                        <span className="text-white text-xxs">1</span>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xxs rounded p-1 w-24 text-center transition-opacity">
                        First Trade
                      </div>
                    </div>
                    
                    {/* Streak Badge */}
                    <div className="relative group">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-300 to-blue-600 rounded-full flex items-center justify-center transition-transform group-hover:scale-110">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                      </div>
                      <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-neo-blue rounded-full flex items-center justify-center border-2 border-white dark:border-gray-800">
                        <span className="text-white text-xxs">5</span>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xxs rounded p-1 w-24 text-center transition-opacity">
                        5-Day Streak
                      </div>
                    </div>
                    
                    {/* Locked Badge */}
                    <div className="relative group opacity-50">
                      <div className="w-12 h-12 bg-gray-400 dark:bg-gray-600 rounded-full flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                        </svg>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xxs rounded p-1 w-24 text-center transition-opacity">
                        Locked Badge
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Quick Actions */}
        <div className="fixed bottom-8 right-8 hidden lg:block">
          <div className="glass-card rounded-full p-2 shadow-neo mb-2 hover:shadow-neo-lg transition-all">
            <a href="/trade" className="w-12 h-12 flex items-center justify-center bg-neo-emerald rounded-full text-white hover:scale-110 transition-transform">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default Dashboard;

