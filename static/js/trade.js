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

  // Neuer globaler Cache für Basispreise aus der Datenbank
  let stockBasePricesCache = {};

  // Funktion zum initialen Laden aller Basispreise aus der Datenbank
  function loadAllBasePrices() {
    logDebug("Loading all base prices from database...");
    
    return fetch(`/api/assets`)
      .then(response => response.json())
      .then(data => {
        if (data.success && Array.isArray(data.assets)) {
          data.assets.forEach(asset => {
            if (asset.symbol && asset.default_price) {
              stockBasePricesCache[asset.symbol] = parseFloat(asset.default_price);
              logDebug(`Cached base price for ${asset.symbol}: $${stockBasePricesCache[asset.symbol]}`);
            }
          });
          logDebug(`Successfully cached base prices for ${Object.keys(stockBasePricesCache).length} assets`);
          return stockBasePricesCache;
        }
        throw new Error("Failed to load asset base prices");
      })
      .catch(error => {
        logDebug(`Error loading base prices: ${error.message}`);
        return {};
      });
  }

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
    
    stockItems.forEach(item => {
      const symbol = item.getAttribute('data-symbol');
      if (!symbol) return;

      fetch(`/api/stock-data?symbol=${symbol}&timeframe=1D`)
        .then(response => response.json())
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            const latestData = data[data.length - 1];
            const price = parseFloat(latestData.close); // Preis als Zahl belassen

            // Wende Mayhem-Effekt an (jetzt ein Pass-Through, der eine Zahl sicherstellt)
            applyMayhemEffect(symbol, price).then(adjustedPrice => {
              item.setAttribute('data-price', adjustedPrice.toFixed(2));
              const priceElement = item.querySelector('.stock-price');
              if (priceElement) {
                priceElement.textContent = `$${adjustedPrice.toFixed(2)}`;
              }
            });
          }
        })
        .catch(error => {
          console.error(`Error updating price for ${symbol}:`, error);
        });
    });
  }

  // Neue Funktion: Überprüfe auf Marktereignisse und passe Preise an (Mayhem-Effekt entfernt/umgangen)
  function applyMayhemEffect(symbol, price) {
    const numericPrice = parseFloat(price);
    if (isNaN(numericPrice)) {
      logDebug(`[applyMayhemEffect] Invalid price for ${symbol}: ${price}. Defaulting to 0.`);
      return Promise.resolve(0); // Stelle sicher, dass eine Zahl zurückgegeben wird
    }
    return Promise.resolve(numericPrice); // Gibt den Preis als Zahl zurück, verpackt in einem Promise
  }

  // Neue Hilfsfunktion für Fallback auf Demo-Preise bei API-Limitierung
  function useFallbackDemoPrice(item, symbol) {
    // Hole Default-Preis aus der Datenbank (immer neu holen!)
    const basePrice = getStartPrice(symbol);
    const fallbackPrice = parseFloat(basePrice).toFixed(2);

    item.setAttribute('data-price', fallbackPrice);
    item.setAttribute('data-source', 'demo');

    const priceElement = item.querySelector('.stock-price');
    if (priceElement) {
      priceElement.textContent = `$${fallbackPrice}`;
      priceElement.classList.add('demo-data');
      setTimeout(() => priceElement.classList.remove('demo-data'), 2000);
    }

    if (currentSymbol === symbol) {
      currentStockPrice = parseFloat(fallbackPrice);
      document.getElementById('current-price').textContent = `$${fallbackPrice}`;
      document.getElementById('current-price').classList.add('demo-data');
      setTimeout(() => document.getElementById('current-price').classList.remove('demo-data'), 2000);
      updateTotalPrice();
    }

    logDebug(`🔄 Fallback-Preis (Demo/Default aus DB) für ${symbol} verwendet: $${fallbackPrice}`);
  }

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

    fetch(`/api/stock-data?symbol=${symbol}&timeframe=${timeframe}&fresh=true`) // Force fresh aktivieren!
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

        // Wenn data ein leeres Array ist, werfe einen Fehler, damit wir zu den Demo-Daten fallen
        if (data.length === 0) {
          logDebug(`❌ API returned empty data array for ${symbol}`);
          throw new Error('Empty data array returned');
        }

        logDebug(`API Success: Received ${data.length} data points for ${symbol}`);
        
        // Vor der Chart-Aktualisierung darauf hinweisen, dass es Testdaten sein könnten
        if (data.length > 0 && data[0].currency === 'USD') {
          // Datum-Format-Check
          try {
            // Teste, ob ein gültiges Datum vorhanden ist
            new Date(data[0].date).toISOString();
          } catch (e) {
            logDebug(`⚠️ Invalid date format in API data for ${symbol}`);
            throw new Error('Invalid date format in API data');
          }
        }
        
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

  // Hinzugefügt: Prüfe API-Key-Status
  function checkApiStatus() {
    logDebug(`Checking API status...`);
    fetch('/api/status')  // Diese Route müssen Sie noch implementieren
    .then(response => response.json())
    .then(data => {
        if (data.api_key_configured) {
            logDebug(`✅ TwelveData API key configured correctly`);
        } else {
            logDebug(`⚠️ No TwelveData API key configured! Using demo data only.`);
            alert("Hinweis: Es ist kein TwelveData API-Key konfiguriert. Die Anwendung verwendet Demo-Daten.");
        }
    })
    .catch(error => {
        logDebug(`⚠️ Error checking API status: ${error.message}`);
    });
  }

  // Neue Funktion: Aktualisiert nur das Chart ohne den Kaufpreis zu ändern
  function updateChartOnly(symbol, apiData) {
    const maxPoints = 300;
    
    // Filtere ungültige Candles heraus (inkl. Datumsprüfung)
    const validData = apiData.filter(item => {
      // Erweiterte Validierung
      if (!item || typeof item !== 'object') return false;
      if (!item.date || !item.open || !item.high || !item.low || !item.close) return false;
      
      try {
        const dateObj = new Date(item.date);
        return !isNaN(dateObj.getTime()) &&
              item.open !== null && item.high !== null && item.low !== null && item.close !== null &&
              isFinite(parseFloat(item.open)) && isFinite(parseFloat(item.high)) && 
              isFinite(parseFloat(item.low)) && isFinite(parseFloat(item.close));
      } catch (e) {
        return false;
      }
    });
    
    if (validData.length === 0) {
      logDebug(`❌ No valid data points found for updateChartOnly`);
      return;
    }
    
    const slicedData = validData.length > maxPoints ? validData.slice(-maxPoints) : validData;

    try {
      const chartData = slicedData.map(item => ({
        x: new Date(item.date),
        y: [
          parseFloat(item.open),
          parseFloat(item.high),
          parseFloat(item.low),
          parseFloat(item.close)
        ]
      }));
      
      // Überprüfe noch einmal für ungültige Werte
      const cleanChartData = chartData.filter(point => 
        !point.y.some(val => isNaN(val)) && 
        !isNaN(point.x.getTime())
      );

      if (cleanChartData.length === 0) return;

      chart.updateSeries([{
        name: symbol,
        data: cleanChartData
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
    } catch(e) {
      logDebug(`❌ Error updating chart only: ${e.message}`);
    }
  }

  // Funktion: Chart und Stats aktualisieren (wie updateChartOnly, aber setzt auch currentStockPrice)
  function updateChartAndStats(symbol, apiData) {
    const maxPoints = 300;
    
    // Debug-Info zum Format der Daten anzeigen
    if (apiData && apiData.length > 0) {
      logDebug(`Data format sample:`, apiData[0]);
    }
    
    // Filtere ungültige Candles heraus (inkl. Datumsprüfung)
    const validData = apiData.filter(item => {
      // Erweiterte Validierung
      if (!item || typeof item !== 'object') return false;
      if (!item.date || !item.open || !item.high || !item.low || !item.close) return false;
      
      try {
        const dateObj = new Date(item.date);
        return !isNaN(dateObj.getTime()) &&
              item.open !== null && item.high !== null && item.low !== null && item.close !== null &&
              isFinite(parseFloat(item.open)) && isFinite(parseFloat(item.high)) && 
              isFinite(parseFloat(item.low)) && isFinite(parseFloat(item.close));
      } catch (e) {
        logDebug(`Invalid data point detected:`, item);
        return false;
      }
    });
    
    if (validData.length === 0) {
      logDebug(`❌ No valid data points found in API response for ${symbol}`);
      useDemoData(symbol, currentTimeframe);
      return;
    }
    
    logDebug(`Valid data points: ${validData.length} out of ${apiData.length}`);
    
    const slicedData = validData.length > maxPoints ? validData.slice(-maxPoints) : validData;

    try {
      const chartData = slicedData.map(item => ({
        x: new Date(item.date),
        y: [
          parseFloat(item.open),
          parseFloat(item.high),
          parseFloat(item.low),
          parseFloat(item.close)
        ]
      }));

      // Überprüfe noch einmal für ungültige Werte, die NaN sein könnten
      const cleanChartData = chartData.filter(point => 
        !point.y.some(val => isNaN(val)) && 
        !isNaN(point.x.getTime())
      );

      if (cleanChartData.length === 0) {
        logDebug(`❌ No valid chart data points after conversion for ${symbol}`);
        useDemoData(symbol, currentTimeframe);
        return;
      }

      chart.updateSeries([{
        name: symbol,
        data: cleanChartData
      }]);

      // Prüfen, ob die Daten realistisch für diese Aktie sind
      const basePrice = getStartPrice(symbol);
      if (slicedData.length > 0) {
        const lastDataPoint = slicedData[slicedData.length - 1];
        const rawClosePrice = parseFloat(lastDataPoint.close);
        
        // Prüfen, ob der Preis realistisch ist (innerhalb von 50% des Default-Preises)
        const isRealisticPrice = Math.abs(rawClosePrice - basePrice) / basePrice < 0.5;
        
        // Wenn der Preis nicht realistisch für diese Aktie ist, verwenden wir den Default-Preis
        const actualPrice = isRealisticPrice ? rawClosePrice : basePrice;
        
        // Wende Mayhem-Effekt auf den korrekten Basispreis an
        applyMayhemEffect(symbol, actualPrice).then(adjustedPrice => {
          currentStockPrice = adjustedPrice;
          document.getElementById('current-price').textContent = `$${adjustedPrice.toFixed(2)}`;
          
          // Aktualisiere die Preisanzeige auch in der Seitenleiste
          const sidebarItem = document.querySelector(`.stock-item[data-symbol="${symbol}"]`);
          if (sidebarItem) {
            sidebarItem.setAttribute('data-price', adjustedPrice.toFixed(2));
            const priceElement = sidebarItem.querySelector('.stock-price');
            if (priceElement) {
              priceElement.textContent = `$${adjustedPrice.toFixed(2)}`;
            }
          }
          
          // Aktualisiere weitere UI-Elemente
          document.getElementById('stock-high').textContent = `$${(parseFloat(lastDataPoint.high) * (adjustedPrice / actualPrice)).toFixed(2)}`;
          document.getElementById('stock-low').textContent = `$${(parseFloat(lastDataPoint.low) * (adjustedPrice / actualPrice)).toFixed(2)}`;
          document.getElementById('stock-volume').textContent = formatNumber(lastDataPoint.volume);
          
          const marketCap = typeof calculateMarketCap === 'function' ? calculateMarketCap(symbol, adjustedPrice) : 'N/A';
          document.getElementById('stock-market-cap').textContent = typeof formatCurrency === 'function' ? formatCurrency(marketCap) : marketCap;
          
          updateTotalPrice();
          logDebug(`📊 Chart and stats updated for ${symbol}, adjusted close: $${adjustedPrice.toFixed(2)}, base price: $${basePrice}`);
        });
      }
    } catch(e) {
      logDebug(`❌ Error updating chart: ${e.message}`);
      useDemoData(symbol, currentTimeframe);
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
  
  // Demo-Daten verwenden, wenn API nicht funktioniert
  function useDemoData(symbol, timeframe) {
    const units = getTimeframeUnits(timeframe);
    const startPrice = getStartPrice(symbol); // immer Default-Preis aus DB holen!
    const isMinutes = timeframe === '1MIN';
    logDebug(`📊 Generating fallback demo data for ${symbol} with startPrice $${parseFloat(startPrice).toFixed(2)}`);
    const demoData = generateCandlestickData(units, startPrice, isMinutes);
    
    // Wende Mayhem-Effekt auf die Demo-Daten an, aber respektiere die startPrice
    applyMayhemEffect(symbol, startPrice).then(adjustedStartPrice => {
        // Passe alle Preise proportional an
        const factor = adjustedStartPrice / startPrice;
        demoData.forEach(item => {
            item.open *= factor;
            item.high *= factor;
            item.low *= factor;
            item.close *= factor;
        });
        
        updateChartWithDemoData(symbol, demoData);
    });
  }

  // Neue Funktion zur Aktualisierung des Charts mit Demo-Daten
  function updateChartWithDemoData(symbol, demoData) {
    try {
      const chartData = demoData.map(item => ({
        x: new Date(item.date),
        y: [
          parseFloat(item.open),
          parseFloat(item.high),
          parseFloat(item.low),
          parseFloat(item.close)
        ]
      }));
      
      chart.updateSeries([{
        name: symbol,
        data: chartData
      }]);
      
      if (demoData.length > 0) {
        const lastDataPoint = demoData[demoData.length - 1];
        currentStockPrice = parseFloat(lastDataPoint.close);
        document.getElementById('current-price').textContent = `$${currentStockPrice.toFixed(2)}`;
        document.getElementById('stock-high').textContent = `$${parseFloat(lastDataPoint.high).toFixed(2)}`;
        document.getElementById('stock-low').textContent = `$${parseFloat(lastDataPoint.low).toFixed(2)}`;
        document.getElementById('stock-volume').textContent = formatNumber(lastDataPoint.volume);
        
        // Aktualisiere die Seitenleiste
        const sidebarItem = document.querySelector(`.stock-item[data-symbol="${symbol}"]`);
        if (sidebarItem) {
          sidebarItem.setAttribute('data-price', currentStockPrice.toFixed(2));
          const priceElement = sidebarItem.querySelector('.stock-price');
          if (priceElement) {
            priceElement.textContent = `$${currentStockPrice.toFixed(2)}`;
          }
        }
        
        const marketCap = typeof calculateMarketCap === 'function' ? calculateMarketCap(symbol, currentStockPrice) : 'N/A';
        document.getElementById('stock-market-cap').textContent = typeof formatCurrency === 'function' ? formatCurrency(marketCap) : marketCap;
        
        updateTotalPrice();
        logDebug(`📊 Demo chart updated for ${symbol}, close: $${currentStockPrice.toFixed(2)}`);
      }
    } catch(e) {
      logDebug(`❌ Error updating chart with demo data: ${e.message}`);
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

    // Wende Mayhem-Effekt auf den aktuellen Preis an
    applyMayhemEffect(currentSymbol, price).then(adjustedPrice => {
      const endpoint = action === 'buy' ? '/api/trade/buy' : '/api/trade/sell';
      const payload = {
        symbol: currentSymbol,
        quantity: quantity,
        price: adjustedPrice
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

  // Verbesserte Funktion für getStartPrice ohne statische Fallbacks
  function getStartPrice(symbol) {
    // 1. Versuche zuerst den Preis aus dem Cache zu lesen
    if (stockBasePricesCache[symbol] !== undefined) {
      return stockBasePricesCache[symbol];
    }
    
    // 2. Wenn nicht im Cache, versuche synchron aus der Datenbank zu laden
    let price = null;
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', `/api/assets/${symbol}`, false); // synchroner Request (nur für Notfall)
      xhr.send(null);
      if (xhr.status === 200) {
        const data = JSON.parse(xhr.responseText);
        if (data && data.asset && data.asset.default_price) {
          price = parseFloat(data.asset.default_price);
          // Für zukünftige Verwendung cachen
          stockBasePricesCache[symbol] = price;
        }
      }
    } catch (e) {
      logDebug(`Error in synchronous fallback for ${symbol}: ${e}`);
    }
    
    if (price && !isNaN(price)) return price;
    
    // 3. Absoluter Fallback: sicherer Standardpreis
    const defaultFallbackPrice = 100 + Math.random() * 50; // Zwischen $100-$150
    logDebug(`Warning: Using generic fallback price for ${symbol}: $${defaultFallbackPrice.toFixed(2)}`);
    return defaultFallbackPrice;
  }

  // Dummy-Funktionen für calculateMarketCap und formatCurrency, falls nicht vorhanden
  function calculateMarketCap(symbol, price) {
    const sharesOutstanding = {"AAPL": 15e9, "TSLA": 3e9, "MSFT": 7e9, "AMZN": 10e9, "GOOGL": 12e9, "META": 2.5e9, "NVDA": 2.5e9};
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
    // Füge CSS für Demo-Daten-Indikator hinzu
    const style = document.createElement('style');
    style.textContent = `
      .demo-data {
        animation: pulse 1s;
        position: relative;
      }
      .demo-data::after {
        content: "⚠️";
        font-size: 0.7em;
        position: absolute;
        top: -8px;
        right: -10px;
      }
      @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
      }
    `;
    document.head.appendChild(style);
    
    setupChart();
    loadUserBalance();
    
    // NEU: Laden der Basispreise VOR dem Aktualisieren der Preise
    loadAllBasePrices().then(() => {
      // HINZUGEFÜGT: Sofort die Default-Preise aus data-price in die UI übernehmen
      document.querySelectorAll('.stock-item').forEach(item => {
        const symbol = item.getAttribute('data-symbol');
        const priceElement = item.querySelector('.stock-price');
        
        // Verwende sowohl data-price als auch cached base price
        let price = parseFloat(item.getAttribute('data-price'));
        if (isNaN(price) && stockBasePricesCache[symbol]) {
          price = stockBasePricesCache[symbol];
          item.setAttribute('data-price', price); // Update das Attribut
        }
        
        if (priceElement && !isNaN(price)) {
          priceElement.textContent = `$${price.toFixed(2)}`;
        }
      });
      
      // NEU: Preise von API laden beim Seitenaufruf
      updateAllStockPrices();
      
      // Regelmäßige Aktualisierung der Preise alle 2 Minuten
      setInterval(updateAllStockPrices, 120000); // 2 Minuten
      
      // NEU: Automatisch das erste Element in der Stockliste auswählen
      selectFirstStockItem();
    });

    // Set up event listeners for stock items
    document.querySelectorAll('.stock-item').forEach(item => {
      item.addEventListener('click', function() {
        selectStockItem(this);
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
        loadStockData(currentSymbol, timeframe, false);
      });
    });

    // Add event listeners for buy and sell buttons
    document.getElementById('buy-button').addEventListener('click', function() {
      handleTrade('buy');
    });
    
    document.getElementById('sell-button').addEventListener('click', function() {
      handleTrade('sell');
    });
  }

  // NEU: Funktion zum Auswählen des ersten Elements
  function selectFirstStockItem() {
    const firstStockItem = document.querySelector('.stock-item');
    if (firstStockItem) {
      logDebug('Selecting first stock item by default');
      selectStockItem(firstStockItem);
      
      // Visuell als ausgewählt markieren
      firstStockItem.classList.remove('border-gray-200', 'dark:border-gray-700');
      firstStockItem.classList.add('border-primary-light', 'dark:border-primary-dark', 'border-2', 'selected-stock');
    } else {
      logDebug('No stock items found to select by default');
    }
  }
  
  // NEU: Auslagern der Stock-Item-Auswahl in separate Funktion
  function selectStockItem(item) {
    const symbol = item.getAttribute('data-symbol');
    const name = item.getAttribute('data-name');
    const basePrice = parseFloat(item.getAttribute('data-price'));
    const change = item.getAttribute('data-change');
    const assetType = item.getAttribute('data-asset-type') || 'stock';

    logDebug(`Selected stock: ${symbol} (${name}), base price: $${basePrice}, change: ${change}%, type: ${assetType}`);

    // Wende Mayhem-Effekt auf den Basispreis an
    applyMayhemEffect(symbol, basePrice).then(adjustedPrice => {
      // Update current symbol and price
      currentSymbol = symbol;
      currentStockPrice = adjustedPrice;
      initialStockPrice = adjustedPrice;

      // Update stock info in UI
      document.getElementById('stock-name').textContent = `${name} (${symbol})`;
      document.getElementById('stock-price').textContent = `Preis: $${adjustedPrice.toFixed(2)} (${change}%)`;
      document.getElementById('current-price').textContent = `$${adjustedPrice.toFixed(2)}`;

      // Optional: Load additional asset details
      loadAssetDetails(symbol);

      // Update total based on quantity
      updateTotalPrice();

      // Load new stock data, WICHTIG: Verwende false statt true, damit der Preis nicht überschrieben wird
      loadStockData(symbol, currentTimeframe, false);

      // Highlight selected stock
      document.querySelectorAll('.stock-item').forEach(s => {
        s.classList.remove('border-primary-light', 'dark:border-primary-dark', 'border-2', 'selected-stock');
        s.classList.add('border-gray-200', 'dark:border-gray-700', 'border-2');
      });
      item.classList.remove('border-gray-200', 'dark:border-gray-700');
      item.classList.add('border-primary-light', 'dark:border-primary-dark', 'border-2', 'selected-stock');

      logDebug(`Updated UI for selected stock: ${symbol} with adjusted price: $${adjustedPrice.toFixed(2)}`);
    });
  }

  initializePage();
});