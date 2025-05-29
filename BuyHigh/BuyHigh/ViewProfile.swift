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
        VStack(spacing: 0) {
            if userLoader.isLoading {
                ProgressView("Loading Profile...")
            } else if let userData = userLoader.userData {
                VStack {
                    Image(systemName: "person.crop.circle")
                        .resizable()
                        .scaledToFit()
                        .frame(width: 100, height: 100)
                        .padding(.bottom, 10)
                    
                    Text("Hello, \(userData.username ?? "User")!")
                        .font(.title)
                    Text(userData.email)
                        .font(.subheadline)
                        .foregroundColor(.gray)
                    
                    // Display other user data as needed
                    // Text("User ID: \\(userData.id)")
                    // if let fbUid = userData.firebase_uid { Text("Firebase UID: \\(fbUid)") }

                    Spacer()
                    
                    Button(action: {
                        authManagerEnv.logout() // Changed from authManager to authManagerEnv
                    }) {
                        Text("Logout")
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding()
                            .frame(width: 220, height: 60)
                            .background(Color.red)
                            .cornerRadius(15.0)
                    }
                    .padding(.top, 50)
                }
                .padding()
            } else if let errorMessage = userLoader.errorMessage {
                VStack {
                    Text("Error")
                        .font(.largeTitle)
                        .foregroundColor(.red)
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding()
                    Button("Retry") {
                        userLoader.fetchUserData()
                    }
                    .padding()
                }
            } else {
                // Fallback or initial state before loading starts
                ProgressView() // Or a message like "Tap to load profile"
            }
        }
        .onAppear {
            // userLoader.authManager = authManagerEnv // No longer needed, authManager is set in UserLoader's init
            userLoader.fetchUserData()
        }
        // Optional: Navigation zu anderen Seiten
        /*.onChange(of: selectedPage) { newPage in
            // Hier könntest du ggf. Navigation auslösen, falls ViewProfile nur für Profil gedacht ist
        }*/
    }
}

// Adjust Preview to provide AuthManager for UserLoader
#Preview {
    let authManager = AuthManager()
    // Simulate logged-in state for preview if needed
    // authManager.isLoggedIn = true
    // authManager.idToken = "fake-token"
    // authManager.userId = 123
    
    // Use the new initializer for the preview
    return ViewProfile(authManager: authManager)
        .environmentObject(authManager) // Still provide it for @EnvironmentObject if used directly in ViewProfile
}
