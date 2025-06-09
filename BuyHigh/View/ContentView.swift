//
//  ContentView.swift
//  BuyHigh
//
//  Created by Julian Stosse on 28.05.25.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var selectedPage: NavBarPage = .dashboard // Behalten für die interne Navigation der Hauptansicht

    var body: some View {
        // Entscheiden, welche Ansicht basierend auf dem Login-Status angezeigt wird
        if authManager.isLoggedIn {
            // Hauptansicht der App nach dem Login
            ZStack {
                // Glass Background für die gesamte App
                LinearGradient(
                    colors: [
                        Color(.systemBackground),
                        Color.blue.opacity(0.02),
                        Color.purple.opacity(0.01),
                        Color(.systemBackground)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    Group {
                        switch selectedPage {
                        case .dashboard:
                            ViewDashboard(authManager: authManager)
                        case .trade:
                            ViewTrade(authManager: authManager)
                        case .game:
                            ViewGame()
                        case .learn:
                            ViewLearn()
                        case .profile:
                            ViewProfile(authManager: authManager)
                        case .transactions:
                            ViewTransactions(authManager: authManager)
                        case .ai:
                            ViewAI()
                            
                        }
                    }
                    
                    NavBar(selectedPage: $selectedPage)
                }
            }
            .onAppear {
                print("ContentView: Displaying main app content (isLoggedIn is true)")
            }
        } else {
            // Login-Ansicht, wenn nicht eingeloggt
            ViewLogin()
                .onAppear {
                    print("ContentView: Displaying ViewLogin (isLoggedIn is false)")
                }
        }
    }
}

#Preview {
    // Für die Vorschau können wir verschiedene Zustände testen:
    let previewAuthManager = AuthManager()
    // Um den nicht eingeloggten Zustand zu sehen:
    // previewAuthManager.isLoggedIn = false
    // Um den eingeloggten Zustand zu sehen (Standard, wenn UserDefaults leer oder true):
    // previewAuthManager.isLoggedIn = true
    
    return ContentView().environmentObject(previewAuthManager)
}
