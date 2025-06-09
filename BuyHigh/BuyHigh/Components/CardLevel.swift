//
//  CardLevel.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct CardLevel: View {
    let xp: Int
    let level: Int
    
    // XP requirements for each level (matching Dashboard logic)
    private let levels = [
        (level: 1, xp_required: 100),
        (level: 2, xp_required: 300),
        (level: 3, xp_required: 600),
        (level: 4, xp_required: 1000),
        (level: 5, xp_required: 2000)
    ]
    
    private var xpPercentage: Double {
        let currentLevelData = levels.first { $0.level == level }
        let xpFromPreviousLevels = level == 1 ? 0 : (levels.first { $0.level == level - 1 }?.xp_required ?? 0)
        
        guard let currentLevel = currentLevelData else { return 0 }
        
        let xpToCompleteCurrentLevel = currentLevel.xp_required
        let xpSpanOfCurrentLevel = xpToCompleteCurrentLevel - xpFromPreviousLevels
        let xpEarnedInCurrentLevel = xp - xpFromPreviousLevels
        
        if xpSpanOfCurrentLevel > 0 {
            let percent = Double(xpEarnedInCurrentLevel) / Double(xpSpanOfCurrentLevel)
            return max(0, min(percent, 1.0))
        }
        
        return xp >= xpToCompleteCurrentLevel ? 1.0 : 0.0
    }
    
    private var nextLevelXP: Int {
        return levels.first { $0.level == level + 1 }?.xp_required ?? 0
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header mit Glass Icon
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.thinMaterial)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                        )
                        .frame(width: 45, height: 45)
                    
                    Image(systemName: "star.fill")
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color.orange, Color.yellow],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .font(.title2)
                        .shadow(color: .orange.opacity(0.5), radius: 5, x: 0, y: 2)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Trader Level")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                    
                    Text("Experience Points")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
                
                Spacer()
            }
            
            // Level Display mit Glow
            HStack(alignment: .bottom) {
                Text("Level \(level)")
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [Color.primary, Color.orange.opacity(0.8)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .shadow(color: .orange.opacity(0.3), radius: 8, x: 0, y: 4)
                
                Spacer()
            }
            
            // XP Progress Bar mit Glass Effect
            VStack(alignment: .leading, spacing: 8) {
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        // Background Track
                        RoundedRectangle(cornerRadius: 6)
                            .fill(.thinMaterial)
                            .overlay(
                                RoundedRectangle(cornerRadius: 6)
                                    .stroke(Color.white.opacity(0.2), lineWidth: 1)
                            )
                            .frame(height: 8)
                        
                        // Progress Fill
                        RoundedRectangle(cornerRadius: 6)
                            .fill(
                                LinearGradient(
                                    colors: [Color.orange, Color.yellow, Color.orange],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: geometry.size.width * xpPercentage, height: 8)
                            .shadow(color: .orange.opacity(0.5), radius: 4, x: 0, y: 2)
                    }
                }
                .frame(height: 8)
                
                // XP Text
                HStack {
                    Text("\(xp) XP")
                        .font(.caption)
                        .fontWeight(.medium)
                        .foregroundStyle(.secondary)
                    
                    Spacer()
                    
                    if nextLevelXP > 0 {
                        Text("\(nextLevelXP) XP")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundStyle(.secondary)
                    } else {
                        Text("Max Level")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundStyle(.orange)
                    }
                }
            }
        }
        .glassCard(cornerRadius: 20)
    }
}

#Preview {
    VStack(spacing: 20) {
        CardLevel(xp: 150, level: 1)
        CardLevel(xp: 450, level: 2)
        CardLevel(xp: 1500, level: 4)
    }
    .padding()
    .background(Color(.systemGroupedBackground))
}
