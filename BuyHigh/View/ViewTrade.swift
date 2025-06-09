//
//  ViewTrade.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewTrade: View {
    let authManager: AuthManager
    @State private var selectedSymbol: String?
    @StateObject private var stockLoader: StockDataLoader
    
    // States for trade inputs and alerts
    @State private var quantityString: String = "1.0"
    @State private var priceString: String = ""
    @State private var isShowingAlert: Bool = false
    @State private var alertTitle: String = ""
    @State private var alertMessage: String = ""
    
    private let tradeService = TradeService()
    
    private enum TradeAction {
        case buy, sell
    }

    init(authManager: AuthManager) {
        self.authManager = authManager
        self._stockLoader = StateObject(wrappedValue: StockDataLoader(authManager: authManager))
    }
    
    var body: some View {
        NavigationView {
            ZStack {
                // Glass Background
                LinearGradient(
                    colors: [
                        Color(.systemBackground),
                        Color.green.opacity(0.03),
                        Color.blue.opacity(0.02),
                        Color(.systemBackground)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 16) {
                        // Header - reduced padding
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Trading")
                                    .font(.system(size: 28, weight: .bold, design: .rounded))
                                    .foregroundStyle(
                                        LinearGradient(
                                            colors: [Color.primary, Color.green.opacity(0.8)],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                
                                Text("Buy high, sell higher!")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            
                            Spacer()
                            
                            ZStack {
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(.thinMaterial)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 16)
                                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                    )
                                    .frame(width: 50, height: 50)
                                    .shadow(color: .green.opacity(0.2), radius: 8, x: 0, y: 4)
                                
                                Image(systemName: "chart.line.uptrend.xyaxis")
                                    .font(.title2)
                                    .foregroundStyle(
                                        LinearGradient(
                                            colors: [Color.green, Color.blue],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, 8)
                        
                        // Stock Selection Card - full width
                        CardSelectStock(
                            selectedSymbol: $selectedSymbol,
                            authManager: authManager,
                            stockLoader: stockLoader
                        )
                        .glassCard()
                        .frame(maxWidth: .infinity)
                        .frame(width: .infinity)
                        
                        // Trading Chart (if symbol selected) - full width
                        if let symbol = selectedSymbol {
                            VStack(alignment: .leading, spacing: 12) {
                                HStack {
                                    Text("Chart for \(symbol)")
                                        .font(.headline)
                                        .foregroundStyle(.primary)
                                    
                                    Spacer()
                                    
                                    // Add chart period selector
                                    HStack(spacing: 8) {
                                        ForEach(["1D", "1W", "1M", "3M"], id: \.self) { period in
                                            Button(period) {
                                                // Handle period selection
                                            }
                                            .font(.caption)
                                            .fontWeight(.medium)
                                            .padding(.horizontal, 12)
                                            .padding(.vertical, 6)
                                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 8))
                                            .foregroundStyle(.secondary)
                                        }
                                    }
                                }
                                .padding(.horizontal, 16)
                                
                                CardTradingCharts(stock: symbol)
                                    .frame(height: 300)
                                    .frame(maxWidth: .infinity)
                            }
                            .glassCard()
                            .padding(.horizontal, 12)
                        }
                        
                        // Trading Actions Card - full width
                        if let currentSymbol = selectedSymbol {
                            VStack(alignment: .leading, spacing: 16) {
                                Text("Trading Actions for \(currentSymbol)")
                                    .font(.headline)
                                    .foregroundStyle(.primary)
                                    .padding(.horizontal, 16)
                                
                                // Quantity Input
                                HStack {
                                    Text("Quantity:")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    TextField("e.g., 1.0", text: $quantityString)
                                        .keyboardType(.decimalPad)
                                        .textFieldStyle(RoundedBorderTextFieldStyle())
                                        .frame(maxWidth: .infinity)
                                }
                                .padding(.horizontal, 16)
                                
                                // Price Input
                                HStack {
                                    Text("Price:")
                                        .font(.subheadline)
                                        .foregroundStyle(.secondary)
                                    TextField("e.g., 150.25", text: $priceString)
                                        .keyboardType(.decimalPad)
                                        .textFieldStyle(RoundedBorderTextFieldStyle())
                                        .frame(maxWidth: .infinity)
                                }
                                .padding(.horizontal, 16)
                                
                                // Buy/Sell buttons
                                HStack(spacing: 12) {
                                    Button(action: {
                                        performTrade(action: .buy, symbol: currentSymbol)
                                    }) {
                                        HStack {
                                            Image(systemName: "plus.circle.fill")
                                            Text("Buy")
                                                .fontWeight(.semibold)
                                        }
                                        .foregroundStyle(.white)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 16)
                                        .background(
                                            LinearGradient(
                                                colors: [Color.green, Color.mint],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            ),
                                            in: RoundedRectangle(cornerRadius: 12)
                                        )
                                        .shadow(color: .green.opacity(0.3), radius: 8, x: 0, y: 4)
                                    }
                                    
                                    Button(action: {
                                        performTrade(action: .sell, symbol: currentSymbol)
                                    }) {
                                        HStack {
                                            Image(systemName: "minus.circle.fill")
                                            Text("Sell")
                                                .fontWeight(.semibold)
                                        }
                                        .foregroundStyle(.white)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 16)
                                        .background(
                                            LinearGradient(
                                                colors: [Color.red, Color.pink],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            ),
                                            in: RoundedRectangle(cornerRadius: 12)
                                        )
                                        .shadow(color: .red.opacity(0.3), radius: 8, x: 0, y: 4)
                                    }
                                }
                                .padding(.horizontal, 16)
                            }
                            .glassCard()
                            .padding(.horizontal, 12)
                        }
                        
                        // Bottom spacing
                        Spacer(minLength: 20)
                    }
                    .padding(.vertical, 8)
                }
                .frame(maxWidth: .infinity)
                .onChange(of: stockLoader.currentPrice) { newValue in
                    if let price = newValue {
                        self.priceString = String(format: "%.2f", price)
                    } else {
                        self.priceString = ""
                    }
                }
                .onChange(of: selectedSymbol) { newValue in
                    if let currentMarketPrice = stockLoader.currentPrice {
                         self.priceString = String(format: "%.2f", currentMarketPrice)
                    } else {
                         self.priceString = "" // Or "Loading..."
                    }
                }
                .alert(isPresented: $isShowingAlert) {
                    Alert(title: Text(alertTitle), message: Text(alertMessage), dismissButton: .default(Text("OK")))
                }
            }
            .navigationBarHidden(true)
        }
        .navigationViewStyle(.stack)
    }

    private func performTrade(action: TradeAction, symbol: String) {
        guard let quantity = Double(quantityString), quantity > 0 else {
            self.alertTitle = "Invalid Quantity"
            self.alertMessage = "Please enter a valid positive quantity."
            self.isShowingAlert = true
            return
        }
        
        let finalTradePrice: Double
        
        if let priceInput = Double(priceString), priceInput > 0 {
            finalTradePrice = priceInput
        } else if priceString.isEmpty, let marketPrice = stockLoader.currentPrice, marketPrice > 0 {
            // Wenn das Preisfeld leer ist, aber ein Marktpreis verfügbar ist, verwende den Marktpreis.
            finalTradePrice = marketPrice
            // Optional: Aktualisiere das Preisfeld, um den verwendeten Marktpreis anzuzeigen
            // self.priceString = String(format: "%.2f", marketPrice)
        } else {
            self.alertTitle = "Invalid Price"
            self.alertMessage = "Please enter a valid positive price, or ensure a market price is available if the field is empty."
            self.isShowingAlert = true
            return
        }

        Task {
            let result: Result<TradeResponse, TradeError>
            switch action {
            case .buy:
                result = await tradeService.buyStock(symbol: symbol, quantity: quantity, price: finalTradePrice, authManager: authManager)
            case .sell:
                result = await tradeService.sellStock(symbol: symbol, quantity: quantity, price: finalTradePrice, authManager: authManager)
            }
            
            await MainActor.run {
                switch result {
                case .success(let response):
                    self.alertTitle = response.success ? "Trade Successful" : "Trade Failed"
                    self.alertMessage = response.message
                    if response.success {
                        // Optionally, refresh user balance or other relevant data
                        // authManager.fetchUserDetails() // Example
                        // stockLoader.loadPortfolio() // Example
                    }
                case .failure(let error):
                    self.alertTitle = "Trade Error"
                    self.alertMessage = "An error occurred: \(error.localizedDescription)"
                }
                self.isShowingAlert = true
            }
        }
    }
}

#Preview {
    ViewTrade(authManager: AuthManager())
}
