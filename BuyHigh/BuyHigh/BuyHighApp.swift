//
//  BuyHighApp.swift
//  BuyHigh
//
//  Created by Julian Stosse on 28.05.25.
//

import SwiftUI

@main
struct BuyHighApp: App {
    @StateObject private var authManager = AuthManager()

    var body: some Scene {
        WindowGroup {
            if authManager.isLoggedIn {
                ContentView()
                    .environmentObject(authManager)
            } else {
                ViewLogin()
                    .environmentObject(authManager)
            }
        }
    }
}
