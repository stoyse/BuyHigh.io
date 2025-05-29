//
//  LoadUser.swift
//  BuyHigh
//
//  Created by Julian Stosse on 29.05.25.
//

import Foundation
import SwiftUI

// Define the structure for the user data based on the API response
struct UserData: Codable {
    let id: Int
    let username: String?
    let email: String
    let firebase_uid: String?
    // Add other fields that are part of the 'user' object in UserDataResponse
    // For example:
    // let balance: Double?
    // let profile_pic_url: String?
    // let level: Int?
    // let xp: Int?
    // let total_profit: Double?
    // let total_trades: Int?
}

struct UserDataApiResponse: Codable {
    let success: Bool
    let user: UserData? // Make sure UserData matches the structure from your backend
}

class UserLoader: ObservableObject {
    @Published var userData: UserData?
    @Published var errorMessage: String?
    @Published var isLoading: Bool = false

    private var authManager: AuthManager

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    func fetchUserData() {
        guard let userId = authManager.userId, let token = authManager.idToken else {
            self.errorMessage = "User ID or Token not available. Please log in."
            return
        }

        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/\\(userId)") else {
            self.errorMessage = "Invalid URL"
            return
        }

        self.isLoading = true
        self.errorMessage = nil
        self.userData = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \\(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                if let error = error {
                    self.errorMessage = "Network error: \\(error.localizedDescription)"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse else {
                    self.errorMessage = "Invalid response from server."
                    return
                }
                
                // Log raw response for debugging
                if let data = data, let rawResponseString = String(data: data, encoding: .utf8) {
                    print("Raw UserData Response: \\(rawResponseString)")
                }


                guard (200...299).contains(httpResponse.statusCode) else {
                    var detailMessage = "Server error: \\(httpResponse.statusCode)."
                    if let data = data, let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data), let detail = errorResponse.detail {
                         detailMessage += " Details: \\(detail)"
                    } else if let data = data, let responseString = String(data: data, encoding: .utf8) {
                        detailMessage += " Response: \\(responseString)"
                    }
                    self.errorMessage = detailMessage
                    return
                }

                guard let data = data else {
                    self.errorMessage = "No data received from server."
                    return
                }

                do {
                    let decodedResponse = try JSONDecoder().decode(UserDataApiResponse.self, from: data)
                    if decodedResponse.success {
                        self.userData = decodedResponse.user
                        if self.userData == nil {
                             self.errorMessage = "User data not found in response, though success was true."
                        }
                    } else {
                        self.errorMessage = "Failed to fetch user data. Server indicated failure."
                         // Potentially use a message from the response if available
                    }
                } catch {
                    let rawDataForErrorMessage = String(data: data, encoding: .utf8) ?? "Raw data not convertible to String"
                    self.errorMessage = "Failed to decode user data: \\(error.localizedDescription). Raw data: \\(rawDataForErrorMessage)"
                }
            }
        }.resume()
    }
}

// Helper struct for decoding error responses if your API sends structured errors
struct ErrorResponse: Codable {
    let detail: String?
}


