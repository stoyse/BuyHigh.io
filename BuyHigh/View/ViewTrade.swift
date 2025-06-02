//
//  ViewTrade.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewTrade: View {
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var assetLoader: AssetLoader

    // Initializer, um authManager entgegenzunehmen und für AssetLoader zu verwenden
    init(authManager: AuthManager) {
        _assetLoader = StateObject(wrappedValue: AssetLoader(authManager: authManager))
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack {
                    Image(systemName: "chart.bar")
                        .imageScale(.large)
                        .foregroundStyle(.tint)
                        .padding(.top)
                    
                    Text("Start Trading!")
                        .font(.title)
                        .padding(.bottom)
                    
                    // CardTrade Komponente hinzufügen und AssetLoader übergeben
                    CardTrade(authManager: authManager, assetLoader: assetLoader)
                        .padding(.horizontal)
                        .padding(.bottom)
                    
                    Spacer()
                }
            }
            .onAppear {
                // Assets laden, wenn die Ansicht erscheint.
                assetLoader.fetchAssets()
            }
            .padding()
        }
    }
}

#Preview {
    // AuthManager für die Preview bereitstellen
    let authManager = AuthManager() // Erstellt eine neue Instanz für die Preview
    // AssetLoader wird innerhalb von ViewTrade initialisiert, das den authManager benötigt.
    ViewTrade(authManager: authManager) // Explizite Übergabe des AuthManagers
        .environmentObject(authManager) // Stellt ihn auch für Kind-Views in der Umgebung bereit
}
