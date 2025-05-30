//
//  BuyHighApp.swift
//  BuyHigh
//
//  Created by Julian Stosse on 28.05.25.
//

import SwiftUI
import FirebaseCore // FirebaseCore importieren

@main
struct BuyHighApp: App {
    @StateObject var authManager = AuthManager() // Stelle sicher, dass AuthManager hier als StateObject initialisiert wird

    // Firebase konfigurieren
    init() {
        FirebaseApp.configure()
        print("Firebase configured!") // Optional: Zum Debuggen
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager) // AuthManager an die Umgebung übergeben
        }
    }
}

// Vorhandener Code in ContentView.swift oder wo auch immer deine Hauptansicht ist:
// Stelle sicher, dass ContentView und andere Views, die AuthManager benötigen,
// ihn über @EnvironmentObject empfangen:
//
// struct ContentView: View {
//     @EnvironmentObject var authManager: AuthManager
//
//     var body: some View {
//         if authManager.isLoggedIn {
//             // Hauptansicht der App nach dem Login
//             ViewDashboard() // Oder deine Haupt-Tab-Ansicht etc.
//         } else {
//             // Login-Ansicht
//             ViewLogin()
//         }
//     }
// }
