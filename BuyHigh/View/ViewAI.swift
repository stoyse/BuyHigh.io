//
//  ViewAI.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import SwiftUI

struct ViewAI: View {
    var body: some View {
        VStack {
            Image(systemName: "brain")
            Text("Hello, Mr.Stonks!")
            CardMrStonks() // Added CardMrStonks
            Spacer()
        }
    }
}

#Preview {
    ViewAI()
}
