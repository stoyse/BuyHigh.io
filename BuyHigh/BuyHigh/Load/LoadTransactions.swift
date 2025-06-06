//
//  LoadTransactions.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import Foundation
import SwiftUI

// Defines the structure for a single transaction
struct Transaction: Codable, Identifiable {
    let id = UUID() // Add identifiable for SwiftUI lists
    let assetSymbol: String
    let quantity: Int
    let pricePerUnit: Double // Assuming price can be decimal
    let transactionType: String
    let timestamp: String

    enum CodingKeys: String, CodingKey {
        case assetSymbol = "asset_symbol"
        case quantity
        case pricePerUnit = "price_per_unit"
        case transactionType = "transaction_type"
        case timestamp
    }
}

// Defines the structure for the API response
struct TransactionsResponse: Codable {
    let success: Bool
    let transactions: [Transaction]?
    let message: String?
}

class TransactionLoader: ObservableObject {
    @Published var transactions: [Transaction] = []
    @Published var isLoading = false
    @Published var errorMessage: String? = nil
    
    private var authManager: AuthManager

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    func loadTransactions(userID: Int) {
        Task {
            await loadTransactionsAsync(userID: userID)
        }
    }
    
    @MainActor
    private func loadTransactionsAsync(userID: Int) async {
        guard let _ = authManager.userId else {
            self.errorMessage = "User ID not available. Please log in."
            return
        }
        
        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            self.errorMessage = "Authentication failed. Please log in again."
            return
        }
        
        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/transactions/\(userID)") else {
            self.errorMessage = "Invalid URL"
            print("UserID: \(userID)")
            return
        }
        
        print("TransactionLoader: Using fresh token for userID: \(userID)")
        print("TransactionLoader: Constructed URL: \(url.absoluteString)")

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
            
            print("TransactionLoader: HTTP Status Code: \(httpResponse.statusCode)")
            
            // Log raw response for debugging
            if let rawString = String(data: data, encoding: .utf8) {
                print("TransactionLoader: Raw response: \(rawString)")
            }

            switch httpResponse.statusCode {
            case 200...299:
                do {
                    let decodedResponse = try JSONDecoder().decode(TransactionsResponse.self, from: data)
                    print("TransactionLoader: Decoded response - success: \(decodedResponse.success)")
                    print("TransactionLoader: Number of transactions: \(decodedResponse.transactions?.count ?? 0)")
                    
                    if decodedResponse.success {
                        self.transactions = decodedResponse.transactions ?? []
                    } else {
                        self.errorMessage = decodedResponse.message ?? "Failed to load transactions."
                    }
                } catch {
                    self.errorMessage = "Failed to decode transaction data: \(error.localizedDescription)"
                }
            case 401:
                self.errorMessage = "Authentication expired. Please log in again."
                authManager.logout()
            case 403:
                self.errorMessage = "Access denied. Please check your permissions."
            case 500...599:
                self.errorMessage = "Server error. Please try again later."                default:
                    self.errorMessage = "Server error: \(httpResponse.statusCode)."
            }
            
        } catch {
            print("TransactionLoader: Network error: \(error.localizedDescription)")
            if error.localizedDescription.contains("timeout") {
                self.errorMessage = "Request timeout. Please check your connection."
            } else {
                self.errorMessage = "Network error: \(error.localizedDescription)"
            }
        }
        
        self.isLoading = false
    }
}


