//
//  ContentView.swift
//  BuyHigh
//
//  Created by Julian Stosse on 28.05.25.
//

import SwiftUI

struct ContentView: View {
    @State private var selectedPage: NavBarPage = .dashboard

    var body: some View {
        VStack(spacing: 0) {
            Group {
                switch selectedPage {
                case .dashboard:
                    VStack {
                        Image(systemName: "house")
                            .imageScale(.large)
                            .foregroundStyle(.tint)
                        Text("Hello, world!")
                        Spacer()
                    }
                    .padding()
                case .profile:
                    ViewProfile()
                case .trade:
                    ViewTrade()
                case .game:
                    ViewGame()
                case .learn:
                    ViewLearn()
                }
            }
            NavBar(selectedPage: $selectedPage)
        }
    }
}

#Preview {
    ContentView()
}
