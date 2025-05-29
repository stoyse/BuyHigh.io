import SwiftUI
import Combine

class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool = UserDefaults.standard.bool(forKey: "isLoggedIn") {
        didSet {
            UserDefaults.standard.set(isLoggedIn, forKey: "isLoggedIn")
        }
    }
    @Published var idToken: String? = UserDefaults.standard.string(forKey: "idToken") {
        didSet {
            UserDefaults.standard.set(idToken, forKey: "idToken")
        }
    }
    @Published var userId: Int? = UserDefaults.standard.object(forKey: "userId") as? Int { // Changed from as? Int? to as? Int
        didSet {
            if let userId = userId {
                UserDefaults.standard.set(userId, forKey: "userId")
            } else {
                UserDefaults.standard.removeObject(forKey: "userId")
            }
        }
    }
    @Published var firebaseUid: String? = UserDefaults.standard.string(forKey: "firebaseUid") {
        didSet {
            UserDefaults.standard.set(firebaseUid, forKey: "firebaseUid")
        }
    }
    @Published var errorMessage: String?

    private var cancellables = Set<AnyCancellable>()

    // Replace with your actual API endpoint
    private let loginURL = URL(string: "https://api.stoyse.hackclub.app/auth/login")! // Removed trailing slash

    init() { // Added init
        // Load initial value for userId from UserDefaults
        self.userId = UserDefaults.standard.object(forKey: "userId") as? Int
        // didSet for userId will handle saving future changes
    }

    func login(email: String, password: String) {
        let loginRequest = LoginRequest(email: email, password: password)

        guard let encoded = try? JSONEncoder().encode(loginRequest) else {
            self.errorMessage = "Failed to encode login request."
            return
        }

        var request = URLRequest(url: loginURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = encoded

        URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { output -> Data in // Explicitly type output to Data
                let httpResponse = output.response as? HTTPURLResponse
                // Log raw response string regardless of status code for debugging
                if let responseString = String(data: output.data, encoding: .utf8) {
                    print("AuthManager - Raw server response [Status: \(httpResponse?.statusCode ?? 0)]:\n\(responseString)")
                }

                guard let validResponse = httpResponse, validResponse.statusCode == 200 else {
                    // Try to decode error message from backend for non-200 responses
                    if let errorData = try? JSONDecoder().decode(LoginErrorResponse.self, from: output.data) {
                         throw LoginError.custom(message: errorData.detail)
                    }
                    // If decoding LoginErrorResponse fails, or for other non-200 errors
                    throw LoginError.invalidResponse
                }
                return output.data
            }
            .decode(type: LoginResponse.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { [weak self] completion in
                switch completion {
                case .failure(let error):
                    print("AuthManager - Login pipeline error: \(error)") // More detailed error logging
                    if let loginError = error as? LoginError {
                        switch loginError {
                        case .custom(let message):
                            self?.errorMessage = message
                        default:
                            self?.errorMessage = "Login failed: \(error.localizedDescription)"
                        }
                    } else {
                         self?.errorMessage = "Login failed: \(error.localizedDescription)"
                    }
                    self?.isLoggedIn = false
                case .finished:
                    self?.errorMessage = nil
                }
            }, receiveValue: { [weak self] response in
                if response.success {
                    self?.isLoggedIn = true
                    self?.idToken = response.id_token
                    self?.userId = response.userId // Should now work correctly
                    self?.firebaseUid = response.firebase_uid
                    self?.errorMessage = nil
                } else {
                    self?.errorMessage = response.message ?? "Login failed. Please try again."
                    self?.isLoggedIn = false
                }
            })
            .store(in: &cancellables)
    }

    func logout() {
        // Add API call to backend logout if necessary
        // For now, just clear local state
        self.isLoggedIn = false
        self.idToken = nil
        self.userId = nil // Should now work correctly
        self.firebaseUid = nil
    }
}

// Helper structs for encoding and decoding
struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct LoginResponse: Codable {
    let success: Bool
    let message: String?
    let userId: Int? // Changed from String? to Int?
    let firebase_uid: String?
    let id_token: String?
}

struct LoginErrorResponse: Codable {
    let detail: String
}

enum LoginError: Error {
    case invalidResponse
    case custom(message: String)
}
