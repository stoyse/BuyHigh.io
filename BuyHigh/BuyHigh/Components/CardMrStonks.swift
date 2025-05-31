//
//  CardMrStonks.swift
//  BuyHigh
//
//  Created by Julian Stosse on 31.05.25.
//

import SwiftUI

struct CardMrStonks: View {
    let dogMessage = "Hello trader! Remember: Buy high, sell higher! Diamond hands only! 💎🙌"

    var body: some View {
        VStack(alignment: .center, spacing: 16) {
            Image(systemName: "person.crop.circle.fill") // Placeholder image
                .resizable()
                .scaledToFit()
                .frame(width: 80, height: 80)
                .foregroundColor(.gray)
                .padding(.top)

            Text(dogMessage)
                .font(.headline)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true) // Allow text to wrap

            // Optional: Add a title for the card
            Text("Mr. Stonks Says:")
                .font(.caption)
                .foregroundColor(.secondary)
                .padding(.bottom)
        }
        .padding()
        .background(Color(UIColor.systemGray6)) // Using systemGray6 for consistency
        .cornerRadius(10)
        .shadow(radius: 3)
        .frame(maxWidth: .infinity) // Ensure the card takes available width
    }
}

#Preview {
    CardMrStonks()
}
