//
//  ViewGame.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewGame: View {
    @State private var selectedPage: NavBarPage = .game

    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Image(systemName: "gamecontroller")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                Text("Hello, Gamer!")
                Spacer()
            }
            .padding()
            //NavBar(selectedPage: $selectedPage)
        }

    }
}

#Preview {
    ViewGame()
}
