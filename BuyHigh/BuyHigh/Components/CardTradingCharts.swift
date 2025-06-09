//
//  CardTradingCharts.swift
//  BuyHigh
//
//  Created by Julian Stosse on 31.05.25.
//

import SwiftUI
import WebKit

struct CardTradingCharts: View {
    let stock: String
    var body: some View {
        WebView(htmlContent: generateTradingViewHTML(for: stock))
            .edgesIgnoringSafeArea(.all)
    }
}

struct WebView: UIViewRepresentable {
    let htmlContent: String

    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView()
        webView.scrollView.isScrollEnabled = false
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        webView.loadHTMLString(htmlContent, baseURL: nil)
    }
}

func generateTradingViewHTML(for symbol: String) -> String {
    return """
<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      html, body {
        margin: 0;
        padding: 0;
        height: 100%;
        background-color: #000;
      }
    </style>
  </head>
  <body>
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <div class="tradingview-widget-copyright">
        <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">

        </a>
      </div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
      {
        "symbols": [
          ["\(symbol)", "\(symbol)|1D"]
        ],
        "chartOnly": false,
        "width": "100%",
        "height": "100%",
        "locale": "en",
        "colorTheme": "dark",
        "autosize": true
      }
      </script>
    </div>
  </body>
</html>
"""
    
    struct TradingViewWidgetApp: App {
        var body: some Scene {
            WindowGroup {
                ContentView()
            }
        }
    }
}

#Preview {
    CardTradingCharts(stock: "AAPL")
}
