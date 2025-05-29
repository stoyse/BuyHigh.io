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
            }
            else if let userData = userLoader.userData {
                let xp = Int(userData.xp ?? 0)
                let level = Int(userData.level ?? 0)
                CardBalance(balance: userData.balance)
                CardLevel(xp: xp, level: level)
                Spacer()
            }
            //.padding() // Padding for the error block
            else {
                Text("No user Data found.")
                    .padding()
                Spacer()
            }
            
        }
    Spacer()
        .onAppear {
            // Fetch user data if not already loaded or if retrying
            if userLoader.userData == nil && !userLoader.isLoading {
                userLoader.fetchUserData()
            }
        }
    }
}

#Preview {
    let authManager = AuthManager()
    
    ViewDashboard(authManager: authManager)
        .environmentObject(authManager)
}
