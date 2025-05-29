//
//  ViewProfile.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewProfile: View {
    @EnvironmentObject var authManagerEnv: AuthManager // Renamed to avoid conflict if needed, or keep as authManager
    @StateObject private var userLoader: UserLoader

    // Explicit initializer to pass AuthManager to UserLoader
    init(authManager: AuthManager) {
        _userLoader = StateObject(wrappedValue: UserLoader(authManager: authManager))
    }

    var body: some View {
        VStack { // Main container
            // User ID Area (Top)
            VStack {
                if let uid = userLoader.userData?.id { // Prefer userData.id if fetch was successful
                    Text("User ID: \\(uid)")
                } else if let uid = authManagerEnv.userId { // Fallback to authManager.userId
                    Text("User ID: \\(uid)")
                } else {
                    Text("User ID: Nicht verfügbar")
                }
            }
            .font(.headline)
            .padding(.top)

            // Dynamic Content Area (Middle)
            if userLoader.isLoading {
                ProgressView("Loading Profile...")
                    .padding()
            } else if let errorMessage = userLoader.errorMessage {
                VStack { // Error message block
                    Text("Fehler")
                        .font(.title3) // Smaller than .largeTitle
                        .foregroundColor(.red)
                        .padding(.bottom, 2)
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                    Button("Erneut versuchen") {
                        userLoader.fetchUserData()
                    }
                    .padding(.top, 5)
                }
                .padding() // Padding for the error block
            } else if let userData = userLoader.userData { // Changed to unwrap userData
                // Display User Details
                List { // Using a List for better structure and scrollability if content grows
                    Section(header: Text("Benutzerinformationen").font(.title2)) {
                        HStack {
                            Text("Username:")
                                .fontWeight(.bold)
                            Spacer()
                            Text(userData.username ?? "N/A")
                        }
                        HStack {
                            Text("Email:")
                                .fontWeight(.bold)
                            Spacer()
                            Text(userData.email)
                        }
                        if let balance = userData.balance {
                            HStack {
                                Text("Balance:")
                                    .fontWeight(.bold)
                                Spacer()
                                Text(String(format: "%.2f", balance))
                            }
                        }
                        if let level = userData.level {
                            HStack {
                                Text("Level:")
                                    .fontWeight(.bold)
                                Spacer()
                                Text(String(level))
                            }
                        }
                        if let xp = userData.xp {
                            HStack {
                                Text("XP:")
                                    .fontWeight(.bold)
                                Spacer()
                                Text(String(xp))
                            }
                        }
                        if let trades = userData.total_trades {
                            HStack {
                                Text("Trades:")
                                    .fontWeight(.bold)
                                Spacer()
                                Text(String(trades))
                            }
                        }
                    }
                }
                .listStyle(GroupedListStyle()) // Apply a grouped list style
                
            } else {
                // Initial state, not loading, no error, no data.
                Text("Keine Benutzerdaten zum Anzeigen vorhanden.")
                    .padding()
                Spacer() // Ensures logout button is pushed down.
            }

            Spacer() // Pushes Logout button to the bottom

            // Logout Button Area (Bottom)
            Button(action: {
                authManagerEnv.logout()
            }) {
                Text("Logout")
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding()
                    .frame(width: 220, height: 60)
                    .background(Color.red)
                    .cornerRadius(15.0)
            }
            .padding(.bottom)
        }
        .onAppear {
            // Fetch user data if not already loaded or if retrying
            if userLoader.userData == nil && !userLoader.isLoading {
                 userLoader.fetchUserData()
            }
        }
    }
}

// Adjust Preview to provide AuthManager for UserLoader
#Preview {
    let authManager = AuthManager()

    
    // Use the new initializer for the preview
    return ViewProfile(authManager: authManager)
        .environmentObject(authManager) // Still provide it for @EnvironmentObject if used directly in ViewProfile
}
