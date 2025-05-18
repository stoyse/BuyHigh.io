import React, { useState, useEffect } from 'react';
import { GetAssets, GetStockData } from '../../apiService';
import ReactApexChart from 'react-apexcharts';

import './Trade.css';

interface Stock {
  id: string;
  symbol: string;
  name: string;
  price?: number; // Optional kennzeichnen
  change_24h?: number; // Optional kennzeichnen
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

  // Lade Aktien beim ersten Render
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        setLoading(true);
        const response = await GetAssets('stock');
        
        // Prüfen, ob die Antwort ein Array ist oder ein Objekt mit einer data-Eigenschaft
        let stocksArray: Stock[] = [];
        
        if (Array.isArray(response)) {
          stocksArray = response;
        } else if (response && typeof response === 'object') {
          // Prüfen, ob es eine data-Eigenschaft gibt, die ein Array ist
          if (response.data && Array.isArray(response.data)) {
            stocksArray = response.data;
          } else {
            // Wenn es keine data-Eigenschaft gibt, versuchen wir, die Werte zu extrahieren
            const possibleArray = Object.values(response).find(item => Array.isArray(item));
            if (possibleArray) {
              stocksArray = possibleArray as Stock[];
            }
          }
        }
        
        // Filtere ungültige oder unvollständige Aktiendaten
        stocksArray = stocksArray.filter(stock => 
          stock && 
          stock.id && 
          stock.symbol && 
          stock.name
        );
        
        console.log('Stocks data received:', stocksArray);
        setStocks(stocksArray);
        
        if (stocksArray.length > 0) {
          setSelectedStock(stocksArray[0]);
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

  // Lade Chartdaten wenn sich die ausgewählte Aktie oder der Zeitrahmen ändert
  useEffect(() => {
    const fetchChartData = async () => {
      if (!selectedStock) return;

      try {
        setLoading(true);
        const data = await GetStockData(selectedStock.symbol, timeframe);
        
        // Sicherstellen, dass wir mit einem Array arbeiten
        let chartDataArray = Array.isArray(data) ? data : (data?.data || []);
        
        console.log("Empfangene Chartdaten:", chartDataArray[0]); // Log für Debugging
        
        // Konvertiere API-Daten ins Candlestick-Format
        const formattedData = chartDataArray
          .map((item: StockDataItem) => {
            // Parsen des Datums in einen Timestamp
            const timestamp = item.date ? new Date(item.date).getTime() : null;
            
            // Nur gültige Datenpunkte zurückgeben
            if (timestamp === null) return null;
            
            return {
              // Verwende Timestamp (Nummer) statt Date-Objekt
              x: timestamp, 
              y: [
                // Stelle sicher, dass die Werte Zahlen sind
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

  // Chart-Konfiguration
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
      // Automatische Berechnung des Min/Max-Bereichs mit etwas Puffer
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

  return (
    <div className="trade-container">
      <h1>Aktienhandel</h1>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="trade-layout">
        <div className="stocks-list glass-card">
          <h2 className="gradient-text">Verfügbare Aktien</h2>
          {loading && !stocks.length ? (
            <p>Lade Aktien...</p>
          ) : stocks.length > 0 ? (
            <ul className="stock-list">
              {stocks.map((stock) => (
                <li 
                  key={stock.id} 
                  className={`stock-item ${selectedStock?.symbol === stock.symbol ? 'selected selected-stock' : ''}`}
                  onClick={() => handleStockSelect(stock)}
                >
                  <div className="stock-symbol">{stock.symbol}</div>
                  <div className="stock-name">{stock.name}</div>
                  <div className={`stock-price ${(stock.change_24h || 0) >= 0 ? 'positive' : 'negative'}`}>
                    {/* Hier fügen wir Null-Checks hinzu */}
                    {typeof stock.price === 'number' ? stock.price.toFixed(2) : 'N/A'}
                    <span className="change">
                      {typeof stock.change_24h === 'number' ? (
                        <>
                          {stock.change_24h >= 0 ? '+' : ''}{stock.change_24h.toFixed(2)}%
                        </>
                      ) : 'N/A'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>Keine Aktien verfügbar. Bitte versuchen Sie es später erneut.</p>
          )}
        </div>
        
        <div className="chart-section glass-card">
          <div className="chart-controls">
            <h2 className="gradient-text">Chart: {selectedStock?.symbol || 'Keine Aktie ausgewählt'}</h2>
            <div className="timeframe-selector">
              <label htmlFor="timeframe">Zeitraum:</label>
              <select id="timeframe" value={timeframe} onChange={handleTimeframeChange}>
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
            <div className="chart-loading">Lade Chart-Daten...</div>
          ) : (
            chartData.length > 0 ? (
              <div className="chart-container">
                <ReactApexChart
                  options={chartOptions as any}
                  series={[{ data: chartData }]}
                  type="candlestick"
                  height={500}
                />
              </div>
            ) : (
              <div className="no-data">Keine Daten verfügbar für {selectedStock?.symbol || 'die ausgewählte Aktie'}</div>
            )
          )}

          {selectedStock && (
            <div className="trading-actions">
              <button className="buy-button">Kaufen</button>
              <button className="sell-button">Verkaufen</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Trade;
