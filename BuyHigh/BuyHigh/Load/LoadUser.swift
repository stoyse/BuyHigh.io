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
    // Added fields based on the server response
    let balance: Double?
    let created_at: String? // Consider decoding to Date if needed
    let last_login: String? // Consider decoding to Date if needed
    let mood_pet: String?
    let pet_energy: Int?
    let is_meme_mode: Bool?
    let email_verified: Bool?
    let theme: String?
    let total_trades: Int?
    let profit_loss: Double? // In your response it's 0.0, ensure type matches if it can be other numbers
    let xp: Int?
    let level: Int?
    // password_hash is intentionally omitted as it's likely not needed in the frontend
    // firebase_provider is also omitted for now, add if needed
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
        // Debug: Print the userId
        print("UserLoader: Attempting to fetch data for userId: \(userId)")

        // Corrected URL interpolation
        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/\(userId)") else {
            self.errorMessage = "Invalid URL"
            return
        }
        // Debug: Print the constructed URL
        print("UserLoader: Constructed URL: \(url.absoluteString)")

        self.isLoading = true
        self.errorMessage = nil
        self.userData = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                // Original: if let error = error {
                // self.errorMessage = "Network error: \\(error.localizedDescription)"
                // return
                // }
                // Adressiert Warnung für Zeile 66
                if error != nil {
                    self.errorMessage = "Network error: \(error!.localizedDescription)"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse else {
                    self.errorMessage = "Invalid response from server."
                    return
                }
                // Debug: Print HTTP status code
                print("UserLoader: HTTP Status Code: \(httpResponse.statusCode)")
                
                // Log raw response for debugging
                // Original: if let data = data, let rawResponseString = String(data: data, encoding: .utf8) {
                // print("Raw UserData Response: \\(rawResponseString)")
                // }
                // Adressiert Warnung für Zeile 77
                if let data = data {
                    if let rawString = String(data: data, encoding: .utf8) {
                        print("Raw UserData Response: \(rawString)") // Korrigierte Interpolation
                    }
                }


                guard (200...299).contains(httpResponse.statusCode) else {
                    var detailMessage = "Server error: \(httpResponse.statusCode)."
                    // Original: if let data = data, let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data), let detail = errorResponse.detail {
                    //      detailMessage += " Details: \\(detail)"
                    // }
                    // Adressiert Warnung für Zeile 84
                    if let data = data, let errorResponse = try? JSONDecoder().decode(ErrorResponse.self, from: data) {
                        if let detailValue = errorResponse.detail { // Used detailValue directly
                             detailMessage += " Details: \(detailValue)"
                        }
                    // Original: } else if let data = data, let responseString = String(data: data, encoding: .utf8) {
                    //     detailMessage += " Response: \\(responseString)"
                    // }
                    // Adressiert Warnung für Zeile 86
                    } else if let data = data {
                        if let str = String(data: data, encoding: .utf8) { // Used str directly
                            detailMessage += " Response: \(str)"
                        }
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
                    // Original: let rawDataForErrorMessage = String(data: data, encoding: .utf8) ?? "Raw data not convertible to String"
                    // self.errorMessage = "Failed to decode user data: \\\\(error.localizedDescription). Raw data: \\\\(rawDataForErrorMessage)"
                    // Adressiert Warnung für Zeile 110 und korrigiert Syntaxfehler
                    self.errorMessage = "Failed to decode user data: \(error.localizedDescription). Raw data: \(String(data: data, encoding: .utf8) ?? "Raw data not convertible to String")"
                }
            }
        }.resume()
    }
}

// Helper struct for decoding error responses if your API sends structured errors
struct ErrorResponse: Codable {
    let detail: String?
}


