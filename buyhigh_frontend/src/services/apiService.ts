const rawApiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_BASE_URL = rawApiBaseUrl.replace(/\/$/, ""); // Remove trailing slash if present

// Function to get all users
export const getAllUsers = async () => {
  try {
    const token = localStorage.getItem('authToken');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/users/all`, {
      method: 'GET',
      headers: headers,
    });

    if (!response.ok) {
      // Try to get error details from response, default to status text or generic message
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.detail || errorMessage;
      } catch (e) {
        // Ignore if response is not JSON or other parsing error
      }
      throw new Error(errorMessage);
    }
    return await response.json(); // Assuming the backend returns { success: boolean, users: [], message?: string }
  } catch (error) {
    console.error('Error fetching all users:', error);
    // Rethrow the error so the calling component (SocialPage) can handle it
    throw error;
  }
};

// If there was other code in this file intended to be kept, 
// it would need to be reviewed. Assuming this file was primarily for getAllUsers after my previous edit.