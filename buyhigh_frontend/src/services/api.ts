const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface RegisterData {
  email: string;
  password: string;
  username?: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface AuthResponse {
  success: boolean;
  message: string;
  userId?: string;
  firebase_uid?: string;
  id_token?: string;
  // For registration specific response
  id?: string; // Firebase UID from registration
  username?: string;
}

export const registerUser = async (userData: RegisterData): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to register');
  }
  return response.json();
};

export const loginUser = async (userData: LoginData): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to login');
  }
  return response.json();
};

// Add other API functions here as needed (e.g., getNews, etc.)
export const getNews = async () => {
  const response = await fetch(`${API_BASE_URL}/news/`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch news');
  }
  const data = await response.json();
  return data.assets; // Assuming the backend returns { success: bool, assets: [] }
};
