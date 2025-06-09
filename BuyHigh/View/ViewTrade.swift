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
                        
                        if selectedSymbol != nil {
                            VStack(alignment: .leading, spacing: 16) {
                                HStack {
                                    Text("Trading Actions")
                                        .font(.headline)
                                        .foregroundStyle(.primary)
                                    
                                    Spacer()
                                }
                                .padding(.horizontal, 16)
                                
                                // Buy/Sell buttons
                                HStack(spacing: 12) {
                                    Button(action: {
                                        // Handle buy action
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
                                        // Handle sell action
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
            }
            .navigationBarHidden(true)
        }
        .navigationViewStyle(.stack)
    }
}

#Preview {
    ViewTrade(authManager: AuthManager())
}
