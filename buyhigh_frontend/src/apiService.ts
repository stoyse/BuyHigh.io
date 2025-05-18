import axios from 'axios';

const API_BASE_URL = 'http://localhost:9876/api';

export const loginUser = async (email: string, password: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/login`, { email, password }, {
      withCredentials: true, // Sends cookies for authentication
    });
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
  try {
    const response = await axios.get(`${API_BASE_URL}/funny-tips`, {
      withCredentials: true, // Sends cookies for authentication
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching funny tips:', error);
    throw error;
  }
};

export const GetUserInfo = async (userId: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/user/${userId}`, {
      withCredentials: true, // Sends cookies for authentication
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        console.error('User is not authenticated. Redirecting to login.');
        // Handle redirection to login page if needed
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
  try {
    const response = await axios.get(`${API_BASE_URL}/user/portfolio/${userId}`, {
      withCredentials: true, // Sends cookies for authentication
    });
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
  try {
    const response = await axios.get(`${API_BASE_URL}/user/transactions/${userId}`, {
      withCredentials: true, // Sends cookies for authentication
    });
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
  try {
    const response = await axios.get(`${API_BASE_URL}/daily-quiz`, {
      withCredentials: true, // Sends cookies for authentication
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Error fetching daily quiz:', error.response?.data || error.message);
    } else {
      console.error('Unexpected error:', error);
    }
    throw error;
  }
}