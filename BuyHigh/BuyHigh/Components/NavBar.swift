//
//  NavBar.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

enum NavBarPage {
    case dashboard
    case trade
    case game
    case learn
    case profile
    case transactions
    case ai  
}

struct NavBar: View {
    @Binding var selectedPage: NavBarPage

    var body: some View {
        HStack(spacing: 0) {
            Spacer()
            
            NavBarButton(
                icon: "house.fill",
                isSelected: selectedPage == .dashboard,
                action: { selectedPage = .dashboard }
            )
            
            Spacer()
            
            NavBarButton(
                icon: "chart.line.uptrend.xyaxis",
                isSelected: selectedPage == .trade,
                action: { selectedPage = .trade }
            )
            
            Spacer()
            
            NavBarButton(
                icon: "gamecontroller.fill",
                isSelected: selectedPage == .game,
                action: { selectedPage = .game }
            )
            
            Spacer()
            
            NavBarButton(
                icon: "book.fill",
                isSelected: selectedPage == .learn,
                action: { selectedPage = .learn }
            )
            
            Spacer()
            
            NavBarButton(
                icon: "brain",
                isSelected: selectedPage == .ai,
                action: { selectedPage = .ai }
            )
            
            Spacer()
        }
        .padding(.vertical, 16)
        .padding(.horizontal, 20)
        .background(
            .regularMaterial,
            in: RoundedRectangle(cornerRadius: 25)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 25)
                .stroke(Color.white.opacity(0.2), lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.1), radius: 20, x: 0, y: 10)
        .padding(.horizontal, 20)
        .padding(.bottom, 10)
    }
}

struct NavBarButton: View {
    let icon: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            ZStack {
                if isSelected {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.thinMaterial)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                        )
                        .frame(width: 40, height: 40)
                        .shadow(color: .blue.opacity(0.3), radius: 8, x: 0, y: 4)
                }
                
                Image(systemName: icon)
                    .font(.title3)
                    .foregroundStyle(
                        isSelected ?
                            LinearGradient(
                                colors: [Color.blue, Color.purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ) :
                            LinearGradient(
                                colors: [Color.secondary],
                                startPoint: .center,
                                endPoint: .center
                            )
                    )
                    .scaleEffect(isSelected ? 1.1 : 1.0)
                    .animation(.easeInOut(duration: 0.2), value: isSelected)
            }
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    NavBar(selectedPage: .constant(.trade))
}
