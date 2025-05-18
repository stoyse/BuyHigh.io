import React from 'react';
import BaseLayout from '../../components/Layout/BaseLayout';
import './Dashboard.css';

const Dashboard: React.FC = () => {
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
          {/* Example Card */}
          <div className="glass-card p-5 rounded-2xl stat-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 bg-neo-purple/10 rounded-full blur-xl"></div>
            <div className="relative">
              <div className="flex items-center mb-3">
                <div className="bg-neo-purple/10 p-2 rounded-lg mr-3">
                  <svg
                    className="w-6 h-6 text-neo-purple"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path>
                  </svg>
                </div>
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300">Current Balance</h3>
              </div>
              <div className="ml-11">
                <div className="text-2xl font-bold text-gray-800 dark:text-gray-100 flex items-end space-x-1">
                  <span className="counter">$0.00</span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Available for trading</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default Dashboard;

