//
//  CardPortfolio.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import SwiftUI

// Es wird davon ausgegangen, dass AuthManager, PortfolioLoader und Portfolio
// im aktuellen Modul/Target verfügbar sind und korrekt eingebunden wurden.

struct CardPortfolio: View {
    @EnvironmentObject var authManagerEnv: AuthManager
    @StateObject private var portfolioLoader: PortfolioLoader
    
    init(authManager: AuthManager) {
        _portfolioLoader = StateObject(wrappedValue: PortfolioLoader(authManager: authManager))
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("My Portfolio")
                .font(.title2)
                .fontWeight(.bold)
                .padding([.leading, .top])
                .padding(.bottom, 8)

            if portfolioLoader.isLoading {
                ProgressView("Loading Portfolio...")
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
            } else if let errorMessage = portfolioLoader.errorMessage {
                VStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                        .font(.title)
                        .padding(.bottom, 2)
                    Text("Error Loading Portfolio")
                        .font(.headline)
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    Button("Try Again") {
                        if let userId = authManagerEnv.userId {
                            portfolioLoader.loadPortfolio(userID: userId)
                        }
                    }
                    .padding(.top, 8)
                    .buttonStyle(.bordered)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .center)
            } else if portfolioLoader.portfolio.isEmpty {
                VStack {
                    Image(systemName: "briefcase.fill")
                        .font(.largeTitle)
                        .foregroundColor(.secondary)
                        .padding(.bottom, 4)
                    Text("Your Portfolio is Empty")
                        .font(.headline)
                    Text("Start trading to see your assets here.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .center)
            } else {
                List {
                    ForEach(portfolioLoader.portfolio) { item in
                        PortfolioItemRow(item: item)
                    }
                }
                .listStyle(PlainListStyle())
            }
        }
        .onAppear {
            if portfolioLoader.portfolio.isEmpty && portfolioLoader.errorMessage == nil && !portfolioLoader.isLoading {
                if let userId = authManagerEnv.userId {
                    portfolioLoader.loadPortfolio(userID: userId)
                } else {
                    // Hier könnte eine Meldung für den nicht eingeloggten Zustand stehen
                    // portfolioLoader.errorMessage = "Please log in to view your portfolio."
                }
            }
        }
        .background(Color.gray.opacity(0.1)) // Reine SwiftUI-Farbe für den Hintergrund
        .cornerRadius(12)
        .padding(.horizontal)
        .padding(.vertical, 10)
    }
}

struct PortfolioItemRow: View {
    let item: Portfolio // Sicherstellen, dass die Struktur `Portfolio` hier bekannt ist.

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.headline)
                    .lineLimit(1)
                Text(item.symbol)
                    .font(.subheadline)
                    .foregroundColor(.gray)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(String(format: "$%.2f", item.value))
                    .font(.headline)
                    .foregroundColor(item.performance >= 0 ? .green : .red)
                
                Text("Qty: \\(item.quantity)")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                HStack(spacing: 4) {
                    Image(systemName: item.performance >= 0 ? "arrow.up.right" : "arrow.down.left")
                        .font(.caption)
                    Text(String(format: "%.2f%%", item.performance * 100))
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .foregroundColor(item.performance >= 0 ? .green : .red)
            }
        }
        .padding(.vertical, 8)
    }
}

#if DEBUG
struct CardPortfolio_Previews: PreviewProvider {
    static var previews: some View {
        // WICHTIG: Stelle sicher, dass AuthManager, PortfolioLoader und Portfolio
        // korrekt definiert und im Target verfügbar sind. Ohne das werden Previews nicht funktionieren.

        // Szenario 1: Erfolgreich geladene Daten
        let dataAuthManager = AuthManager()
        // dataAuthManager.userId = 1 // Setze ggf. eine Test-UserID
        // dataAuthManager.isLoggedIn = true
        let dataPortfolioLoader = PortfolioLoader(authManager: dataAuthManager)
        dataPortfolioLoader.portfolio = [
            Portfolio(symbol: "AAPL", name: "Apple Inc.", type: "Stock", quantity: 10, averagePrice: 150.0, currentPrice: 175.0, performance: (175.0-150.0)/150.0, sector: "Technology", value: 1750.0),
            Portfolio(symbol: "MSFT", name: "Microsoft Corp.", type: "Stock", quantity: 5, averagePrice: 300.0, currentPrice: 290.0, performance: (290.0-300.0)/300.0, sector: "Technology", value: 1450.0)
        ]
        dataPortfolioLoader.isLoading = false
        dataPortfolioLoader.errorMessage = nil

        // Szenario 2: Leeres Portfolio
        let emptyAuthManager = AuthManager()
        // emptyAuthManager.userId = 2
        // emptyAuthManager.isLoggedIn = true
        let emptyPortfolioLoader = PortfolioLoader(authManager: emptyAuthManager)
        emptyPortfolioLoader.portfolio = []
        emptyPortfolioLoader.isLoading = false
        emptyPortfolioLoader.errorMessage = nil

        // Szenario 3: Fehlerzustand
        let errorAuthManager = AuthManager()
        // errorAuthManager.userId = 3
        // errorAuthManager.isLoggedIn = true
        let errorPortfolioLoader = PortfolioLoader(authManager: errorAuthManager)
        errorPortfolioLoader.portfolio = []
        errorPortfolioLoader.isLoading = false
        errorPortfolioLoader.errorMessage = "Network Error: Could not fetch portfolio."

        // Szenario 4: Ladezustand
        let loadingAuthManager = AuthManager()
        // loadingAuthManager.userId = 4
        // loadingAuthManager.isLoggedIn = true
        let loadingPortfolioLoader = PortfolioLoader(authManager: loadingAuthManager)
        loadingPortfolioLoader.portfolio = []
        loadingPortfolioLoader.isLoading = true
        loadingPortfolioLoader.errorMessage = nil

        return Group {
            NavigationView {
                CardPortfolio(authManager: dataAuthManager)
            }
            .environmentObject(dataAuthManager)
            .previewDisplayName("Data Loaded")

            NavigationView {
                CardPortfolio(authManager: emptyAuthManager)
            }
            .environmentObject(emptyAuthManager)
            .previewDisplayName("Empty Portfolio")

            NavigationView {
                CardPortfolio(authManager: errorAuthManager)
            }
            .environmentObject(errorAuthManager)
            .previewDisplayName("Error State")

            NavigationView {
                CardPortfolio(authManager: loadingAuthManager)
            }
            .environmentObject(loadingAuthManager)
            .previewDisplayName("Loading State")
        }
    }
}
#endif

