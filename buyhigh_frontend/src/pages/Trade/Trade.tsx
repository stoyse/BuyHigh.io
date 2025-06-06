import React, { useState, useEffect, useRef, memo } from 'react';
import { GetAssets, BuyStock, SellStock } from '../../apiService';
import BaseLayout from '../../components/Layout/BaseLayout';

import './Trade.css';

// TradingView Widget Component
interface TradingViewWidgetProps {
  symbol: string;
}

const TradingViewWidget: React.FC<TradingViewWidgetProps> = memo(({ symbol }) => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    
    // Clear previous widget
    container.current.innerHTML = '';
    
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = `
      {
        "autosize": true,
        "symbol": "NASDAQ:${symbol}",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "allow_symbol_change": true,
        "support_host": "https://www.tradingview.com"
      }`;
    container.current.appendChild(script);
  }, [symbol]);

  return (
    <div className="tradingview-widget-container" ref={container} style={{ height: "100%", width: "100%" }}>
      <div className="tradingview-widget-container__widget" style={{ height: "calc(100% - 32px)", width: "100%" }}></div>
      <div className="tradingview-widget-copyright">
        <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
          <span className="blue-text">Track all markets on TradingView</span>
        </a>
      </div>
    </div>
  );
});

// TradingView Technical Analysis Widget Component
interface TradingViewTechnicalAnalysisProps {
  symbol: string;
}

const TradingViewTechnicalAnalysis: React.FC<TradingViewTechnicalAnalysisProps> = memo(({ symbol }) => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    
    // Clear previous widget
    container.current.innerHTML = '';
    
    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-technical-analysis.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = `
      {
        "interval": "1m",
        "width": 425,
        "isTransparent": false,
        "height": 450,
        "symbol": "NASDAQ:${symbol}",
        "showIntervalTabs": true,
        "displayMode": "multiple",
        "locale": "en",
        "colorTheme": "dark"
      }`;
    container.current.appendChild(script);
  }, [symbol]);

  return (
    <div className="tradingview-widget-container" ref={container} style={{ height: "450px", width: "425px" }}>
      <div className="tradingview-widget-container__widget"></div>
      <div className="tradingview-widget-copyright">
        <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
          <span className="blue-text">Track all markets on TradingView</span>
        </a>
      </div>
    </div>
  );
});

TradingViewTechnicalAnalysis.displayName = 'TradingViewTechnicalAnalysis';

interface Stock {
  id: string;
  symbol: string;
  name: string;
  price?: number | string; // Extended to allow both numbers and strings
  change_24h?: number | string; // Extended to allow both numbers and strings
  currency?: string;
}

const Trade: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [timeframe, setTimeframe] = useState<string>('1d');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [prevPrices, setPrevPrices] = useState<{[key: string]: number}>({});
  const [priceChangeClass, setPriceChangeClass] = useState<{[key: string]: string}>({});
  const [quantity, setQuantity] = useState<number>(1);
  const [tradePrice, setTradePrice] = useState<number | undefined>(undefined);
  const [executingTrade, setExecutingTrade] = useState<boolean>(false);
  const [tradeMessage, setTradeMessage] = useState<{text: string, type: 'success' | 'error' | null}>({
    text: '',
    type: null
  });

  // Load stocks on first render
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        setLoading(true);
        const response = await GetAssets('stock');
        
        let stocksArray: Stock[] = [];
        
        if (Array.isArray(response)) {
          stocksArray = response;
        } else if (response && typeof response === 'object') {
          if (response.data && Array.isArray(response.data)) {
            stocksArray = response.data;
          } else {
            const possibleArray = Object.values(response).find(item => Array.isArray(item));
            if (possibleArray) {
              stocksArray = possibleArray as Stock[];
            }
          }
        }
        
        stocksArray = stocksArray.filter(stock => 
          stock && 
          stock.id && 
          stock.symbol && 
          stock.name
        );
        
        const enrichedStocks = stocksArray.map(stock => {
          if (!stock.price) {
            const basePrice = Math.floor(Math.random() * 500) + 50;
            const change = (Math.random() * 10 - 5).toFixed(2);
            
            return {
              ...stock,
              price: basePrice,
              change_24h: parseFloat(change),
              currency: '$'
            };
          }
          return stock;
        });
        
        if (process.env.NODE_ENV === 'development' && enrichedStocks.length > 0) {
          const firstItem = enrichedStocks[0];
          console.debug('Market data loaded:', firstItem.symbol);
        }
        
        setStocks(enrichedStocks);
        
        if (enrichedStocks.length > 0) {
          setSelectedStock(enrichedStocks[0]);
        }
        setLoading(false);
      } catch (err) {
        console.error('Error fetching stocks:', err);
        setError('Error loading stocks');
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  useEffect(() => {
    const newPriceChanges: {[key: string]: string} = {};
    const newPrices: {[key: string]: number} = {};
    
    stocks.forEach(stock => {
      if (!stock.id || typeof stock.price === 'undefined') return;
      
      const currentPrice = typeof stock.price === 'string' ? 
        parseFloat(stock.price) : stock.price;
      
      if (isNaN(currentPrice)) return;
      
      const prevPrice = prevPrices[stock.id];
      
      if (prevPrice) {
        if (currentPrice > prevPrice) {
          newPriceChanges[stock.id] = 'price-up';
        } else if (currentPrice < prevPrice) {
          newPriceChanges[stock.id] = 'price-down';
        }
      }
      
      newPrices[stock.id] = currentPrice;
    });
    
    setPrevPrices(newPrices);
    setPriceChangeClass(newPriceChanges);
    
    const timer = setTimeout(() => {
      setPriceChangeClass({});
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [stocks]);

  useEffect(() => {
    if (selectedStock && typeof selectedStock.price === 'number') {
      setTradePrice(selectedStock.price);
    } else if (selectedStock && typeof selectedStock.price === 'string') {
      const parsedPrice = parseFloat(selectedStock.price);
      if (!isNaN(parsedPrice)) {
        setTradePrice(parsedPrice);
      }
    }
  }, [selectedStock]);

  const formatPrice = (price: number | string | undefined, currency: string = '$'): string => {
    if (price === undefined || price === null) return 'N/A';
    
    let numericPrice: number;
    
    if (typeof price === 'string') {
      numericPrice = parseFloat(price);
    } else {
      numericPrice = price;
    }
    
    if (isNaN(numericPrice)) return 'N/A';
    
    if (numericPrice >= 1000) {
      return `${currency}${numericPrice.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    } else if (numericPrice >= 10) {
      return `${currency}${numericPrice.toFixed(2)}`;
    } else {
      return `${currency}${numericPrice.toFixed(3)}`;
    }
  };
  
  const formatPercentage = (percentage: number | string | undefined): string => {
    if (typeof percentage === 'undefined') return 'N/A';
    
    const numericPercentage = typeof percentage === 'string' ? 
      parseFloat(percentage) : percentage;
    
    if (isNaN(numericPercentage)) return 'N/A';
    
    return `${numericPercentage >= 0 ? '+' : ''}${numericPercentage.toFixed(2)}%`;
  };

  const handleStockSelect = (stock: Stock) => {
    setSelectedStock(stock);
  };

  const handleTimeframeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setTimeframe(event.target.value);
  };

  const handleBuy = async () => {
    if (!selectedStock || !tradePrice) return;
    
    setExecutingTrade(true);
    setTradeMessage({ text: '', type: null });
    
    try {
      const result = await BuyStock(selectedStock.symbol, quantity, tradePrice);
      setTradeMessage({ 
        text: `Successfully bought ${quantity} shares of ${selectedStock.symbol} at ${formatPrice(tradePrice)}!`, 
        type: 'success' 
      });
      console.log('Buy transaction successful:', result);
    } catch (error) {
      setTradeMessage({ 
        text: `Error during purchase: ${error instanceof Error ? error.message : 'Unknown error'}`, 
        type: 'error' 
      });
      console.error('Buy transaction failed:', error);
    } finally {
      setExecutingTrade(false);
    }
  };

  const handleSell = async () => {
    if (!selectedStock || !tradePrice) return;
    
    setExecutingTrade(true);
    setTradeMessage({ text: '', type: null });
    
    try {
      const result = await SellStock(selectedStock.symbol, quantity, tradePrice);
      setTradeMessage({ 
        text: `Successfully sold ${quantity} shares of ${selectedStock.symbol} at ${formatPrice(tradePrice)}!`, 
        type: 'success' 
      });
      console.log('Sell transaction successful:', result);
    } catch (error) {
      setTradeMessage({ 
        text: `Error during sale: ${error instanceof Error ? error.message : 'Unknown error'}`, 
        type: 'error' 
      });
      console.error('Sell transaction failed:', error);
    } finally {
      setExecutingTrade(false);
    }
  };

  return (
    <BaseLayout title="Trade Dashboard">
      <div className="trade-container">
        <h1 className="text-2xl font-bold mb-4 gradient-text">Stock Trading</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="trade-layout">
          <div className="stocks-list glass-card dark:bg-gray-800/40 dark:border-gray-700/30">
            <h2 className="gradient-text text-xl mb-3">Available Stocks</h2>
            {loading && !stocks.length ? (
              <div className="flex justify-center py-10">
                <div className="loader"></div>
              </div>
            ) : stocks.length > 0 ? (
              <ul className="stock-list">
                {stocks.map((stock) => (
                  <li 
                    key={stock.id} 
                    className={`stock-item ${selectedStock?.symbol === stock.symbol ? 'selected selected-stock' : ''} dark:hover:bg-gray-700/30 dark:border-gray-700/20`}
                    onClick={() => handleStockSelect(stock)}
                  >
                    <div className="stock-symbol dark:text-white">{stock.symbol}</div>
                    <div className="stock-name dark:text-gray-300">{stock.name}</div>
                    <div className={`stock-price ${priceChangeClass[stock.id] || ''}`}>
                      <div className="price-value">
                        {formatPrice(stock.price, stock.currency || '$')}
                      </div>
                      <span className={`change ${(parseFloat(String(stock.change_24h || 0)) >= 0) ? 'positive' : 'negative'}`}>
                        {formatPercentage(stock.change_24h)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-center py-10 text-gray-500 dark:text-gray-400">No stocks available. Please try again later.</p>
            )}
          </div>
          
          <div className="right-panel">
            <div className="chart-section glass-card dark:bg-gray-800/40 dark:border-gray-700/30">
              <div className="chart-controls">
                <h2 className="gradient-text text-xl">{selectedStock?.symbol || 'No stock selected'}</h2>
                <div className="timeframe-selector">
                  <label htmlFor="timeframe" className="text-sm mr-2 text-gray-600 dark:text-gray-300">Timeframe:</label>
                  <select 
                    id="timeframe" 
                    value={timeframe} 
                    onChange={handleTimeframeChange}
                    className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm px-3 py-1"
                  >
                    <option value="1d">1 Day</option>
                    <option value="1w">1 Week</option>
                    <option value="1m">1 Month</option>
                    <option value="3m">3 Months</option>
                    <option value="1y">1 Year</option>
                    <option value="5y">5 Years</option>
                  </select>
                </div>
              </div>
              
              <div className="chart-and-analysis-container" style={{ display: "flex", gap: "16px" }}>
                <div className="chart-wrapper" style={{ flex: "1" }}>
                  {selectedStock ? (
                    <div className="chart-container" style={{ height: "500px" }}>
                      <TradingViewWidget symbol={selectedStock.symbol} />
                    </div>
                  ) : (
                    <div className="no-data dark:text-gray-400">
                      <svg className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                      </svg>
                      <p>Please select a stock to view the chart</p>
                    </div>
                  )}
                </div>
                
                {selectedStock && (
                  <div className="technical-analysis-wrapper">
                    <TradingViewTechnicalAnalysis symbol={selectedStock.symbol} />
                  </div>
                )}
              </div>
            </div>

            {selectedStock && (
              <div className="trade-execution-card glass-card dark:bg-gray-800/40 dark:border-gray-700/30 mt-4">
                <h2 className="gradient-text text-xl mb-3">Execute Trade</h2>
                
                <div className="trade-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Stock</label>
                      <div className="stock-badge">
                        <span className="stock-symbol-badge">{selectedStock.symbol}</span>
                        <span className="stock-price-badge">
                          {formatPrice(selectedStock.price, selectedStock.currency || '$')}
                        </span>
                      </div>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quantity</label>
                      <div className="input-with-buttons">
                        <button 
                          className="qty-btn" 
                          onClick={() => setQuantity(prev => Math.max(1, prev - 1))}
                          disabled={quantity <= 1}
                        >−</button>
                        <input
                          type="number"
                          id="quantity"
                          min="1"
                          value={quantity}
                          onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                          className="quantity-input dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        />
                        <button 
                          className="qty-btn" 
                          onClick={() => setQuantity(prev => prev + 1)}
                        >+</button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="form-group mt-4">
                    <label htmlFor="price" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Price ($)</label>
                    <input
                      type="number"
                      id="price"
                      step="0.01"
                      min="0.01"
                      value={tradePrice}
                      onChange={(e) => setTradePrice(parseFloat(e.target.value) || undefined)}
                      className="price-input dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      placeholder="Enter price"
                    />
                  </div>
                  
                  <div className="total-calculation mt-3">
                    <div className="flex justify-between items-center text-sm font-medium">
                      <span className="text-gray-600 dark:text-gray-400">Total Value:</span>
                      <span className="text-gray-800 dark:text-gray-200">
                        {tradePrice ? formatPrice(tradePrice * quantity) : 'N/A'}
                      </span>
                    </div>
                  </div>
                  
                  {tradeMessage.text && (
                    <div className={`trade-message mt-3 p-2 rounded text-sm 
                      ${tradeMessage.type === 'success' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}
                      ${tradeMessage.type === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : ''}
                    `}>
                      {tradeMessage.text}
                    </div>
                  )}
                  
                  <div className="trading-actions mt-4">
                    <button 
                      className="buy-button neo-button" 
                      onClick={handleBuy}
                      disabled={executingTrade || !tradePrice}
                    >
                      {executingTrade ? (
                        <span className="flex items-center">
                          <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Buying...
                        </span>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                          </svg>
                          Buy
                        </>
                      )}
                    </button>
                    <button 
                      className="sell-button neo-button" 
                      onClick={handleSell}
                      disabled={executingTrade || !tradePrice}
                    >
                      {executingTrade ? (
                        <span className="flex items-center">
                          <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Selling...
                        </span>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 12H6"></path>
                          </svg>
                          Sell
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
            
            {selectedStock && (
              <div className="technical-analysis-card glass-card dark:bg-gray-800/40 dark:border-gray-700/30 mt-4">
                <h2 className="gradient-text text-xl mb-3">Technical Analysis</h2>
                
                <div className="analysis-widget-container" style={{ position: 'relative', width: '100%', height: '450px' }}>
                  <TradingViewTechnicalAnalysis symbol={selectedStock.symbol} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default Trade;
