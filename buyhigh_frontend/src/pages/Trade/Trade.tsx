import React, { useState, useEffect } from 'react';
import { GetAssets, GetStockData, BuyStock, SellStock } from '../../apiService';
import ReactApexChart from 'react-apexcharts';
import BaseLayout from '../../components/Layout/BaseLayout';

import './Trade.css';

interface Stock {
  id: string;
  symbol: string;
  name: string;
  price?: number | string; // Erweitert, um sowohl Zahlen als auch Strings zu erlauben
  change_24h?: number | string; // Erweitert, um sowohl Zahlen als auch Strings zu erlauben
  currency?: string;
}

interface CandlestickData {
  x: number; // Timestamp
  y: [number, number, number, number]; // open, high, low, close
}

interface StockDataItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  currency: string;
}

const Trade: React.FC = () => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [timeframe, setTimeframe] = useState<string>('1d');
  const [chartData, setChartData] = useState<CandlestickData[]>([]);
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

  // Lade Aktien beim ersten Render
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
        setError('Fehler beim Laden der Aktien');
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!selectedStock) return;

      try {
        setLoading(true);
        const data = await GetStockData(selectedStock.symbol, timeframe);
        
        let chartDataArray = Array.isArray(data) ? data : (data?.data || []);
        
        console.log("Empfangene Chartdaten:", chartDataArray[0]);
        
        const formattedData = chartDataArray
          .map((item: StockDataItem) => {
            const timestamp = item.date ? new Date(item.date).getTime() : null;
            
            if (timestamp === null) return null;
            
            return {
              x: timestamp, 
              y: [
                typeof item.open === 'number' ? item.open : parseFloat(String(item.open)) || 0,
                typeof item.high === 'number' ? item.high : parseFloat(String(item.high)) || 0,
                typeof item.low === 'number' ? item.low : parseFloat(String(item.low)) || 0,
                typeof item.close === 'number' ? item.close : parseFloat(String(item.close)) || 0
              ]
            } as CandlestickData;
          })
          .filter((item: CandlestickData | null): item is CandlestickData => item !== null);
        
        console.log(`${formattedData.length} Datenpunkte für Chart formatiert`);
        setChartData(formattedData);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching chart data:', err);
        setError('Fehler beim Laden der Chart-Daten');
        setLoading(false);
      }
    };

    fetchChartData();
  }, [selectedStock, timeframe]);

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

  const chartOptions = {
    chart: {
      type: 'candlestick',
      height: 500,
      background: '#f8f9fa',
      animations: {
        enabled: false
      },
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
          reset: true
        }
      }
    },
    title: {
      text: selectedStock ? `${selectedStock.name} (${selectedStock.symbol})` : 'Aktien-Chart',
      align: 'left'
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeUTC: false,
        format: 'dd MMM yyyy'
      },
      tickAmount: 10
    },
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        formatter: function(value: number) {
          return value.toFixed(2);
        }
      },
      forceNiceScale: true,
      tickAmount: 8
    },
    tooltip: {
      enabled: true,
      x: {
        format: 'dd MMM yyyy HH:mm'
      },
      y: {
        formatter: function(value: number) {
          return `$${value.toFixed(2)}`;
        }
      }
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#0cac6e',
          downward: '#d32f2f'
        },
        wick: {
          useFillColor: true
        }
      }
    },
    grid: {
      borderColor: '#f1f1f1',
      row: {
        colors: ['transparent', 'transparent'],
        opacity: 0.2
      }
    },
    responsive: [
      {
        breakpoint: 1000,
        options: {
          chart: {
            height: 400
          }
        }
      },
      {
        breakpoint: 600,
        options: {
          chart: {
            height: 300
          }
        }
      }
    ]
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
        text: `Erfolgreich ${quantity} Anteile von ${selectedStock.symbol} zu ${formatPrice(tradePrice)} gekauft!`, 
        type: 'success' 
      });
      console.log('Buy transaction successful:', result);
    } catch (error) {
      setTradeMessage({ 
        text: `Fehler beim Kauf: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`, 
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
        text: `Erfolgreich ${quantity} Anteile von ${selectedStock.symbol} zu ${formatPrice(tradePrice)} verkauft!`, 
        type: 'success' 
      });
      console.log('Sell transaction successful:', result);
    } catch (error) {
      setTradeMessage({ 
        text: `Fehler beim Verkauf: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`, 
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
        <h1 className="text-2xl font-bold mb-4 gradient-text">Aktienhandel</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="trade-layout">
          <div className="stocks-list glass-card dark:bg-gray-800/40 dark:border-gray-700/30">
            <h2 className="gradient-text text-xl mb-3">Verfügbare Aktien</h2>
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
              <p className="text-center py-10 text-gray-500 dark:text-gray-400">Keine Aktien verfügbar. Bitte versuchen Sie es später erneut.</p>
            )}
          </div>
          
          <div className="right-panel">
            <div className="chart-section glass-card dark:bg-gray-800/40 dark:border-gray-700/30">
              <div className="chart-controls">
                <h2 className="gradient-text text-xl">{selectedStock?.symbol || 'Keine Aktie ausgewählt'}</h2>
                <div className="timeframe-selector">
                  <label htmlFor="timeframe" className="text-sm mr-2 text-gray-600 dark:text-gray-300">Zeitraum:</label>
                  <select 
                    id="timeframe" 
                    value={timeframe} 
                    onChange={handleTimeframeChange}
                    className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm px-3 py-1"
                  >
                    <option value="1d">1 Tag</option>
                    <option value="1w">1 Woche</option>
                    <option value="1m">1 Monat</option>
                    <option value="3m">3 Monate</option>
                    <option value="1y">1 Jahr</option>
                    <option value="5y">5 Jahre</option>
                  </select>
                </div>
              </div>
              
              {loading && selectedStock ? (
                <div className="chart-loading">
                  <div className="loader"></div>
                  <p className="mt-3 text-gray-500 dark:text-gray-400">Lade Chart-Daten...</p>
                </div>
              ) : (
                chartData.length > 0 ? (
                  <div className="chart-container dark:bg-gray-800/70">
                    <ReactApexChart
                      options={{
                        ...chartOptions,
                        theme: {
                          mode: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
                        },
                        chart: {
                          ...chartOptions.chart,
                          background: document.documentElement.classList.contains('dark') ? '#1f2937' : '#f8f9fa',
                        },
                        grid: {
                          borderColor: document.documentElement.classList.contains('dark') ? '#374151' : '#f1f1f1',
                        },
                        xaxis: {
                          ...chartOptions.xaxis,
                          labels: {
                            ...chartOptions.xaxis.labels,
                            style: {
                              colors: document.documentElement.classList.contains('dark') ? '#d1d5db' : '#4b5563',
                            }
                          },
                        },
                        yaxis: {
                          ...chartOptions.yaxis,
                          labels: {
                            ...chartOptions.yaxis.labels,
                            style: {
                              colors: document.documentElement.classList.contains('dark') ? '#d1d5db' : '#4b5563',
                            }
                          },
                        }
                      } as any}
                      series={[{ data: chartData }]}
                      type="candlestick"
                      height={500}
                    />
                  </div>
                ) : (
                  <div className="no-data dark:text-gray-400">
                    <svg className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <p>Keine Daten verfügbar für {selectedStock?.symbol || 'die ausgewählte Aktie'}</p>
                  </div>
                )
              )}
            </div>

            {selectedStock && (
              <div className="trade-execution-card glass-card dark:bg-gray-800/40 dark:border-gray-700/30 mt-4">
                <h2 className="gradient-text text-xl mb-3">Trade ausführen</h2>
                
                <div className="trade-form">
                  <div className="form-row">
                    <div className="form-group">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Aktie</label>
                      <div className="stock-badge">
                        <span className="stock-symbol-badge">{selectedStock.symbol}</span>
                        <span className="stock-price-badge">
                          {formatPrice(selectedStock.price, selectedStock.currency || '$')}
                        </span>
                      </div>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Menge</label>
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
                    <label htmlFor="price" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preis ($)</label>
                    <input
                      type="number"
                      id="price"
                      step="0.01"
                      min="0.01"
                      value={tradePrice}
                      onChange={(e) => setTradePrice(parseFloat(e.target.value) || undefined)}
                      className="price-input dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      placeholder="Preis eingeben"
                    />
                  </div>
                  
                  <div className="total-calculation mt-3">
                    <div className="flex justify-between items-center text-sm font-medium">
                      <span className="text-gray-600 dark:text-gray-400">Gesamtwert:</span>
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
                          Kaufe...
                        </span>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                          </svg>
                          Kaufen
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
                          Verkaufe...
                        </span>
                      ) : (
                        <>
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 12H6"></path>
                          </svg>
                          Verkaufen
                        </>
                      )}
                    </button>
                  </div>
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
