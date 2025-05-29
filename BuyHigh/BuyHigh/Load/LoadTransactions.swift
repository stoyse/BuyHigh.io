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

    func loadTransactions(userID: Int) {
        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/transactions/\(userID)") else {
            self.errorMessage = "Invalid URL"
            return
        }

        isLoading = true
        errorMessage = nil

        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                if let error = error {
                    self.errorMessage = "Failed to load data: \\(error.localizedDescription)"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                    self.errorMessage = "Invalid response from server"
                    return
                }

                guard let data = data else {
                    self.errorMessage = "No data received"
                    return
                }

                do {
                    let decodedResponse = try JSONDecoder().decode(TransactionsResponse.self, from: data)
                    if decodedResponse.success {
                        self.transactions = decodedResponse.transactions ?? []
                    } else {
                        self.errorMessage = decodedResponse.message ?? "Failed to load transactions."
                    }
                } catch {
                    self.errorMessage = "Failed to decode JSON: \\(error.localizedDescription)"
                }
            }
        }.resume()
    }
}


