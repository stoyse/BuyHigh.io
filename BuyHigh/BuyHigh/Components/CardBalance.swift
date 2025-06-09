//
//  CardBalance.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct CardBalance: View {
    let balance: Double?
    
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
                    
                    Image(systemName: "dollarsign.circle.fill")
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color.purple, Color.blue],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .font(.title2)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Current Balance")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                    
                    Text("Available for trading")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
                
                Spacer()
            }
            
            // Balance Amount mit Glow Effect
            HStack(alignment: .bottom) {
                if let balance = balance {
                    Text("$\(String(format: "%.2f", balance))")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color.primary, Color.primary.opacity(0.8)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .shadow(color: .blue.opacity(0.3), radius: 10, x: 0, y: 5)
                } else {
                    Text("$0.00")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundStyle(.tertiary)
                }
                
                Spacer()
            }
        }
        .glassCard(cornerRadius: 20)
        .contentShape(Rectangle())
    }
}


// Zur Erinnerung: Stellen Sie sicher, dass die übergeordnete Ansicht, die CardBalance verwendet,
// in eine NavigationView eingebettet ist, damit die Navigation funktioniert.
// Zum Beispiel:
/*
NavigationView {
    YourParentViewContainingCardBalance()
}
*/

#Preview {
    CardBalance(balance: 1234.56)
}




