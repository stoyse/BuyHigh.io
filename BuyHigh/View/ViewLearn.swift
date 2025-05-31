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
            ScrollView {
                VStack {
                    Image(systemName: "graduationcap")
                        .imageScale(.large)
                        .foregroundStyle(.tint)
                    Text("Start Learning!")
                        .font(.title)
                        .padding(.bottom)
                    
                    // Add the CardDailyQuiz here
                    CardDailyQuiz()
                        .padding(.horizontal) // Add some horizontal padding to the card

                    Spacer() // Pushes content to the top
                }
                .padding() // Add padding around the content VStack
            }
            //NavBar(selectedPage: $selectedPage)
        }
        .navigationTitle("Learn") // Optional: Add a navigation title
    }
}

#Preview {
    ViewLearn()
}
