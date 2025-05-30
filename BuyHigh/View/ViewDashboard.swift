//
//  ViewDashboard.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewDashboard: View {
    @State private var selectedPage: NavBarPage = .dashboard
    @EnvironmentObject var authManagerEnv: AuthManager
    @StateObject private var userLoader: UserLoader
    
    init(authManager: AuthManager) {
        _userLoader = StateObject(wrappedValue: UserLoader(authManager: authManager))
    }
    
    var body: some View {
        NavigationView { // Wrap with NavigationView
            ScrollView { // Wrap the main content in a ScrollView
                VStack {
                    if userLoader.isLoading {
                        ProgressView("Loading Profile...")
                            .padding()
                    }
                    else if let errorMessage = userLoader.errorMessage {
                        VStack { // Error message block
                            Text("Error")
                                .font(.title3) // Smaller than .largeTitle
                                .foregroundColor(.red)
                                .padding(.bottom, 2)
                            Text(errorMessage)
                                .foregroundColor(.red)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal)
                            Button("Try Again") {
                                userLoader.fetchUserData()
                            }
                            .padding(.top, 5)
                        }
                        .padding() // Add padding to the error VStack itself for better spacing
                    }
                    else if let userData = userLoader.userData {
                        let xp = Int(userData.xp ?? 0)
                        let level = Int(userData.level ?? 0)
                        
                        // Improved greeting design
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Hi there!")
                                    .font(.headline)
                                    .foregroundColor(.secondary)
                                
                                if let username = userData.username {
                                    Text(username)
                                        .font(.title2)
                                        .fontWeight(.bold)
                                        .foregroundColor(.primary)
                                } else {
                                    Text("Welcome")
                                        .font(.title2)
                                        .fontWeight(.bold)
                                        .foregroundColor(.primary)
                                }
                            }
                            
                            Spacer()
                            
                            // Profile navigation icon
                            NavigationLink(destination: ViewProfile(authManager: authManagerEnv)) {
                                Image(systemName: "person.circle.fill")
                                    .font(.title)
                                    .foregroundColor(.purple)
                            }
                        }
                        .padding(.horizontal)
                        .padding(.top, 8)
                        .padding(.bottom, 16)
                        
                        NavigationLink(destination: ViewTransactions(authManager: authManagerEnv)) { // Wrap CardBalance in NavigationLink
                            CardBalance(balance: userData.balance)
                        }
                        CardLevel(xp: xp, level: level)
                        
                        // Portfolio-Karte hinzufügen
                        CardPortfolio(authManager: authManagerEnv)
                            .padding(.top) // Etwas Abstand nach oben
                        
                        // Spacer() // Removed Spacer to allow ScrollView to manage content height
                    }
                    //.padding() // Padding for the error block
                    else {
                        Text("No user Data found.")
                            .padding()
                        // Spacer() // Removed Spacer here as well
                    }
                    
                } // End of main VStack
            } // End of ScrollView
            .onAppear {
                // Fetch user data if not already loaded or if retrying
                if userLoader.userData == nil && !userLoader.isLoading {
                    userLoader.fetchUserData()
                }
            }
            // .navigationTitle("Dashboard") // Optional: Add a title if desired
        }
        .navigationViewStyle(.stack) // Add for consistent stack navigation
    }
}

#Preview {
    let authManager = AuthManager()
    
    ViewDashboard(authManager: authManager)
        .environmentObject(authManager)
}
