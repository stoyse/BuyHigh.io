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
        Task {
            await loadStockDataAsync(symbol: symbol, timeframe: timeframe, fresh: fresh)
        }
    }
    
    @MainActor
    private func loadStockDataAsync(symbol: String, timeframe: String, fresh: Bool) async {
        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            self.errorMessage = "Authentication failed. Please log in again."
            return
        }
        
        print("StockDataLoader: Using fresh token for symbol: \(symbol)")
        
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

        isLoading = true
        errorMessage = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                self.errorMessage = "Invalid response from server"
                self.isLoading = false
                return
            }
            
            print("StockDataLoader: HTTP Status Code: \(httpResponse.statusCode)")
            
            switch httpResponse.statusCode {
            case 200:
                await handleStockDataResponse(data, symbol: symbol)
            case 401:
                self.errorMessage = "Authentication expired. Please log in again."
                authManager.logout()
            case 404:
                self.errorMessage = "Stock symbol '\(symbol)' not found."
            case 500...599:
                self.errorMessage = "Server error. Please try again later."
            default:
                self.errorMessage = "Failed to load stock data (Code: \(httpResponse.statusCode))"
            }
            
        } catch {
            print("StockDataLoader: Network error: \(error.localizedDescription)")
            if error.localizedDescription.contains("timeout") {
                self.errorMessage = "Request timeout. Please check your connection."
            } else {
                self.errorMessage = "Network error: \(error.localizedDescription)"
            }
        }
        
        self.isLoading = false
    }
    
    private func handleStockDataResponse(_ data: Data, symbol: String) async {
        // Debug: Print raw response
        if let rawString = String(data: data, encoding: .utf8) {
            print("StockDataLoader: Raw response: \(rawString)")
        }

        do {
            // Try to decode as direct array of StockDataPoint
            if let decodedStockData = try? JSONDecoder().decode([StockDataPoint].self, from: data) {
                print("StockDataLoader: Decoded direct array - Number of data points: \(decodedStockData.count)")
                self.stockData = decodedStockData
                
                // Update current price with the latest data point
                if let latestDataPoint = decodedStockData.last {
                    self.currentPrice = latestDataPoint.close
                    self.pricesBySymbol[symbol] = latestDataPoint.close
                }
            } else {
                // Try to decode as StockDataResponse
                let decodedResponse = try JSONDecoder().decode(StockDataResponse.self, from: data)
                print("StockDataLoader: Decoded response - success: \(decodedResponse.success ?? false)")
                
                if decodedResponse.success == true {
                    self.stockData = decodedResponse.data ?? []
                    
                    if let latestDataPoint = decodedResponse.data?.last {
                        self.currentPrice = latestDataPoint.close
                        self.pricesBySymbol[symbol] = latestDataPoint.close
                    }
                } else {
                    self.errorMessage = decodedResponse.message ?? "Failed to load stock data"
                }
            }
        } catch {
            print("StockDataLoader: JSON decode error: \(error.localizedDescription)")
            self.errorMessage = "Failed to decode stock data: \(error.localizedDescription)"
        }
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