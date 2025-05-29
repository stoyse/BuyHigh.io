//
//  ViewTrade.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewTrade: View {
    @State private var selectedPage: NavBarPage = .trade
    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Image(systemName: "chart.bar")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                Text("Start Trading!")
                Spacer()
            }
            .padding()
            //NavBar(selectedPage: $selectedPage)
        }

    }
}

#Preview {
    ViewTrade()
}
