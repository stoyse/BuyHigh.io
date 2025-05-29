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
        VStack(alignment: .leading, spacing: 12) {
            // Header mit Icon
            HStack {
                // Icon Container
                ZStack {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color.purple.opacity(0.1))
                        .frame(width: 40, height: 40)
                    
                    Image(systemName: "dollarsign.circle")
                        .foregroundColor(.purple)
                        .font(.title2)
                }
                
                VStack(alignment: .leading, spacing: 2) {
                    Text("Current Balance")
                        .font(.caption)
                        .fontWeight(.semibold)
                        .foregroundColor(.secondary)
                    
                    Text("Available for trading")
                        .font(.caption2)
                        .foregroundColor(.secondary.opacity(0.7))
                }
                
                Spacer()
            }
            
            // Balance Amount
            HStack(alignment: .bottom) {
                if let balance = balance {
                    Text("$\(String(format: "%.2f", balance))")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.primary)
                } else {
                    Text("$0.00")
                        .font(.title)
                        .fontWeight(.bold)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
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




