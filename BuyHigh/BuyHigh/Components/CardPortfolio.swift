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
        // Optional: Protokolliert die Initialisierung, um zu sehen, ob sie unerwartet oft aufgerufen wird.
        // print("CardPortfolio init - portfolioLoader instance: \\(portfolioLoader)")
    }
    
    var body: some View {
        // Protokolliert den Zustand des portfolioLoader jedes Mal, wenn body ausgewertet wird.
        let _ = { // Verwende einen Closure, um mehrere Print-Anweisungen sauber zu gruppieren
            print("CardPortfolio body: isLoading = \(portfolioLoader.isLoading)")
            print("CardPortfolio body: errorMessage = \(portfolioLoader.errorMessage ?? "No error message")")
            print("CardPortfolio body: portfolio.count = \(portfolioLoader.portfolio.count)")
        }()

        VStack(alignment: .leading, spacing: 0) {
            // Header mit Glass Design
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.thinMaterial)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                        )
                        .frame(width: 40, height: 40)
                    
                    Image(systemName: "briefcase.fill")
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color.blue, Color.purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .font(.title3)
                }
                
                Text("My Portfolio")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(.primary)
                
                Spacer()
            }
            .padding(.bottom, 16)

            if portfolioLoader.isLoading {
                let _ = print("CardPortfolio body: Zeige ProgressView")
                ProgressView("Loading Portfolio...")
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .center)
            } else if let errorMessage = portfolioLoader.errorMessage {
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundStyle(.orange)
                        .font(.title)
                        .shadow(color: .orange.opacity(0.3), radius: 5, x: 0, y: 2)
                    
                    Text("Error Loading Portfolio")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                    
                    Button("Try Again") {
                        if let userId = authManagerEnv.userId {
                            portfolioLoader.loadPortfolio(userID: userId)
                        }
                    }
                    .glassButton()
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .center)
            } else if portfolioLoader.portfolio.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "briefcase.fill")
                        .font(.system(size: 40))
                        .foregroundStyle(.tertiary)
                        .shadow(color: .gray.opacity(0.2), radius: 5, x: 0, y: 2)
                    
                    Text("Your Portfolio is Empty")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    
                    Text("Start trading to see your assets here.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .center)
            } else {
                let _ = print("CardPortfolio body: Zeige Liste mit \(portfolioLoader.portfolio.count) Elementen")

                // Dynamische Höhenberechnung für die Liste
                let numberOfRows = portfolioLoader.portfolio.count
                let rowHeight: CGFloat = 75 // Geschätzte/durchschnittliche Höhe für eine PortfolioItemRow (anpassbar)
                let maxVisibleRows = 4 // Maximale Anzahl von Zeilen, die angezeigt werden, bevor die Liste intern scrollt
                let maxListHeight = CGFloat(maxVisibleRows) * rowHeight
                
                let calculatedListHeight = CGFloat(numberOfRows) * rowHeight
                let listDisplayHeight = min(calculatedListHeight, maxListHeight)

                List {
                    ForEach(portfolioLoader.portfolio) { item in
                        PortfolioItemRow(item: item)
                            .listRowBackground(Color.clear)
                    }
                }
                .listStyle(PlainListStyle())
                .scrollContentBackground(.hidden)
                // .background(Color.green) // Hintergrund für die gesamte Liste - ENTFERNT
                // Wende die berechnete Höhe an. Stelle sicher, dass die Höhe nicht Null ist, wenn Elemente vorhanden sind.
                .frame(height: numberOfRows > 0 ? listDisplayHeight : 0) 
            }
        }
        .padding(20)
        .background(Color.gray.opacity(0.1)) // Reine SwiftUI-Farbe für den Hintergrund
        .cornerRadius(12)
        .glassCard(cornerRadius: 20)
        .padding(.horizontal)
        .padding(.vertical, 10)
    }
}

struct PortfolioItemRow: View {
    let item: Portfolio

    var body: some View {
        HStack(spacing: 16) {
            // Asset Icon mit Glass Effect
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(.ultraThinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                    )
                    .frame(width: 35, height: 35)
                
                Text(String(item.symbol.prefix(2)))
                    .font(.caption)
                    .fontWeight(.bold)
                    .foregroundStyle(.primary)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                Text(item.name)
                    .font(.headline)
                    .lineLimit(1)
                    .foregroundStyle(.primary)
                
                Text(item.symbol)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            Spacer()
            
            VStack(alignment: .trailing, spacing: 4) {
                Text(String(format: "$%.2f", item.value))
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundStyle(item.performance >= 0 ? Color.green : Color.red)
                    .shadow(color: (item.performance >= 0 ? Color.green : Color.red).opacity(0.3), radius: 3, x: 0, y: 1)
                
                Text("Qty: \(item.quantity, specifier: "%.2f")")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
                
                HStack(spacing: 4) {
                    Image(systemName: item.performance >= 0 ? "arrow.up.right" : "arrow.down.left")
                        .font(.caption)
                    Text(String(format: "%.2f%%", item.performance * 100))
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .foregroundStyle(item.performance >= 0 ? Color.green : Color.red)
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

#Preview {
    let mockAuthManager = AuthManager()
    let mockPortfolioLoader = PortfolioLoader(authManager: mockAuthManager)
    mockPortfolioLoader.portfolio = [
        Portfolio(symbol: "AAPL", name: "Apple Inc.", type: "Stock", quantity: 10, averagePrice: 150.0, currentPrice: 175.0, performance: 0.1667, sector: "Technology", value: 1750.0),
        Portfolio(symbol: "TSLA", name: "Tesla Inc.", type: "Stock", quantity: 5, averagePrice: 600.0, currentPrice: 700.0, performance: 0.1667, sector: "Automotive", value: 3500.0)
    ]
    return CardPortfolio(authManager: mockAuthManager)
        .environmentObject(mockAuthManager)
}

