document.addEventListener('DOMContentLoaded', function() {
  const DEBUG = true; // Schalter für erhöhtes Logging

  // Globale Variablen für Symbol, Zeitrahmen etc.
  let currentSymbol = null;
  let currentTimeframe = '3M';
  let chart = null;
  let currentStockPrice = 0;
  let initialStockPrice = 0;
  let liveUpdateIntervalId = null;
  const LIVE_UPDATE_INTERVAL_MS = 60000; // 60 Sekunden

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
  
  // Neue Funktion, die beim Laden der Seite alle Aktienpreise aktualisiert
  function updateAllStockPrices() {
    logDebug("Updating all stock prices from API...");
    const stockItems = document.querySelectorAll('.stock-item');
    
    // Für jede Aktie in der Liste
    stockItems.forEach(item => {
      const symbol = item.getAttribute('data-symbol');
      if (!symbol) return;
      
      // API-Aufruf für aktuelle Preisdaten
      fetch(`/api/stock-data?symbol=${symbol}&timeframe=1D`)
        .then(response => response.json())
        .then(data => {
          if (data && data.length > 0) {
            const latestData = data[data.length - 1];
            const price = parseFloat(latestData.close).toFixed(2);
            
            // Alten Preis extrahieren für Vergleich
            const oldPrice = parseFloat(item.getAttribute('data-price'));
            
            // Update data-attribute
            item.setAttribute('data-price', price);
            
            // Update UI elements
            const priceElement = item.querySelector('.stock-price');
            if (priceElement) {
              // Optional: Farbanimation für Preisänderung
              if (price > oldPrice) {
                priceElement.classList.add('price-flash-up');
                setTimeout(() => priceElement.classList.remove('price-flash-up'), 1000);
              } else if (price < oldPrice) {
                priceElement.classList.add('price-flash-down');
                setTimeout(() => priceElement.classList.remove('price-flash-down'), 1000);
              }
              
              priceElement.textContent = `$${price}`;
            }
            
            // Wenn diese Aktie aktuell ausgewählt ist, auch deren Details aktualisieren
            if (currentSymbol === symbol) {
              currentStockPrice = parseFloat(price);
              document.getElementById('current-price').textContent = `$${price}`;
              updateTotalPrice();
            }
            
            logDebug(`✅ Updated price for ${symbol}: $${price}`);
          }
        })
        .catch(error => {
          logDebug(`⚠️ Error updating price for ${symbol}: ${error.message}`);
        });
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
        // Robust: Prüfe, ob data ein Array ist
        if (!Array.isArray(data)) {
          logDebug(`❌ API returned non-array data:`, data);
          throw new Error(data && data.error ? data.error : 'API returned invalid data');
        }

        logDebug(`✅ API Success: Received ${data.length} data points for ${symbol}`);
        
        // Immer updateChartAndStats aufrufen, damit die Candles aktualisiert werden!
        updateChartAndStats(symbol, data);
        
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
    const maxPoints = 300;
    // Filtere ungültige Candles heraus (inkl. Datumsprüfung)
    const validData = apiData.filter(item => {
      const dateObj = new Date(item.date);
      return !isNaN(dateObj.getTime()) &&
             item.open !== null && item.high !== null && item.low !== null && item.close !== null &&
             isFinite(item.open) && isFinite(item.high) && isFinite(item.low) && isFinite(item.close);
    });
    const slicedData = validData.length > maxPoints ? validData.slice(-maxPoints) : validData;

    const chartData = slicedData.map(item => ({
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

    if (slicedData.length > 0) {
      const lastDataPoint = slicedData[slicedData.length - 1];
      document.getElementById('stock-high').textContent = `$${parseFloat(lastDataPoint.high).toFixed(2)}`;
      document.getElementById('stock-low').textContent = `$${parseFloat(lastDataPoint.low).toFixed(2)}`;
      document.getElementById('stock-volume').textContent = formatNumber(lastDataPoint.volume);
      const marketCap = typeof calculateMarketCap === 'function' ? calculateMarketCap(symbol, parseFloat(lastDataPoint.close)) : 'N/A';
      document.getElementById('stock-market-cap').textContent = typeof formatCurrency === 'function' ? formatCurrency(marketCap) : marketCap;
      logDebug(`📊 Chart updated for ${symbol}, using chartData close: $${parseFloat(lastDataPoint.close).toFixed(2)}, but keeping purchase price at $${currentStockPrice.toFixed(2)}`);
    }
  }

  // Funktion: Chart und Stats aktualisieren (wie updateChartOnly, aber setzt auch currentStockPrice)
  function updateChartAndStats(symbol, apiData) {
    const maxPoints = 300;
    // Filtere ungültige Candles heraus (inkl. Datumsprüfung)
    const validData = apiData.filter(item => {
      const dateObj = new Date(item.date);
      return !isNaN(dateObj.getTime()) &&
             item.open !== null && item.high !== null && item.low !== null && item.close !== null &&
             isFinite(item.open) && isFinite(item.high) && isFinite(item.low) && isFinite(item.close);
    });
    const slicedData = validData.length > maxPoints ? validData.slice(-maxPoints) : validData;

    const chartData = slicedData.map(item => ({
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

    if (slicedData.length > 0) {
      const lastDataPoint = slicedData[slicedData.length - 1];
      currentStockPrice = parseFloat(lastDataPoint.close);
      document.getElementById('current-price').textContent = `$${currentStockPrice.toFixed(2)}`;
      document.getElementById('stock-high').textContent = `$${parseFloat(lastDataPoint.high).toFixed(2)}`;
      document.getElementById('stock-low').textContent = `$${parseFloat(lastDataPoint.low).toFixed(2)}`;
      document.getElementById('stock-volume').textContent = formatNumber(lastDataPoint.volume);
      const marketCap = typeof calculateMarketCap === 'function' ? calculateMarketCap(symbol, currentStockPrice) : 'N/A';
      document.getElementById('stock-market-cap').textContent = typeof formatCurrency === 'function' ? formatCurrency(marketCap) : marketCap;
      updateTotalPrice();
      logDebug(`📊 Chart and stats updated for ${symbol}, close: $${currentStockPrice.toFixed(2)}`);
    }
  }

  // Neue Funktion: Demo-Daten verwenden, aber den ursprünglichen Preis beibehalten
  function useDemoDataPreservePrice(symbol, timeframe) {
    const units = getTimeframeUnits(timeframe);
    const startPrice = initialStockPrice > 0 ? initialStockPrice : getStartPrice(symbol);
    const isMinutes = timeframe === '1MIN';
    
    logDebug(`📊 Generating demo data using startPrice: $${startPrice.toFixed(2)} for ${symbol}`);
    
    const rawDemoData = generateCandlestickData(units, startPrice, isMinutes); // Dies gibt Rohdaten zurück
    
    // Mappe Rohdaten in das ApexCharts-Format
    const apexChartFormattedDemoData = rawDemoData.map(item => ({
      x: new Date(item.date),
      y: [
        parseFloat(item.open).toFixed(2),
        parseFloat(item.high).toFixed(2),
        parseFloat(item.low).toFixed(2),
        parseFloat(item.close).toFixed(2)
      ]
    })).filter(item => { // Zusätzliche Filterung für Gültigkeit
        const dateObj = new Date(item.x);
        return !isNaN(dateObj.getTime()) &&
               item.y.every(val => val !== null && isFinite(parseFloat(val)));
    });
    
    chart.updateSeries([{
      name: symbol,
      data: apexChartFormattedDemoData // Verwende die gemappten und gefilterten Daten
    }]);
    
    if (rawDemoData.length > 0) {
      const lastRawDemoCandle = rawDemoData[rawDemoData.length - 1]; // Objekt mit .open, .high, etc.
      
      document.getElementById('stock-high').textContent = `$${parseFloat(lastRawDemoCandle.high).toFixed(2)}`;
      document.getElementById('stock-low').textContent = `$${parseFloat(lastRawDemoCandle.low).toFixed(2)}`;
      document.getElementById('stock-volume').textContent = formatNumber(lastRawDemoCandle.volume);
      
      const marketCap = typeof calculateMarketCap === 'function' ? calculateMarketCap(symbol, currentStockPrice) : 'N/A'; // currentStockPrice wird beibehalten
      document.getElementById('stock-market-cap').textContent = typeof formatCurrency === 'function' ? formatCurrency(marketCap) : marketCap;
      
      logDebug(`📊 Demo chart updated for ${symbol}, last close: $${parseFloat(lastRawDemoCandle.close).toFixed(2)}, but keeping purchase price at $${currentStockPrice.toFixed(2)}`);
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
  
  // Neue Funktion zum Laden von Asset-Details (Preis, Name, Beschreibung usw.)
  function loadAssetDetails(symbol) {
    logDebug(`Loading asset details for symbol: ${symbol}`);
    
    fetch(`/api/assets/${symbol}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.success && data.asset) {
          const asset = data.asset;
          
          // Asset-Informationen anzeigen
          document.getElementById('stock-name').textContent = `${asset.name} (${asset.symbol})`;
          
          // Weitere Asset-Informationen, wenn vorhanden
          if (asset.sector) {
            // Sektor anzeigen, wenn verfügbar
            const sectorLabel = document.createElement('span');
            sectorLabel.className = 'ml-2 text-xs px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded';
            sectorLabel.textContent = asset.sector;
            document.getElementById('stock-name').appendChild(sectorLabel);
          }
          
          // News-Button mit dem richtigen Symbol aktualisieren
          document.getElementById('news-button').href = `/news/${asset.symbol}`;
          
          logDebug(`✅ Asset details loaded for ${symbol}`, asset);
        } else {
          logDebug(`❌ Failed to load asset details for ${symbol}`);
        }
      })
      .catch(error => {
        logDebug(`⚠️ Error loading asset details: ${error.message}`);
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

  // Demo-Candlestick-Daten-Generator (einfaches Random-Walk-Modell)
  function generateCandlestickData(units, startPrice, isMinutes) {
    const data = [];
    let price = startPrice;
    if (!isFinite(price)) price = 100; // Fallback für ungültigen Startpreis

    for (let i = 0; i < units; i++) {
      const open = price;
      const change = (Math.random() - 0.5) * (isMinutes ? 0.5 : 5); // Kleinere Änderungen für Minuten
      let close = open + change;
      // Sicherstellen, dass der Preis nicht negativ wird
      if (close <= 0) close = open * (0.95 + Math.random() * 0.1); // kleiner positiver Wert relativ zu open

      const high = Math.max(open, close) + Math.random() * (isMinutes ? 0.2 : 2);
      const low = Math.min(open, close) - Math.random() * (isMinutes ? 0.2 : 2);
      
      // Sicherstellen, dass low <= open/close und high >= open/close
      const finalLow = Math.min(low, open, close);
      const finalHigh = Math.max(high, open, close);

      const volume = Math.floor(Math.random() * (isMinutes ? 50000 : 10000000) + (isMinutes ? 1000 : 500000));
      let date = new Date();
      if (isMinutes) {
        date.setMinutes(date.getMinutes() - (units - i - 1));
      } else {
        date.setDate(date.getDate() - (units - i - 1));
      }
      data.push({
        date: date.toISOString(),
        open: open,
        high: finalHigh, // Verwende finalHigh
        low: finalLow,   // Verwende finalLow
        close: close,
        volume: volume
      });
      price = close;
    }
    return data;
  }

  // Demo-Daten verwenden, wenn API nicht funktioniert
  function useDemoData(symbol, timeframe) {
    const units = getTimeframeUnits(timeframe);
    const startPrice = initialStockPrice > 0 ? initialStockPrice : getStartPrice(symbol);
    const isMinutes = timeframe === '1MIN';
    logDebug(`📊 Generating fallback demo data for ${symbol} with startPrice $${startPrice.toFixed(2)}`);
    const demoData = generateCandlestickData(units, startPrice, isMinutes);
    updateChartAndStats(symbol, demoData);
  }

  // Dummy für getStartPrice, falls nicht vorhanden
  function getStartPrice(symbol) {
    const basePrice = {"SPY": 450, "AAPL": 170, "TSLA": 250, "MSFT": 330, "AMZN": 130, "GOOGL": 140, "META": 290};
    return basePrice[symbol] || (100 + Math.random() * 400);
  }

  // Dummy-Funktionen für calculateMarketCap und formatCurrency, falls nicht vorhanden
  function calculateMarketCap(symbol, price) {
    const sharesOutstanding = {"SPY": 1e9, "AAPL": 15e9, "TSLA": 3e9, "MSFT": 7e9, "AMZN": 10e9, "GOOGL": 12e9, "META": 2.5e9};
    return price * (sharesOutstanding[symbol] || 5e9); 
  }

  function formatCurrency(value) {
    if (value === 'N/A' || !isFinite(value)) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(2)}`;
  }

  // Initialize the page
  function initializePage() {
    setupChart();
    loadUserBalance();
    
    // NEU: Preise von API laden beim Seitenaufruf
    updateAllStockPrices();
    
    // Regelmäßige Aktualisierung der Preise alle 2 Minuten
    setInterval(updateAllStockPrices, 120000); // 2 Minuten

    // Set up event listeners for stock items
    document.querySelectorAll('.stock-item').forEach(item => {
      item.addEventListener('click', function() {
        const symbol = this.getAttribute('data-symbol');
        const name = this.getAttribute('data-name');
        const price = this.getAttribute('data-price');
        const change = this.getAttribute('data-change');
        const assetType = this.getAttribute('data-asset-type') || 'stock';

        logDebug(`Selected stock: ${symbol} (${name}), price from HTML: $${price}, change: ${change}%, type: ${assetType}`);

        // Update current symbol and price
        currentSymbol = symbol;
        currentStockPrice = parseFloat(price);
        initialStockPrice = parseFloat(price);

        // Update stock info in UI
        document.getElementById('stock-name').textContent = `${name} (${symbol})`;
        document.getElementById('stock-price').textContent = `Preis: $${price} (${change}%)`;
        document.getElementById('current-price').textContent = `$${price}`;
        
        // Optional: Load additional asset details
        loadAssetDetails(symbol);

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

        // KORREKTUR: Beim Wechsel des Zeitrahmens preserveInitialPrice = false!
        loadStockData(currentSymbol, currentTimeframe, false);
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