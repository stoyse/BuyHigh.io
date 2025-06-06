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
        Task {
            await fetchUserDataAsync()
        }
    }
    
    @MainActor
    private func fetchUserDataAsync() async {
        guard let userId = authManager.userId else {
            self.errorMessage = "User ID not available. Please log in."
            return
        }
        
        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            self.errorMessage = "Authentication failed. Please log in again."
            return
        }
        
        guard let url = URL(string: "https://api.stoyse.hackclub.app/user/\(userId)") else {
            self.errorMessage = "Invalid URL"
            return
        }
        
        print("UserLoader: Using fresh token for userID: \(userId)")

        isLoading = true
        errorMessage = nil
        userData = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30.0

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                self.errorMessage = "Invalid response from server."
                self.isLoading = false
                return
            }
            
            print("UserLoader: HTTP Status Code: \(httpResponse.statusCode)")
            
            // Log raw response for debugging
            if let rawString = String(data: data, encoding: .utf8) {
                print("Raw UserData Response: \(rawString)")
            }

            switch httpResponse.statusCode {
            case 200...299:
                do {
                    let decodedResponse = try JSONDecoder().decode(UserDataApiResponse.self, from: data)
                    if decodedResponse.success {
                        self.userData = decodedResponse.user
                        if self.userData == nil {
                            self.errorMessage = "User data not found in response, though success was true."
                        }
                    } else {
                        self.errorMessage = "Failed to fetch user data. Server indicated failure."
                    }
                } catch {
                    self.errorMessage = "Failed to decode user data: \(error.localizedDescription)"
                }
            case 401:
                self.errorMessage = "Authentication expired. Please log in again."
                authManager.logout()
            case 404:
                self.errorMessage = "User not found."
            case 500...599:
                self.errorMessage = "Server error. Please try again later."                default:
                    self.errorMessage = "Server error: \(httpResponse.statusCode)."
            }
            
        } catch {
            print("UserLoader: Network error: \(error.localizedDescription)")
            if error.localizedDescription.contains("timeout") {
                self.errorMessage = "Request timeout. Please check your connection."
            } else {
                self.errorMessage = "Network error: \(error.localizedDescription)"
            }
        }
        
        self.isLoading = false
    }
}


