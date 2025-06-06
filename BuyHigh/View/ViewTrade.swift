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
    @StateObject private var stockLoader: StockDataLoader
    
    init(authManager: AuthManager) {
        self.authManager = authManager
        self._stockLoader = StateObject(wrappedValue: StockDataLoader(authManager: authManager))
    }
    
    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack {
                    CardSelectStock(selectedSymbol: $selectedSymbol, authManager: authManager, stockLoader: stockLoader)
                    
                    if let symbol = selectedSymbol {
                        VStack {
                            CardTradingCharts(stock: symbol)
                                .frame(height: 400)
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
