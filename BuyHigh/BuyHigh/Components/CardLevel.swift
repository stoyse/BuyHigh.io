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
        VStack(alignment: .leading, spacing: 12) {
            // Header mit Icon
            HStack {
                // Icon Container
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color.orange.opacity(0.1))
                        .frame(width: 40, height: 40)
                    
                    Image(systemName: "star.fill")
                        .foregroundColor(.orange)
                        .font(.title2)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Trader Level")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    Text("Experience Points")
                        .font(.caption2)
                        .foregroundColor(.secondary.opacity(0.7))
                }
                
                Spacer()
            }
            
            // Level Display
            HStack(alignment: .bottom) {
                Text("Level \(level)")
                    .font(.title)
                    .fontWeight(.bold)
                    .foregroundColor(.primary)
                
                Spacer()
            }
            
            // XP Progress Bar
            VStack(alignment: .leading, spacing: 4) {
                // Progress Bar
                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color(.systemGray5))
                            .frame(height: 6)
                        
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.orange)
                            .frame(width: geometry.size.width * xpPercentage, height: 6)
                    }
                }
                .frame(height: 6)
                
                // XP Text
                HStack {
                    Text("\(xp) XP")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    
                    Spacer()
                    
                    if nextLevelXP > 0 {
                        Text("\(nextLevelXP) XP")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    } else {
                        Text("Max Level")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .padding(20)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(.systemBackground))
                .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 4)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color(.systemGray5), lineWidth: 1)
        )
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
