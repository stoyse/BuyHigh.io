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
    @StateObject private var transactionLoader = TransactionLoader() // Add TransactionLoader
    
    init(authManager: AuthManager) {
        _userLoader = StateObject(wrappedValue: UserLoader(authManager: authManager))
    }
    
    var body: some View {
        NavigationView { // Added NavigationView for title
            VStack {
                if transactionLoader.isLoading {
                    ProgressView("Loading transactions...")
                } else if let errorMessage = transactionLoader.errorMessage {
                    Text("Error: \\\\(errorMessage)")
                        .foregroundColor(.red)
                } else if transactionLoader.transactions.isEmpty {
                    Text("No transactions found.")
                } else {
                    List(transactionLoader.transactions) { transaction in
                        VStack(alignment: .leading) {
                            Text("Asset: \\\\(transaction.assetSymbol)")
                                .font(.headline)
                            Text("Quantity: \\\\(transaction.quantity)")
                            Text(String(format: "Price: $%.2f", transaction.pricePerUnit)) // Corrected string format
                            Text("Type: \\\\(transaction.transactionType)")
                            Text("Date: \\\\(transaction.timestamp)")
                                .font(.caption)
                        }
                    }
                }
            }
            .navigationTitle("Transactions") // Added title
            .onAppear {
                // Assuming userLoader.userData.id is the correct userID
                if let userID = userLoader.userData?.id { // Corrected to use userData
                    transactionLoader.loadTransactions(userID: userID)
                } else {
                    // Handle case where userID is not available
                    // For example, show an error or a login prompt
                    // Also, consider triggering fetchUserData if userData is nil and not already loading
                    if userLoader.userData == nil && !userLoader.isLoading {
                        userLoader.fetchUserData() // Attempt to load user data if not available
                    }
                    // Update error message or handle state appropriately
                    // This message might appear briefly while user data is loading
                    transactionLoader.errorMessage = "User ID not available. Loading user data or please log in."
                }
            }
        }
    }
}

#Preview {
    let authManager = AuthManager()
    
    ViewTransactions(authManager: authManager) // Removed explicit return
        .environmentObject(authManager)
    
}
