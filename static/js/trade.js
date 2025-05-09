document.addEventListener('DOMContentLoaded', function() {
  const DEBUG = true; // Schalter für erhöhtes Logging

  // Globale Variablen für Symbol, Zeitrahmen etc.
  let currentSymbol = null;
  let currentTimeframe = '3M';
  let chart = null;
  let currentStockPrice = 0;
  let initialStockPrice = 0;
  let liveUpdateIntervalId = null;
  const LIVE_UPDATE_INTERVAL_MS = 60000;

  // Verbesserte Logging-Funktion
  function logDebug(message, data = null) {
    if (!DEBUG) return;
    
    const logStyle = "background: #0047AB; color: white; padding: 2px 5px; border-radius: 3px;";
    if (data) {
      console.log(`%c[BuyHigh Debug]`, logStyle, message, data);
    } else {
      console.log(`%c[BuyHigh Debug]`, logStyle, message);
    }
  }
  
  // Hilfsfunktion für Zahlenformatierung
  function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1000000000) return (num / 1000000000).toFixed(1) + 'B';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  }

  // Hilfsfunktion für Demo-Daten: Anzahl Einheiten pro Zeitraum
  function getTimeframeUnits(timeframe) {
    switch (timeframe) {
      case '1MIN': return 240;
      case '1W': return 7;
      case '1M': return 30;
      case '3M': return 90;
      case '6M': return 180;
      case '1Y': return 365;
      case 'ALL': return 1825;
      default: return 90;
    }
  }

  // Funktion zum Laden des Benutzerkontostands
  function loadUserBalance() {
    fetch('/api/portfolio')
      .then(response => response.json())
      .then(data => {
        if (data.success && data.balance !== null) {
          document.getElementById('user-balance').textContent = `€${parseFloat(data.balance).toFixed(2)}`;
        } else if (data.message) {
          console.error("Error fetching balance: ", data.message);
          document.getElementById('user-balance').textContent = 'N/A';
        }
      })
      .catch(error => {
        console.error('Error fetching user balance:', error);
        document.getElementById('user-balance').textContent = 'Fehler';
      });
  }
  
  // Funktion zum Laden von Aktiendaten
  function loadStockData(symbol, timeframe, preserveInitialPrice = false) {
    logDebug(`Loading stock data for ${symbol}, timeframe: ${timeframe}, preserve price: ${preserveInitialPrice}`);
    
    // Show loading state
    document.getElementById('candlestick-chart').classList.add('opacity-50');

    // Live-Updates stoppen, bevor neue Daten geladen werden
    if (liveUpdateIntervalId) {
      clearInterval(liveUpdateIntervalId);
      liveUpdateIntervalId = null;
    }
    
    chart.updateOptions({
      xaxis: {
        labels: {
          formatter: function (value, timestamp, opts) {
            if (timeframe === '1MIN') {
              return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            return new Date(timestamp).toLocaleDateString([], { year: '2-digit', month: 'short', day: 'numeric' });
          }
        }
      }
    });

    // Save the initial stock price if this is the first load for this symbol
    if (preserveInitialPrice && initialStockPrice > 0) {
      logDebug(`📌 Preserving initial price: $${initialStockPrice.toFixed(2)} for ${symbol}`);
    }

    fetch(`/api/stock-data?symbol=${symbol}&timeframe=${timeframe}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.error) {
          throw new Error(data.error);
        }
        
        logDebug(`✅ API Success: Received ${data.length} data points for ${symbol}`);
        
        // Update chart without changing the buy price if preserveInitialPrice is true
        if (preserveInitialPrice && initialStockPrice > 0) {
          updateChartOnly(symbol, data);
        } else {
          updateChartAndStats(symbol, data);
        }
        
        document.getElementById('candlestick-chart').classList.remove('opacity-50');

        // Live-Updates starten, wenn 1MIN ausgewählt ist, aber nur für Chart-Updates
        if (timeframe === '1MIN') {
          logDebug(`Starting live updates for ${symbol} 1MIN data`);
          liveUpdateIntervalId = setInterval(() => {
            fetchLatestData(symbol, timeframe, preserveInitialPrice);
          }, LIVE_UPDATE_INTERVAL_MS);
        }
      })
      .catch(error => {
        logDebug(`⚠️ API Error: ${error.message} for ${symbol}, using demo data`);
        
        // Bei Fehler Demo-Daten verwenden, aber originalen Preis beibehalten
        if (preserveInitialPrice && initialStockPrice > 0) {
          useDemoDataPreservePrice(symbol, timeframe);
        } else {
          useDemoData(symbol, timeframe);
        }
        
        document.getElementById('candlestick-chart').classList.remove('opacity-50');

        // Live-Updates für Demo-Daten, aber nur für Chart-Updates
        if (timeframe === '1MIN') {
          logDebug(`Starting demo live updates for ${symbol} 1MIN data`);
          liveUpdateIntervalId = setInterval(() => {
            if (preserveInitialPrice && initialStockPrice > 0) {
              useDemoDataPreservePrice(symbol, timeframe);
            } else {
              useDemoData(symbol, timeframe);
            }
          }, LIVE_UPDATE_INTERVAL_MS);
        }
      });
  }
  
  // Neue Funktion: Aktualisiert nur das Chart ohne den Kaufpreis zu ändern
  function updateChartOnly(symbol, apiData) {
    const chartData = apiData.map(item => ({
      x: new Date(item.date),
      y: [
        parseFloat(item.open).toFixed(2), 
        parseFloat(item.high).toFixed(2), 
        parseFloat(item.low).toFixed(2), 
        parseFloat(item.close).toFixed(2)
      ]
    }));
        
    chart.updateSeries([{
      name: symbol,
      data: chartData
    }]);
    
    if (apiData.length > 0) {
      const lastDataPoint = apiData[apiData.length - 1];
      
      // Nur die Chart-bezogenen Elemente aktualisieren, nicht den Kaufpreis
      document.getElementById('stock-high').textContent = `$${parseFloat(lastDataPoint.high).toFixed(2)}`;
      document.getElementById('stock-low').textContent = `$${parseFloat(lastDataPoint.low).toFixed(2)}`;
      document.getElementById('stock-volume').textContent = formatNumber(lastDataPoint.volume);
      
      const marketCap = calculateMarketCap(symbol, parseFloat(lastDataPoint.close));
      document.getElementById('stock-market-cap').textContent = formatCurrency(marketCap);
      
      logDebug(`📊 Chart updated for ${symbol}, using chartData close: $${parseFloat(lastDataPoint.close).toFixed(2)}, but keeping purchase price at $${currentStockPrice.toFixed(2)}`);
    }
  }
  
  // Neue Funktion: Demo-Daten verwenden, aber den ursprünglichen Preis beibehalten
  function useDemoDataPreservePrice(symbol, timeframe) {
    const units = getTimeframeUnits(timeframe);
    const startPrice = initialStockPrice > 0 ? initialStockPrice : getStartPrice(symbol);
    const isMinutes = timeframe === '1MIN';
    
    logDebug(`📊 Generating demo data using startPrice: $${startPrice.toFixed(2)} for ${symbol}`);
    
    const demoDataForChart = generateCandlestickData(units, startPrice, isMinutes);
    
    chart.updateSeries([{
      name: symbol,
      data: demoDataForChart
    }]);
    
    if (demoDataForChart.length > 0) {
      const lastDemoCandle = demoDataForChart[demoDataForChart.length - 1].y;
      
      // Behalte den Preis bei, aktualisiere nur das Chart
      document.getElementById('stock-high').textContent = `$${parseFloat(lastDemoCandle[1]).toFixed(2)}`;
      document.getElementById('stock-low').textContent = `$${parseFloat(lastDemoCandle[2]).toFixed(2)}`;
      document.getElementById('stock-volume').textContent = formatNumber(Math.floor(Math.random() * (isMinutes ? 50000 : 10000000) + (isMinutes ? 1000 : 500000)));
      
      const marketCap = calculateMarketCap(symbol, currentStockPrice);
      document.getElementById('stock-market-cap').textContent = formatCurrency(marketCap);
      
      logDebug(`📊 Demo chart updated for ${symbol}, last close: $${parseFloat(lastDemoCandle[3]).toFixed(2)}, but keeping purchase price at $${currentStockPrice.toFixed(2)}`);
    }
  }
  
  // Funktion zum Abholen der neuesten Daten für Live-Updates
  function fetchLatestData(symbol, timeframe, preserveInitialPrice = false) {
    logDebug(`Fetching latest data for ${symbol}, timeframe: ${timeframe}`);
    
    fetch(`/api/stock-data?symbol=${symbol}&timeframe=${timeframe}`)
      .then(response => {
        if (!response.ok) {
          logDebug(`⚠️ Live update fetch failed for ${symbol}`);
          return; 
        }
        return response.json();
      })
      .then(data => {
        if (data && !data.error && data.length > 0) {
          logDebug(`✅ Live update received: ${data.length} points for ${symbol}`);
          
          // Update chart without changing the buy price if preserveInitialPrice is true
          if (preserveInitialPrice && initialStockPrice > 0) {
            updateChartOnly(symbol, data);
          } else {
            updateChartAndStats(symbol, data);
          }
        } else if (data && data.error) {
          logDebug(`⚠️ Error in live update data for ${symbol}: ${data.error}`);
        }
      })
      .catch(error => {
        logDebug(`⚠️ Error during live update fetch for ${symbol}: ${error.message}`);
      });
  }
  
  // Set up candlestick chart
  function setupChart() {
    if (typeof ApexCharts === "undefined") {
      console.error("ApexCharts is not loaded. Bitte stelle sicher, dass <script src=\"https://cdn.jsdelivr.net/npm/apexcharts\"></script> VOR /static/js/trade.js eingebunden ist.");
      alert("Chart-Engine konnte nicht geladen werden. Bitte Seite neu laden oder Admin kontaktieren.");
      return;
    }
    const options = {
      series: [{
        name: 'Stock Data',
        data: [] // Initially empty
      }],
      chart: {
        type: 'candlestick',
        height: 350,
        toolbar: {
          show: true
        },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800
        },
        background: 'transparent'
      },
      xaxis: {
        type: 'datetime',
        labels: {
          style: {
            fontSize: '10px'
          }
        }
      },
      yaxis: {
        tooltip: {
          enabled: true
        }
      },
      tooltip: {
        enabled: true
      }
    };

    // Initialize and render the chart
    chart = new ApexCharts(document.querySelector("#candlestick-chart"), options);
    chart.render();
  }

  // Update total price based on quantity and current price
  function updateTotalPrice() {
    const quantity = parseFloat(document.getElementById('quantity').value) || 0;
    const totalPrice = quantity * currentStockPrice;
    document.getElementById('total-price').textContent = `$${totalPrice.toFixed(2)}`;
  }

  function handleTrade(action) {
    const quantity = parseFloat(document.getElementById('quantity').value) || 0;
    const price = parseFloat(currentStockPrice) || 0;

    if (quantity <= 0 || price <= 0) {
      alert("Invalid quantity or price.");
      return;
    }

    const endpoint = action === 'buy' ? '/api/trade/buy' : '/api/trade/sell';
    const payload = {
      symbol: currentSymbol,
      quantity: quantity,
      price: price
    };

    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(data.message);
        loadUserBalance();
        loadStockData(currentSymbol, currentTimeframe, true);
      } else {
        alert(data.message);
      }
    })
    .catch(error => {
      console.error('Error during trade:', error);
      alert('An error occurred during the trade.');
    });
  }

  // Initialize the page
  function initializePage() {
    setupChart();
    loadUserBalance();

    // Set up event listeners for stock items
    document.querySelectorAll('.stock-item').forEach(item => {
      item.addEventListener('click', function() {
        const symbol = this.getAttribute('data-symbol');
        const name = this.getAttribute('data-name');
        const price = this.getAttribute('data-price');
        const change = this.getAttribute('data-change');

        logDebug(`Selected stock: ${symbol} (${name}), price from HTML: $${price}, change: ${change}%`);

        // Update current symbol and price
        currentSymbol = symbol;
        currentStockPrice = parseFloat(price);
        initialStockPrice = parseFloat(price);

        // Update stock info in UI
        document.getElementById('stock-name').textContent = `${name} (${symbol})`;
        document.getElementById('stock-price').textContent = `Preis: $${price} (${change}%)`;
        document.getElementById('current-price').textContent = `$${price}`;

        // Update total based on quantity
        updateTotalPrice();

        // Load new stock data, aber behalte den ursprünglichen Preis bei
        loadStockData(symbol, currentTimeframe, true);

        // Highlight selected stock
        document.querySelectorAll('.stock-item').forEach(s => {
          s.classList.remove('border-primary-light', 'dark:border-primary-dark', 'border-2');
          s.classList.add('border-gray-200', 'dark:border-gray-700', 'border-2');
        });
        this.classList.remove('border-gray-200', 'dark:border-gray-700');
        this.classList.add('border-primary-light', 'dark:border-primary-dark', 'border-2');
      });
    });

    // Set up event listeners for timeframe buttons
    document.querySelectorAll('.timeframe-btn').forEach(button => {
      button.addEventListener('click', function() {
        // Remove active class from all buttons
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
          btn.classList.remove('bg-primary-light', 'dark:bg-primary-dark', 'text-white');
          btn.classList.add('bg-gray-200', 'dark:bg-gray-700');
        });

        // Add active class to clicked button
        this.classList.remove('bg-gray-200', 'dark:bg-gray-700');
        this.classList.add('bg-primary-light', 'dark:bg-primary-dark', 'text-white');

        // Get timeframe value
        const timeframe = this.getAttribute('data-timeframe');
        currentTimeframe = timeframe;

        logDebug(`Timeframe changed to: ${timeframe}`);

        // Load data for current symbol and new timeframe, aber behalte den Preis bei
        loadStockData(currentSymbol, currentTimeframe, true);
      });
    });

    // Set up event listeners for quantity input
    document.getElementById('quantity').addEventListener('input', updateTotalPrice);
    
    // Setup trade buttons
    document.getElementById('buy-button').addEventListener('click', () => handleTrade('buy'));
    document.getElementById('sell-button').addEventListener('click', () => handleTrade('sell'));

    // Select first stock item by default
    document.querySelector('.stock-item').click();
  }

  initializePage();
});