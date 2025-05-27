import React, { useState, useEffect } from 'react';
import BaseLayout from '../../components/Layout/BaseLayout';
import { GetRecentTransactions } from '../../apiService';
import { useAuth } from '../../contexts/AuthContext';

interface Transaction {
  id?: number;
  asset_symbol: string;
  quantity: number;
  price_per_unit: number;
  transaction_type: 'buy' | 'sell';
  timestamp: string;
}

interface TransactionsResponse {
  success: boolean;
  transactions: Transaction[];
  message?: string;
}

const TransactionsPage: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchTransactions = async () => {
      if (!user?.id) {
        setError('User not authenticated');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // The API expects all transactions, not just recent ones for the transactions page
        // But we'll use the existing GetRecentTransactions API with a high limit
        const response: TransactionsResponse | Transaction[] = await GetRecentTransactions(String(user.id));
        
        let transactionsList: Transaction[] = [];
        
        // Handle different response formats
        if (Array.isArray(response)) {
          transactionsList = response;
        } else if (response && typeof response === 'object' && 'success' in response) {
          if (response.success && Array.isArray(response.transactions)) {
            transactionsList = response.transactions;
          } else {
            throw new Error(response.message || 'Failed to fetch transactions');
          }
        } else {
          throw new Error('Unexpected response format');
        }

        setTransactions(transactionsList);
      } catch (err) {
        console.error('Error fetching transactions:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch transactions');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [user?.id]);

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString || '-';
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const calculateTotal = (transaction: Transaction) => {
    return transaction.quantity * transaction.price_per_unit;
  };

  if (loading) {
    return (
      <BaseLayout title="Transactions - BuyHigh.io">
        <div className="container mx-auto px-4 py-6 max-w-full">
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-neo-purple"></div>
          </div>
        </div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout title="Transactions - BuyHigh.io">
      <div className="container mx-auto px-4 py-6 max-w-full">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold gradient-text mb-2 flex justify-center items-center">
            <svg className="w-8 h-8 mr-2 animate-pulse-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Transaction History
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm max-w-2xl mx-auto">
            Here you can find all your past buys and sells.
          </p>
        </header>

        {/* Error Display */}
        {error && (
          <div className="glass-card border border-red-500/20 bg-red-500/10 rounded-2xl p-4 mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span className="text-red-700 dark:text-red-300">{error}</span>
            </div>
          </div>
        )}

        {/* Transactions Table */}
        <div className="glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 overflow-x-auto">
          {transactions && transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Date
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Type
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Asset
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Amount
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Price/Unit
                    </th>
                    <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Total
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {transactions.map((tx, index) => (
                    <tr
                      key={`${tx.asset_symbol}-${tx.timestamp}-${index}`}
                      className="hover:bg-neo-purple/5 dark:hover:bg-neo-purple/10 transition-all"
                    >
                      <td className="px-4 py-2 text-xs text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {formatDate(tx.timestamp)}
                      </td>
                      <td className="px-4 py-2 text-xs font-medium whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                            tx.transaction_type === 'buy'
                              ? 'bg-neo-emerald/10 text-neo-emerald'
                              : 'bg-neo-red/10 text-neo-red'
                          }`}
                        >
                          {tx.transaction_type === 'buy' ? (
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v3m0 0v3m0-3h3m-3 0H9"></path>
                            </svg>
                          ) : (
                            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12H9"></path>
                            </svg>
                          )}
                          {tx.transaction_type === 'buy' ? 'Buy' : 'Sell'}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-xs text-gray-800 dark:text-gray-100 whitespace-nowrap font-medium">
                        {tx.asset_symbol}
                      </td>
                      <td className="px-4 py-2 text-xs text-right text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {formatAmount(tx.quantity)}
                      </td>
                      <td className="px-4 py-2 text-xs text-right text-gray-700 dark:text-gray-300 whitespace-nowrap">
                        {formatCurrency(tx.price_per_unit)}
                      </td>
                      <td
                        className={`px-4 py-2 text-xs text-right font-semibold whitespace-nowrap ${
                          tx.transaction_type === 'buy' ? 'text-neo-emerald' : 'text-neo-red'
                        }`}
                      >
                        {tx.transaction_type === 'buy' ? '-' : '+'}
                        {formatCurrency(calculateTotal(tx))}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12">
              <svg
                className="w-16 h-16 text-gray-400 dark:text-gray-600 mb-4 animate-pulse-slow"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                ></path>
              </svg>
              <h3 className="text-lg font-medium text-gray-600 dark:text-gray-300 mb-2">
                No transactions found
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                Start your first trade to fill your history!
              </p>
            </div>
          )}
        </div>
      </div>
    </BaseLayout>
  );
};

export default TransactionsPage;
