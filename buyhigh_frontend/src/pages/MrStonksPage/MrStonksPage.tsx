import React from 'react';
import { useNavigate } from 'react-router-dom';
import TopNavBar from '../../components/Navbar/TopNavBar';

const MrStonksPage: React.FC = () => {
  const navigate = useNavigate();

  const handleChatClick = () => {
    navigate('/chatbot');
  };

  // Mock data for TopNavBar, as it's a shared component.
  // In a real app, this would come from a global state (Context, Redux, etc.).
  const [user, setUser] = React.useState<any>(null); 
  const [darkMode, setDarkMode] = React.useState<boolean>(false);
  const handleLogout = () => {
    setUser(null);
    console.log("User logged out");
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <TopNavBar user={user} handleLogout={handleLogout} darkMode={darkMode} setDarkMode={setDarkMode} />
      <div className="flex flex-col items-center justify-center text-center pt-20 px-4">
        <img src="/mr-stonks-avatar.png" alt="Mr. Stonks" className="w-40 h-40 rounded-full mb-6 shadow-lg" />
        <h1 className="text-5xl font-bold text-gray-800 dark:text-white mb-4">Mr. Stonks</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-md">
          Your personal AI finance assistant. Ready to help you navigate the markets with data-driven insights.
        </p>
        <button 
          onClick={handleChatClick}
          className="bg-primary hover:bg-primary-dark text-white font-bold py-3 px-6 rounded-lg shadow-xl transition duration-300 ease-in-out transform hover:scale-105"
        >
          Chat with Mr. Stonks
        </button>
      </div>
    </div>
  );
};

export default MrStonksPage;
