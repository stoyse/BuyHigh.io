//
//  ViewProfile.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import SwiftUI

struct ViewProfile: View {
    @State private var selectedPage: NavBarPage = .profile

    var body: some View {
        VStack(spacing: 0) {
            VStack {
                Image(systemName: "person.crop.circle")
                    .imageScale(.large)
                    .foregroundStyle(.tint)
                Text("Hello, User!")
                Spacer()
            }
            .padding()
            //NavBar(selectedPage: $selectedPage)
        }
        // Optional: Navigation zu anderen Seiten
        .onChange(of: selectedPage) { newPage in
            // Hier könntest du ggf. Navigation auslösen, falls ViewProfile nur für Profil gedacht ist
        }
    }
}

#Preview {
    ViewProfile()
}
