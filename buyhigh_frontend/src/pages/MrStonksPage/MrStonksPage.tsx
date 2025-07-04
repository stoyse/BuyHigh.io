import React from 'react';
import { useNavigate } from 'react-router-dom';
import BaseLayout from '../../components/Layout/BaseLayout';

const MrStonksPage: React.FC = () => {
  const navigate = useNavigate();

  const handleChatClick = () => {
    navigate('/chatbot');
  };

  return (
    <BaseLayout title="Mr. Stonks">
      <div className="flex flex-col items-center justify-center text-center py-10 px-4">
        <img src="/mr-stonks-avatar.png" alt="Mr. Stonks" className="w-40 h-40 rounded-full mb-6 shadow-lg" />
        <h1 className="text-5xl font-bold text-gray-800 dark:text-white mb-4">Mr. Stonks</h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-md">
          Your personal AI finance assistant. Ready to help you navigate the markets with data-driven insights.
        </p>
        <button 
          onClick={handleChatClick}
          className="bg-neo-purple hover:bg-neo-blue text-white font-bold py-3 px-6 rounded-lg shadow-xl transition duration-300 ease-in-out transform hover:scale-105"
        >
          Chat with Mr. Stonks
        </button>
      </div>
    </BaseLayout>
  );
};

export default MrStonksPage;
