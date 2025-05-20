import axios from 'axios';

const rawApiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:9876/api'; // Fallback für den Fall, dass die Umgebungsvariable fehlt
const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, ""); // Entfernt einen abschließenden Schrägstrich, falls vorhanden
const DEBUG = true; // Debug-Modus aktivieren/deaktivieren

// Debug-Logging-Funktion
const logDebug = (message: string, data: any = null) => {
  if (!DEBUG) return;

  const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
  console.debug(`[${timestamp}]`, message, data);
};

// Hilfsfunktion zum Loggen von API-Aufrufen
const logApiCall = (method: string, endpoint: string, params?: any) => {
  const url = `${API_BASE_URL}${endpoint}`;

  if (params) {
    logDebug(`${method} Request: ${url}`, params);
  } else {
    logDebug(`${method} Request: ${url}`);
  }
};

export const loginUser = async (email: string, password: string) => {
  logApiCall('POST', '/login', { email });
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, { email, password }, {
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
      if (error.response?.status === 401) {
        console.error('User is not authenticated. Redirecting to login.');
        window.location.href = '/login';
      }
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

    // Sicherstellen, dass wir immer ein Array zurückgeben
    let result = response.data;
    if (!Array.isArray(result)) {
      if (result && typeof result === 'object') {
        // Suchen nach einem Array-Property in der Response
        const possibleArrayKey = Object.keys(result).find(key => Array.isArray(result[key]));
        if (possibleArrayKey) {
          result = result[possibleArrayKey];
        } else {
          // Fallback zu leerem Array
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
    // Bei Fehlern leeres Array zurückgeben
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