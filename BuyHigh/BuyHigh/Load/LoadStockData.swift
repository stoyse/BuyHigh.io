//
//  LoadStockData.swift
//  BuyHigh
//
//  Created by Julian Stosse on 05.06.25.
//

import Foundation
import SwiftUI

// Defines the structure for a single stock data point
struct StockDataPoint: Codable, Identifiable {
    let date: String
    let open: Double
    let high: Double
    let low: Double
    let close: Double
    let volume: Int
    let currency: String
    
    // Computed property for Identifiable - uses date as unique identifier
    var id: String { date }
}

// Defines the structure for the API response
struct StockDataResponse: Codable {
    let success: Bool?
    let data: [StockDataPoint]?
    let message: String?
    let is_demo: Bool?
    let currency: String?
    let demo_reason: String?
}

class StockDataLoader: ObservableObject {
    @Published var stockData: [StockDataPoint] = []
    @Published var currentPrice: Double? = nil
    @Published var pricesBySymbol: [String: Double] = [:]
    @Published var isLoading = false
    @Published var errorMessage: String? = nil
    
    private var authManager: AuthManager

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    func loadStockData(symbol: String, timeframe: String = "3M", fresh: Bool = false) {
        guard let token = authManager.idToken else {
            self.errorMessage = "Token not available. Please log in."
            return
        }
        
        // Debug: Print token info
        print("StockDataLoader: Attempting to fetch stock data for symbol: \(symbol)")
        print("StockDataLoader: Token available: \(token.prefix(20))...") // Only show first 20 chars for security
        
        // Construct URL with query parameters
        var urlComponents = URLComponents(string: "https://api.stoyse.hackclub.app/stock-data")!
        urlComponents.queryItems = [
            URLQueryItem(name: "symbol", value: symbol),
            URLQueryItem(name: "timeframe", value: timeframe),
            URLQueryItem(name: "fresh", value: String(fresh))
        ]
        
        guard let url = urlComponents.url else {
            self.errorMessage = "Invalid URL"
            return
        }
        
        // Debug: Print the constructed URL
        print("StockDataLoader: Constructed URL: \(url.absoluteString)")

        isLoading = true
        errorMessage = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                
                // Debug: Print response info
                if let httpResponse = response as? HTTPURLResponse {
                    print("StockDataLoader: HTTP Status Code: \(httpResponse.statusCode)")
                }
                
                if let error = error {
                    print("StockDataLoader: Network error: \(error.localizedDescription)")
                    self.errorMessage = "Failed to load data: \(error.localizedDescription)"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                    print("StockDataLoader: Invalid HTTP response or status code")
                    self.errorMessage = "Invalid response from server"
                    return
                }

                guard let data = data else {
                    print("StockDataLoader: No data received")
                    self.errorMessage = "No data received"
                    return
                }
                
                // Debug: Print raw response
                if let rawString = String(data: data, encoding: .utf8) {
                    print("StockDataLoader: Raw response: \(rawString)")
                }

                do {
                    // Try to decode as direct array of StockDataPoint (based on backend response_model)
                    if let decodedStockData = try? JSONDecoder().decode([StockDataPoint].self, from: data) {
                        print("StockDataLoader: Decoded direct array - Number of data points: \(decodedStockData.count)")
                        self.stockData = decodedStockData
                        
                        // Set current price to the latest close price and store it by symbol
                        if let latestDataPoint = decodedStockData.last {
                            self.currentPrice = latestDataPoint.close
                            self.pricesBySymbol[symbol] = latestDataPoint.close
                            print("StockDataLoader: Current price for \(symbol) set to: \(latestDataPoint.close)")
                        }
                    } else {
                        // Fallback: Try to decode as wrapped response (if API returns error with wrapped format)
                        let decodedResponse = try JSONDecoder().decode(StockDataResponse.self, from: data)
                        print("StockDataLoader: Decoded wrapped response - success: \(decodedResponse.success ?? false)")
                        
                        if let stockDataPoints = decodedResponse.data {
                            self.stockData = stockDataPoints
                            if let latestDataPoint = stockDataPoints.last {
                                self.currentPrice = latestDataPoint.close
                                self.pricesBySymbol[symbol] = latestDataPoint.close
                                print("StockDataLoader: Current price for \(symbol) set to: \(latestDataPoint.close)")
                            }
                        } else {
                            print("StockDataLoader: Server returned failure: \(decodedResponse.message ?? "No message")")
                            self.errorMessage = decodedResponse.message ?? "Failed to load stock data."
                        }
                    }
                } catch {
                    print("StockDataLoader: JSON decode error: \(error.localizedDescription)")
                    self.errorMessage = "Failed to decode JSON: \(error.localizedDescription)"
                }
            }
        }.resume()
    }
    
    // Convenience function to load just the current price (uses minimal timeframe)
    func loadCurrentPrice(symbol: String) {
        loadStockData(symbol: symbol, timeframe: "1W", fresh: true)
    }
    
    // Get the current price for a specific symbol
    func getCurrentPrice(for symbol: String) -> Double? {
        return pricesBySymbol[symbol]
    }
    
    // Check if we have loaded data for a specific symbol
    func hasLoadedData(for symbol: String) -> Bool {
        return pricesBySymbol[symbol] != nil
    }
}