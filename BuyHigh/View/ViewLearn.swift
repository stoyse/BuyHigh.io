//
//  ViewLearn.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewLearn: View {
    @State private var selectedPage: NavBarPage = .learn
    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Image(systemName: "graduationcap")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                Text("Start LEarning!")
                Spacer()
            }
            .padding()
            //NavBar(selectedPage: $selectedPage)
        }

    }
}

#Preview {
    ViewLearn()
}
