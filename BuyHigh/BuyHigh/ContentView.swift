//
//  ContentView.swift
//  BuyHigh
//
//  Created by Julian Stosse on 28.05.25.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager // Added AuthManager
    @State private var selectedPage: NavBarPage = .dashboard

    var body: some View {
        VStack(spacing: 0) {
            Group {
                switch selectedPage {
                case .dashboard:
                    ViewDashboard(authManager: authManager)
                case .profile:
                  ViewProfile(authManager: authManager) // Pass AuthManager
                case .trade:
                    ViewTrade()
                case .game:
                    ViewGame()
                case .learn:
                    ViewLearn()
                }
            }
            NavBar(selectedPage: $selectedPage)
        }
    }
}

#Preview {

    ContentView()
        .environmentObject(AuthManager()) // Add AuthManager for preview
}
