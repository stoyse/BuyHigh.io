//
//  ViewLearn.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewLearn: View {
    @State private var selectedPage: NavBarPage = .learn
    
    var body: some View {
        ZStack {
            // Glass Background
            LinearGradient(
                colors: [
                    Color(.systemBackground),
                    Color.mint.opacity(0.04),
                    Color.green.opacity(0.02),
                    Color(.systemBackground)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 24) {
                    // Header Section
                    VStack(spacing: 20) {
                        // Icon with Glass Effect
                        ZStack {
                            RoundedRectangle(cornerRadius: 20)
                                .fill(.ultraThinMaterial)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 20)
                                        .stroke(
                                            LinearGradient(
                                                colors: [
                                                    Color.white.opacity(0.6),
                                                    Color.green.opacity(0.3),
                                                    Color.mint.opacity(0.2)
                                                ],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            ),
                                            lineWidth: 2
                                        )
                                )
                                .frame(width: 80, height: 80)
                                .shadow(color: .green.opacity(0.3), radius: 15, x: 0, y: 8)
                            
                            Image(systemName: "graduationcap.fill")
                                .font(.system(size: 35))
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: [Color.green, Color.mint],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                        }
                        
                        VStack(spacing: 8) {
                            Text("Start Learning!")
                                .font(.system(size: 28, weight: .bold, design: .rounded))
                                .foregroundStyle(
                                    LinearGradient(
                                        colors: [Color.primary, Color.green.opacity(0.8)],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .shadow(color: .green.opacity(0.2), radius: 5, x: 0, y: 2)
                            
                            Text("Test your trading knowledge")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .glassCard()
                    .padding(.horizontal)
                    
                    // Daily Quiz Section
                    CardDailyQuiz()
                        .padding(.horizontal)
                    
                    // Learning Resources Section
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
                                
                                Image(systemName: "books.vertical.fill")
                                    .foregroundStyle(
                                        LinearGradient(
                                            colors: [Color.blue, Color.purple],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .font(.title3)
                            }
                            
                            Text("Learning Resources")
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundStyle(.primary)
                            
                            Spacer()
                        }
                        
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 16) {
                            LearningResourceCard(
                                icon: "chart.bar.fill",
                                title: "Technical Analysis",
                                description: "Learn to read charts",
                                gradientColors: [Color.blue, Color.cyan]
                            )
                            
                            LearningResourceCard(
                                icon: "building.columns.fill",
                                title: "Fundamentals",
                                description: "Company analysis",
                                gradientColors: [Color.green, Color.mint]
                            )
                            
                            LearningResourceCard(
                                icon: "shield.fill",
                                title: "Risk Management",
                                description: "Protect your capital",
                                gradientColors: [Color.orange, Color.yellow]
                            )
                            
                            LearningResourceCard(
                                icon: "brain.head.profile",
                                title: "Psychology",
                                description: "Trading mindset",
                                gradientColors: [Color.purple, Color.pink]
                            )
                        }
                    }
                    .glassCard()
                    .padding(.horizontal)
                    
                    // Progress Section
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
                                
                                Image(systemName: "chart.line.uptrend.xyaxis")
                                    .foregroundStyle(
                                        LinearGradient(
                                            colors: [Color.green, Color.blue],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .font(.title3)
                            }
                            
                            Text("Your Progress")
                                .font(.title2)
                                .fontWeight(.bold)
                                .foregroundStyle(.primary)
                            
                            Spacer()
                        }
                        
                        VStack(spacing: 12) {
                            ProgressRow(
                                title: "Daily Quizzes Completed",
                                progress: 0.7,
                                value: "7/10"
                            )
                            
                            ProgressRow(
                                title: "Learning Modules",
                                progress: 0.3,
                                value: "3/10"
                            )
                            
                            ProgressRow(
                                title: "Achievement Badges",
                                progress: 0.5,
                                value: "5/10"
                            )
                        }
                    }
                    .glassCard()
                    .padding(.horizontal)
                }
                .padding(.vertical, 20)
            }
        }
        .navigationTitle("Learn")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct LearningResourceCard: View {
    let icon: String
    let title: String
    let description: String
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
                Text(title)
                    .font(.headline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                
                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(height: 120)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(.ultraThinMaterial)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                )
                .shadow(color: .black.opacity(0.05), radius: 8, x: 0, y: 4)
        )
    }
}

struct ProgressRow: View {
    let title: String
    let progress: Double
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(title)
                    .font(.subheadline)
                    .foregroundStyle(.primary)
                
                Spacer()
                
                Text(value)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.secondary)
            }
            
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 4)
                        .fill(.ultraThinMaterial)
                        .overlay(
                            RoundedRectangle(cornerRadius: 4)
                                .stroke(Color.white.opacity(0.2), lineWidth: 1)
                        )
                        .frame(height: 6)
                    
                    RoundedRectangle(cornerRadius: 4)
                        .fill(
                            LinearGradient(
                                colors: [Color.green, Color.mint],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * progress, height: 6)
                        .shadow(color: .green.opacity(0.3), radius: 2, x: 0, y: 1)
                }
            }
            .frame(height: 6)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    ViewLearn()
}
