//
//  ViewTransactions.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewTransactions: View {
    @EnvironmentObject var authManagerEnv: AuthManager
    @StateObject private var userLoader: UserLoader
    @StateObject private var transactionLoader: TransactionLoader // Remove immediate initialization
    @State private var hasTriedToLoadTransactions = false // Track if we've attempted to load transactions
    
    init(authManager: AuthManager) {
        _userLoader = StateObject(wrappedValue: UserLoader(authManager: authManager))
        _transactionLoader = StateObject(wrappedValue: TransactionLoader(authManager: authManager)) // Initialize with authManager
    }
    
    var body: some View {
        NavigationView { // Added NavigationView for title
            VStack {
                if transactionLoader.isLoading {
                    ProgressView("Loading transactions...")
                } else if let errorMessage = transactionLoader.errorMessage {
                    Text("Error: \(errorMessage)")
                        .foregroundColor(.red)
                } else if transactionLoader.transactions.isEmpty {
                    Text("No transactions found.")
                } else {
                    List(transactionLoader.transactions) { transaction in
                        VStack(alignment: .leading) {
                            Text("Asset: \(transaction.assetSymbol)")
                                .font(.headline)
                            Text("Quantity: \(transaction.quantity)")
                            Text(String(format: "Price: $%.2f", transaction.pricePerUnit)) // Corrected string format
                            Text("Type: \(transaction.transactionType)")
                            Text("Date: \(transaction.timestamp)")
                                .font(.caption)
                        }
                    }
                }
            }
            .navigationTitle("Transactions") // Added title
            .onAppear {
                print("ViewTransactions: onAppear called")
                loadTransactionsIfNeeded()
            }
            .onReceive(userLoader.$userData) { userData in
                print("ViewTransactions: userData received: \(userData?.id ?? -1)")
                loadTransactionsIfNeeded()
            }
        }
    }
    
    private func loadTransactionsIfNeeded() {
        if let uid = userLoader.userData?.id, !hasTriedToLoadTransactions {
            print("ViewTransactions: Loading transactions for UserID: \(uid)")
            hasTriedToLoadTransactions = true
            transactionLoader.loadTransactions(userID: uid)
        } else if userLoader.userData == nil && !userLoader.isLoading {
            print("ViewTransactions: UserData not available, fetching...")
            userLoader.fetchUserData()
        }
    }
    }


#Preview {
    let authManager = AuthManager()
    
    ViewTransactions(authManager: authManager) // Removed explicit return
        .environmentObject(authManager)
    
}
