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
        NavigationView {
            ZStack {
                // Animated Glass Background
                LinearGradient(
                    colors: [
                        Color(.systemBackground),
                        Color.blue.opacity(0.05),
                        Color.purple.opacity(0.03),
                        Color(.systemBackground)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        if userLoader.isLoading {
                            VStack {
                                ProgressView("Loading Profile...")
                                    .padding()
                                    .glassBackground(cornerRadius: 16)
                            }
                        }
                        else if let errorMessage = userLoader.errorMessage {
                            VStack(spacing: 16) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.title)
                                    .foregroundStyle(.orange)
                                    .shadow(color: .orange.opacity(0.3), radius: 5, x: 0, y: 2)
                                
                                Text("Error")
                                    .font(.title3)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.primary)
                                
                                Text(errorMessage)
                                    .foregroundStyle(.secondary)
                                    .multilineTextAlignment(.center)
                                
                                Button("Try Again") {
                                    userLoader.fetchUserData()
                                }
                                .glassButton()
                            }
                            .glassCard()
                            .padding(.horizontal)
                        }
                        else if let userData = userLoader.userData {
                            let xp = Int(userData.xp ?? 0)
                            let level = Int(userData.level ?? 0)
                            
                            // Improved greeting design mit Glass
                            HStack {
                                VStack(alignment: .leading, spacing: 8) {
                                    Text("Hi there!")
                                        .font(.headline)
                                        .foregroundStyle(.secondary)
                                    
                                    if let username = userData.username {
                                        Text(username)
                                            .font(.system(size: 24, weight: .bold, design: .rounded))
                                            .foregroundStyle(
                                                LinearGradient(
                                                    colors: [Color.primary, Color.blue.opacity(0.8)],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                )
                                            )
                                            .shadow(color: .blue.opacity(0.2), radius: 5, x: 0, y: 2)
                                    } else {
                                        Text("Welcome")
                                            .font(.system(size: 24, weight: .bold, design: .rounded))
                                            .foregroundStyle(.primary)
                                    }
                                }
                                
                                Spacer()
                                
                                NavigationLink(destination: ViewProfile(authManager: authManagerEnv)) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 16)
                                            .fill(.thinMaterial)
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 16)
                                                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                            )
                                            .frame(width: 50, height: 50)
                                            .shadow(color: .purple.opacity(0.2), radius: 8, x: 0, y: 4)
                                        
                                        Image(systemName: "person.circle.fill")
                                            .font(.title)
                                            .foregroundStyle(
                                                LinearGradient(
                                                    colors: [Color.purple, Color.blue],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                )
                                            )
                                    }
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.top, 8)
                            .padding(.bottom, 16)
                            
                            NavigationLink(destination: ViewTransactions(authManager: authManagerEnv)) {
                                CardBalance(balance: userData.balance)
                                    .padding(.horizontal)
                            }
                            .buttonStyle(PlainButtonStyle())
                            
                            CardLevel(xp: xp, level: level)
                                .padding(.horizontal)
                            
                            CardPortfolio(authManager: authManagerEnv)
                        }
                        else {
                            VStack {
                                Text("No user Data found.")
                                    .foregroundStyle(.secondary)
                            }
                            .glassCard()
                            .padding(.horizontal)
                        }
                    }
                }
                .onAppear {
                    // Fetch user data if not already loaded or if retrying
                    if userLoader.userData == nil && !userLoader.isLoading {
                        userLoader.fetchUserData()
                    }
                }
            }
        }
        .navigationViewStyle(.stack)
    }
}

#Preview {
    let authManager = AuthManager()
    
    ViewDashboard(authManager: authManager)
        .environmentObject(authManager)
}
