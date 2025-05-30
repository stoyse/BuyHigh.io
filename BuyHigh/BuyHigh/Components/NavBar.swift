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
            Button(action: { selectedPage = .dashboard }) {
                VStack { 
                    Image(systemName: "house")
                        .font(.title2)
                }
            }
            Spacer()
            Button(action: { selectedPage = .trade }) {
                Image(systemName: "chart.line.uptrend.xyaxis")
                    .font(.title2)
            }
            Spacer()
            Button(action: { selectedPage = .game }) {
                VStack { 
                    Image(systemName: "gamecontroller.fill")
                        .font(.title2)
                }
            }
            Spacer()
            Button(action: { selectedPage = .learn }) {
                VStack { 
                    Image(systemName: "book.fill")
                        .font(.title2)
                }
            }
            Spacer()
            Button(action: { selectedPage = .ai }) {
                VStack { 
                    Image(systemName: "brain")
                        .font(.title2)
                }
            }
            Spacer()
        }
        .padding(.vertical, 20.0)
        .frame(maxWidth: .infinity)
        .background(Color(.systemGray6))
        .shadow(radius: 5)
    }
}

#Preview {
    NavBar(selectedPage: .constant(.dashboard))
}
