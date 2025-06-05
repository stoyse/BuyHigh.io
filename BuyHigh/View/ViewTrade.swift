//
//  ViewTrade.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewTrade: View {
    @State private var selectedSymbol: String?
    var authManager: AuthManager
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack {
                    CardSelectStock(selectedSymbol: $selectedSymbol, authManager: authManager)
                    
                    if let symbol = selectedSymbol {
                        VStack {
                            Text("Selected Asset: \(symbol)")
                                .font(.headline)
                                .foregroundColor(.blue)
                                .padding()
                            
                            // Hier kannst du später deinen Chart hinzufügen
                            Text("Chart für \(symbol) wird hier angezeigt")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                                .padding()
                                .background(Color(.systemGray6))
                                .cornerRadius(8)
                        }
                        .padding()
                    }
                    
                    Spacer()
                }
            }
            .padding()
        }
    }
}

#Preview {
    ViewTrade(authManager: AuthManager())
}
