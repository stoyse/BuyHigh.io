import axios from 'axios';

const rawApiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'; // Updated port
const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, ""); // Remove trailing slash if present
const DEBUG = true; // Enable/disable debug mode

// Debug logging function
const logDebug = (message: string, data: any = null) => {
  if (!DEBUG) return;

  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  console.debug(`[${timestamp}]`, message, data);
};

// Helper function to log API calls
const logApiCall = (method: string, endpoint: string, params?: any) => {
  const url = `${API_BASE_URL}${endpoint}`;

  if (DEBUG || (params && params.logOverride)) { // Example condition
    if (params) {
      logDebug(`${method} Request: ${url}`, params);
    } else {
      logDebug(`${method} Request: ${url}`);
    }
  }
};

export interface LoginResponse {
  success: boolean;
  message: string;
  userId: string | number; // Assuming local DB ID can be number
  firebase_uid: string;
  id_token: string;
  email?: string; // Optional, da es möglicherweise nicht immer vorhanden ist (z.B. beim Standard-Login)
  username?: string; // Optional
}

export interface RegisterRequestData {
  email: string;
  password: string;
  username?: string; 
}

export interface RegisterResponse {
  id: string; // Firebase UID
  email: string
  username: string;
  message: string;
  success?: boolean; // Optional, depending on backend consistency
}

export interface GoogleLoginRequest {
  id_token: string;
}

// Die Backend-Antwort für Google-Login ist ähnlich wie die normale LoginResponse
// Daher können wir LoginResponse wiederverwenden oder eine spezifischere erstellen, falls nötig.
// Fürs Erste verwenden wir LoginResponse.

export const loginWithGoogleToken = async (idToken: string): Promise<LoginResponse> => {
  logApiCall('POST', '/auth/google-login', { id_token_length: idToken.length }); // Loggen, aber nicht das Token selbst
  try {
    const response = await axios.post<LoginResponse>(`${API_BASE_URL}/auth/google-login`, { id_token: idToken }, {
      withCredentials: true,
    });
    logDebug('Google Login Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error during Google login:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error during Google login:', error);
    }
    throw error;
  }
}

export const loginUser = async (email: string, password: string): Promise<LoginResponse> => {
  logApiCall('POST', '/auth/login', { email }); // Updated endpoint
  try {
    const response = await axios.post<LoginResponse>(`${API_BASE_URL}/auth/login`, { email, password }, {
      withCredentials: true, // Sends cookies for authentication
    });
    logDebug('Login Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error during login:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error during login:', error);
    }
    throw error;
  }
};

export const registerUser = async (userData: RegisterRequestData): Promise<RegisterResponse> => {
  logApiCall('POST', '/auth/register', userData);
  try {
    const response = await axios.post<RegisterResponse>(`${API_BASE_URL}/auth/register`, userData, {
      withCredentials: true,
    });
    logDebug('Register Response:', response.data);
    // Ensure the response has a 'success' field, or derive it.
    // For now, we assume the backend might not always send 'success' but a message indicates it.
    // A more robust way is to ensure backend sends a consistent 'success: true/false'.
    return { ...response.data, success: response.status === 200 || response.status === 201 };
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      console.error('Error during registration:', error.response.data);
      // Return the error response from the backend, which should include a message
      // and potentially a success = false field or rely on status code.
      return { 
        ...(error.response.data as any), 
        success: false, 
        message: (error.response.data as any).detail || (error.response.data as any).message || 'Registration failed due to server error.' 
      };
    } else {
      console.error('Unexpected error during registration:', error);
      throw error; // Or return a generic error object
    }
  }
};

export const logoutUser = async () => {
  logApiCall('POST', '/logout');
  try {
    // Server request for logout
    const response = await axios.post(`${API_BASE_URL}/logout`, {}, {
      withCredentials: true, // Sends cookies for authentication
    });
    
    // Clear client session
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    sessionStorage.clear(); // Clear all session storage data
    
    // Optionally: Set a cookie with an expired date to delete it
    document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    // Reset Axios default headers
    if (axios.defaults.headers.common['Authorization']) {
      delete axios.defaults.headers.common['Authorization'];
    }
    
    logDebug('Logout Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error during logout:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error during logout:', error);
    }
    
    // Clear client session despite the error
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    sessionStorage.clear();
    document.cookie = 'auth_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    
    if (axios.defaults.headers.common['Authorization']) {
      delete axios.defaults.headers.common['Authorization'];
    }
    
    // Return successful status even in case of error
    return { success: true, message: "Client session cleared" };
  }
};

export const fetchFunnyTips = async () => {
  logApiCall('GET', '/funny-tips');
  try {
    const response = await axios.get(`${API_BASE_URL}/funny-tips`, {
      withCredentials: true,
    });
    logDebug('Funny Tips Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching funny tips:', error);
    throw error;
  }
};

export const GetUserInfo = async (userId: string) => {
  logApiCall('GET', `/user/${userId}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/user/${userId}`, {
      withCredentials: true,
    });
    logDebug('User Info Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching user info:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

export const GetPortfolioData = async (userId: string) => {
  logApiCall('GET', `/user/portfolio/${userId}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/user/portfolio/${userId}`, {
      withCredentials: true,
    });
    logDebug('Portfolio Data Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching portfolio data:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

export const GetRecentTransactions = async (userId: string) => {
  logApiCall('GET', `/user/transactions/${userId}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/user/transactions/${userId}`, {
      withCredentials: true,
    });
    logDebug('Recent Transactions Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching recent transactions:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

export const GetDailyQuiz = async () => {
  logApiCall('GET', '/daily-quiz');
  try {
    const response = await axios.get(`${API_BASE_URL}/daily-quiz`, {
      withCredentials: true,
    });
    logDebug('Daily Quiz Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching daily quiz:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

// Add new types and function for submitting daily quiz answer
export interface DailyQuizAttemptPayload {
  quiz_id: string;
  selected_answer: string;
}

export interface DailyQuizAttemptResponse {
  success: boolean;
  is_correct: boolean;
  correct_answer: string;
  explanation?: string;
  xp_gained?: number;
  message?: string;
  selected_answer?: string; // Ensure this field is part of the interface if not already
  quiz_id?: string; // Added quiz_id as an optional field
}

export const SubmitDailyQuizAnswer = async (payload: DailyQuizAttemptPayload): Promise<DailyQuizAttemptResponse> => {
  // Corrected endpoint: Removed /education prefix to align with how GetDailyQuiz is successfully called
  logApiCall('POST', '/daily-quiz/attempt', payload);
  try {
    const response = await axios.post(`${API_BASE_URL}/daily-quiz/attempt`, payload, {
      withCredentials: true,
    });
    logDebug('Submit Daily Quiz Answer Response:', response.data);
    return response.data; // Ensure this matches DailyQuizAttemptResponse
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error submitting daily quiz answer:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error submitting daily quiz answer:', error);
    }
    // Return a default error response object
    return {
      success: false,
      is_correct: false,
      correct_answer: '',
      message: 'Failed to submit quiz answer.',
    };
  }
};

export const GetDailyQuizAttemptToday = async (): Promise<DailyQuizAttemptResponse> => {
  logApiCall('GET', '/daily-quiz/attempt/today');
  try {
    const response = await axios.get(`${API_BASE_URL}/daily-quiz/attempt/today`, {
      withCredentials: true,
    });
    logDebug('Get Daily Quiz Attempt Today Response:', response.data);
    // The backend returns success: false if no attempt is found, which is a valid scenario.
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching daily quiz attempt for today:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error fetching daily quiz attempt for today:', error);
    }
    // Return a default error-like response to indicate failure in fetching
    return {
      success: false, // Explicitly false to indicate an issue with the fetch itself
      is_correct: false,
      correct_answer: '',
      message: 'Failed to fetch today\'s quiz attempt status.',
      xp_gained: 0,
      // selected_answer will be undefined by default if not set
    };
  }
};

export const GetAssets = async (type?: string, activeOnly: boolean = true) => {
  const queryParams = new URLSearchParams();
  if (type) queryParams.append('type', type);
  queryParams.append('active_only', activeOnly.toString());

  logApiCall('GET', `/assets?${queryParams.toString()}`);
  try {
    const response = await axios.get(`${API_BASE_URL}/assets?${queryParams.toString()}`, {
      withCredentials: true,
    });
    logDebug('Assets Response:', response.data);

    // Ensure we always return an array
    let result = response.data;
    if (!Array.isArray(result)) {
      if (result && typeof result === 'object') {
        // Search for an array property in the response
        const possibleArrayKey = Object.keys(result).find(key => Array.isArray(result[key]));
        if (possibleArrayKey) {
          result = result[possibleArrayKey];
        } else {
          // Fallback to empty array
          console.warn('Assets API returned non-array data:', result);
          result = [];
        }
      } else {
        result = [];
      }
    }
    return result;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching assets:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    // Return empty array in case of errors
    return [];
  }
};

export const GetStockData = async (symbol: string, timeframe: string) => {
  const params = { symbol, timeframe };
  logApiCall('GET', '/stock-data', params);
  try {
    const response = await axios.get(`${API_BASE_URL}/stock-data`, {
      params,
      withCredentials: true,
    });
    logDebug('Stock Data Response:', { symbol, timeframe, dataPoints: response.data.length });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching stock data:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

export const BuyStock = async (symbol: string, quantity: number, price: number) => {
  const payload = { symbol, quantity, price };
  logApiCall('POST', '/trade/buy', payload);
  try {
    const response = await axios.post(`${API_BASE_URL}/trade/buy`,
      payload,
      { withCredentials: true }
    );
    logDebug('Buy Stock Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error buying stock:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

export const SellStock = async (symbol: string, quantity: number, price: number) => {
  const payload = { symbol, quantity, price };
  logApiCall('POST', '/trade/sell', payload);
  try {
    const response = await axios.post(`${API_BASE_URL}/trade/sell`,
      payload,
      { withCredentials: true }
    );
    logDebug('Sell Stock Response:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error selling stock:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
};

// Definition für die Struktur der einzelnen Nachrichten-Assets, wie sie von der API erwartet/geliefert werden.
// Idealerweise würde dies aus einer gemeinsamen Typendatei importiert, wenn sie auch in NewsPage.tsx verwendet wird.
interface ApiNewsAsset {
  id: number | string;
  symbol: string;      // Wird als Quelle verwendet
  name: string;        // Wird als Überschrift verwendet
  asset_type: string;  // Wird als Kategorie verwendet
  default_price?: number | null;
  url?: string;         // Hinzugefügtes Feld für die Artikel-URL
}

// Definition für die gesamte Antwortstruktur des /news/-Endpunkts
interface NewsApiResponseData {
    success: boolean;
    assets: ApiNewsAsset[];
    message?: string;
}

export const getNews = async (): Promise<ApiNewsAsset[]> => {
  logApiCall('GET', '/news/');
  try {
    const response = await axios.get<NewsApiResponseData>(`${API_BASE_URL}/news/`, {
      withCredentials: true,
    });
    logDebug('News Response:', response.data);
    if (response.data && response.data.success && Array.isArray(response.data.assets)) {
      return response.data.assets;
    } else {
      console.error('Invalid news data structure from API:', response.data);
      return []; 
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching news:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error fetching news:', error);
    }
    return []; // Leeres Array im Fehlerfall
  }
};