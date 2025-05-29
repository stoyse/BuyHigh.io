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
        guard let _ = authManager.userId, let token = authManager.idToken else {
            self.errorMessage = "User ID or Token not available. Please log in."
            return
        }
        
        // Debug: Print the userID and token info
        print("TransactionLoader: Attempting to fetch transactions for userID: \(userID)")
        print("TransactionLoader: Token available: \(token.prefix(20))...") // Only show first 20 chars for security
        
        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/transactions/\(userID)") else {
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
                    let decodedResponse = try JSONDecoder().decode(TransactionsResponse.self, from: data)
                    print("TransactionLoader: Decoded response - success: \(decodedResponse.success)")
                    print("TransactionLoader: Number of transactions: \(decodedResponse.transactions?.count ?? 0)")
                    
                    if decodedResponse.success {
                        self.transactions = decodedResponse.transactions ?? []
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


