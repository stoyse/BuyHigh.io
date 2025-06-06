//
//  LoadPortfolio.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import Foundation
import SwiftUI

struct Portfolio: Codable, Identifiable {
    // let id = UUID() // Alt: UUID als ID
    var id: String { symbol } // Neu: Symbol als ID
    let symbol: String
    let name: String
    let type: String
    let quantity: Double // Geändert von Int zu Double
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
    let totalValue: Double? // Geändert von Double zu Double?
    let message: String?

    enum CodingKeys: String, CodingKey {
        case success
        case portfolio
        case totalValue = "total_value"
        case message
    }
}

class PortfolioLoader: ObservableObject {
        @Published var portfolio: [Portfolio] = [] {
            didSet {
                print("PortfolioLoader: portfolio property was updated.")
                print("PortfolioLoader: New portfolio count: \(portfolio.count)")
                if let _ = portfolio.first { // Replaced firstItem with _
                    // If you need to use the first item, you can assign it here
                    // e.g., let firstSymbol = portfolio.first?.symbol
                    // print("PortfolioLoader: First item in portfolio: \\(firstSymbol ?? \"N/A\")")
                } else {
                    print("PortfolioLoader: Portfolio is empty after update.")
                }
            }
        }
        @Published var isLoading = false
        @Published var errorMessage: String? = nil
        
        private var authManager: AuthManager

        init(authManager: AuthManager) {
            self.authManager = authManager
        }

        func loadPortfolio(userID: Int) {
            Task {
                await loadPortfolioAsync(userID: userID)
            }
        }
        
        @MainActor
        private func loadPortfolioAsync(userID: Int) async {
            guard let _ = authManager.userId else {
                self.errorMessage = "User ID not available. Please log in."
                return
            }
            
            // Get a fresh token
            guard let token = await authManager.getValidToken() else {
                self.errorMessage = "Authentication failed. Please log in again."
                return
            }
            
            guard let url = URL(string: "https://api.stoyse.hackclub.app/user/portfolio/\(userID)") else {
                self.errorMessage = "Invalid URL"
                print("UserID: \(userID)")
                return
            }
            
            print("PortfolioLoader: Using fresh token for userID: \(userID)")
            print("PortfolioLoader: Constructed URL: \(url.absoluteString)")

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
                    self.errorMessage = "Invalid response from server."
                    self.isLoading = false
                    return
                }
                
                print("PortfolioLoader: HTTP Status Code: \(httpResponse.statusCode)")
                
                // Log raw response for debugging
                if let rawString = String(data: data, encoding: .utf8) {
                    print("PortfolioLoader: Raw response: \(rawString)")
                }

                switch httpResponse.statusCode {
                case 200...299:
                    do {
                        let decodedResponse = try JSONDecoder().decode(PortfolioResponse.self, from: data)
                        print("PortfolioLoader: Decoded response - success: \(decodedResponse.success)")
                        print("PortfolioLoader: Number of portfolio items: \(decodedResponse.portfolio.count)")
                        
                        if decodedResponse.success {
                            self.portfolio = decodedResponse.portfolio
                        } else {
                            self.errorMessage = decodedResponse.message ?? "Failed to load portfolio."
                        }
                    } catch {
                        self.errorMessage = "Failed to decode portfolio data: \(error.localizedDescription)"
                    }
                case 401:
                    self.errorMessage = "Authentication expired. Please log in again."
                    authManager.logout()
                case 403:
                    self.errorMessage = "Access denied. Please check your permissions."
                case 500...599:
                    self.errorMessage = "Server error. Please try again later."
                default:
                    self.errorMessage = "Server error: \(httpResponse.statusCode)."
                }
                
            } catch {
                print("PortfolioLoader: Network error: \(error.localizedDescription)")
                if error.localizedDescription.contains("timeout") {
                    self.errorMessage = "Request timeout. Please check your connection."
                } else {
                    self.errorMessage = "Network error: \(error.localizedDescription)"
                }
            }
            
            self.isLoading = false
        }
    }


