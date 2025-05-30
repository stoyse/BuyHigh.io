//
//  LoadPortfolio.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import Foundation
import SwiftUI

struct Portfolio: Codable, Identifiable {
    let id = UUID()
    let symbol: String
    let name: String
    let type: String
    let quantity: Int
    let averagePrice: Double
    let currentPrice: Double
    let performance: Double
    let sector: String
    let value: Double
    
    enum CodingKeys: String, CodingKey {
        case symbol
        case name
        case type
        case quantity
        case averagePrice = "average_price"
        case currentPrice = "current_price"
        case performance
        case sector
        case value
    }
}

struct PortfolioResponse: Codable {
    let success: Bool
    let portfolio: [Portfolio]
    let totalValue: Double
    let message: String?
}

class PortfolioLoader: ObservableObject {
        @Published var portfolio: [Portfolio] = []
        @Published var isLoading = false
        @Published var errorMessage: String? = nil
        
        private var authManager: AuthManager

        init(authManager: AuthManager) {
            self.authManager = authManager
        }

        func loadPortfolio(userID: Int) {
            guard let _ = authManager.userId, let token = authManager.idToken else {
                self.errorMessage = "User ID or Token not available. Please log in."
                return
            }
            
            // Debug: Print the userID and token info
            print("TransactionLoader: Attempting to fetch transactions for userID: \(userID)")
            print("TransactionLoader: Token available: \(token.prefix(20))...") // Only show first 20 chars for security
            
            guard let url = URL(string: "https://api.stoyse.hackclub.app/user/portfolio/\(userID)") else {
                self.errorMessage = "Invalid URL"
                print("UserID: \(userID)")
                return
            }
            
            // Debug: Print the constructed URL
            print("TransactionLoader: Constructed URL: \(url.absoluteString)")

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
                        print("TransactionLoader: HTTP Status Code: \(httpResponse.statusCode)")
                    }
                    
                    if let error = error {
                        print("TransactionLoader: Network error: \(error.localizedDescription)")
                        self.errorMessage = "Failed to load data: \(error.localizedDescription)"
                        return
                    }

                    guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                        print("TransactionLoader: Invalid HTTP response or status code")
                        self.errorMessage = "Invalid response from server"
                        return
                    }

                    guard let data = data else {
                        print("TransactionLoader: No data received")
                        self.errorMessage = "No data received"
                        return
                    }
                    
                    // Debug: Print raw response
                    if let rawString = String(data: data, encoding: .utf8) {
                        print("TransactionLoader: Raw response: \(rawString)")
                    }

                    do {
                        let decodedResponse = try JSONDecoder().decode(PortfolioResponse.self, from: data)
                        print("TransactionLoader: Decoded response - success: \(decodedResponse.success)")
                        print("TransactionLoader: Number of transactions: \(decodedResponse.portfolio.count ?? 0)")
                        
                        if decodedResponse.success {
                            self.portfolio = decodedResponse.portfolio ?? []
                        } else {
                            print("TransactionLoader: Server returned failure: \(decodedResponse.message ?? "No message")")
                            self.errorMessage = decodedResponse.message ?? "Failed to load transactions."
                        }
                    } catch {
                        print("TransactionLoader: JSON decode error: \(error.localizedDescription)")
                        self.errorMessage = "Failed to decode JSON: \(error.localizedDescription)"
                    }
                }
            }.resume()
        }
    }


