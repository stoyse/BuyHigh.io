//
//  ViewProfile.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewProfile: View {
    let authManager: AuthManager
    @StateObject private var userLoader: UserLoader
    
    init(authManager: AuthManager) {
        self.authManager = authManager
        self._userLoader = StateObject(wrappedValue: UserLoader(authManager: authManager))
    }
    
    var body: some View {
        ZStack {
            // Glass Background
            LinearGradient(
                colors: [
                    Color(.systemBackground),
                    Color.purple.opacity(0.05),
                    Color.blue.opacity(0.03),
                    Color(.systemBackground)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    if userLoader.isLoading {
                        VStack {
                            ProgressView("Loading Profile...")
                                .padding()
                        }
                        .glassCard()
                        .padding(.horizontal)
                    }
                    else if let errorMessage = userLoader.errorMessage {
                        VStack(spacing: 16) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.title)
                                .foregroundStyle(.orange)
                                .shadow(color: .orange.opacity(0.3), radius: 5, x: 0, y: 2)
                            
                            Text("Error Loading Profile")
                                .font(.headline)
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
                        // Profile Header
                        VStack(spacing: 20) {
                            // Avatar Section
                            ZStack {
                                RoundedRectangle(cornerRadius: 25)
                                    .fill(.ultraThinMaterial)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 25)
                                            .stroke(
                                                LinearGradient(
                                                    colors: [
                                                        Color.white.opacity(0.6),
                                                        Color.purple.opacity(0.3),
                                                        Color.blue.opacity(0.2)
                                                    ],
                                                    startPoint: .topLeading,
                                                    endPoint: .bottomTrailing
                                                ),
                                                lineWidth: 2
                                            )
                                    )
                                    .frame(width: 100, height: 100)
                                    .shadow(color: .purple.opacity(0.3), radius: 15, x: 0, y: 8)
                                
                                Image(systemName: "person.fill")
                                    .font(.system(size: 45))
                                    .foregroundStyle(
                                        LinearGradient(
                                            colors: [Color.purple, Color.blue],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                            }
                            
                            // Name and Email
                            VStack(spacing: 8) {
                                if let username = userData.username {
                                    Text(username)
                                        .font(.system(size: 28, weight: .bold, design: .rounded))
                                        .foregroundStyle(
                                            LinearGradient(
                                                colors: [Color.primary, Color.purple.opacity(0.8)],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .shadow(color: .purple.opacity(0.2), radius: 5, x: 0, y: 2)
                                } else {
                                    Text("User")
                                        .font(.system(size: 28, weight: .bold, design: .rounded))
                                        .foregroundStyle(.primary)
                                }
                                
                                Text(userData.email)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .glassCard()
                        .padding(.horizontal)
                        
                        // Profile Stats Grid
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            ProfileStatCard(
                                icon: "star.fill",
                                title: "Level",
                                value: "\(userData.level ?? 0)",
                                gradientColors: [Color.orange, Color.yellow]
                            )
                            
                            ProfileStatCard(
                                icon: "bolt.fill",
                                title: "XP",
                                value: "\(userData.xp ?? 0)",
                                gradientColors: [Color.blue, Color.purple]
                            )
                            
                            ProfileStatCard(
                                icon: "chart.line.uptrend.xyaxis",
                                title: "Total Trades",
                                value: "\(userData.total_trades ?? 0)",
                                gradientColors: [Color.green, Color.mint]
                            )
                            
                            ProfileStatCard(
                                icon: "dollarsign.circle.fill",
                                title: "P&L",
                                value: String(format: "%.2f", userData.profit_loss ?? 0.0),
                                gradientColors: [Color.pink, Color.orange]
                            )
                        }
                        .padding(.horizontal)
                        
                        // Account Settings
                        VStack(alignment: .leading, spacing: 16) {
                            HStack {
                                ZStack {
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(.thinMaterial)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 12)
                                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                        )
                                        .frame(width: 40, height: 40)
                                    
                                    Image(systemName: "gear")
                                        .foregroundStyle(
                                            LinearGradient(
                                                colors: [Color.gray, Color.secondary],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .font(.title3)
                                }
                                
                                Text("Account Settings")
                                    .font(.title2)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.primary)
                                
                                Spacer()
                            }
                            
                            VStack(spacing: 12) {
                                ProfileSettingRow(
                                    icon: "envelope.fill",
                                    title: "Email",
                                    value: userData.email,
                                    isVerified: userData.email_verified ?? false
                                )
                                
                                ProfileSettingRow(
                                    icon: "calendar",
                                    title: "Member Since",
                                    value: formatDate(userData.created_at ?? ""),
                                    isVerified: true
                                )
                                
                                ProfileSettingRow(
                                    icon: "paintbrush.fill",
                                    title: "Theme",
                                    value: userData.theme?.capitalized ?? "System",
                                    isVerified: true
                                )
                            }
                        }
                        .glassCard()
                        .padding(.horizontal)
                        
                        // Logout Button
                        Button(action: {
                            authManager.logout()
                        }) {
                            HStack {
                                Image(systemName: "rectangle.portrait.and.arrow.right")
                                    .font(.title3)
                                Text("Logout")
                                    .font(.headline)
                                    .fontWeight(.semibold)
                            }
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(
                                LinearGradient(
                                    colors: [Color.red, Color.pink],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ),
                                in: RoundedRectangle(cornerRadius: 12)
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
                            )
                            .shadow(color: .red.opacity(0.4), radius: 15, x: 0, y: 8)
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.vertical, 20)
            }
        }
        .navigationTitle("Profile")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if userLoader.userData == nil && !userLoader.isLoading {
                userLoader.fetchUserData()
            }
        }
    }
    
    private func formatDate(_ dateString: String) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
        
        if let date = formatter.date(from: dateString) {
            let displayFormatter = DateFormatter()
            displayFormatter.dateStyle = .medium
            return displayFormatter.string(from: date)
        }
        
        return "Unknown"
    }
}

struct ProfileStatCard: View {
    let icon: String
    let title: String
    let value: String
    let gradientColors: [Color]
    
    var body: some View {
        VStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 12)
                    .fill(.thinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                    )
                    .frame(width: 45, height: 45)
                
                Image(systemName: icon)
                    .foregroundStyle(
                        LinearGradient(
                            colors: gradientColors,
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .font(.title2)
            }
            
            VStack(spacing: 4) {
                Text(value)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(.primary)
                
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .glassCard(cornerRadius: 16)
    }
}

struct ProfileSettingRow: View {
    let icon: String
    let title: String
    let value: String
    let isVerified: Bool
    
    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                RoundedRectangle(cornerRadius: 8)
                    .fill(.ultraThinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 8)
                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                    )
                    .frame(width: 30, height: 30)
                
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(value)
                    .font(.subheadline)
                    .foregroundStyle(.primary)
            }
            
            Spacer()
            
            if isVerified {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                    .font(.caption)
            }
        }
        .padding(.vertical, 8)
    }
}

#Preview {
    NavigationView {
        ViewProfile(authManager: AuthManager())
    }
}
