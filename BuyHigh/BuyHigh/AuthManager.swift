import SwiftUI
import Combine
import FirebaseAuth // Import FirebaseAuth - Ensure this is correctly linked in your project

class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool = UserDefaults.standard.bool(forKey: "isLoggedIn") {
        didSet {
            UserDefaults.standard.set(isLoggedIn, forKey: "isLoggedIn")
            print("AuthManager: isLoggedIn didSet to \(isLoggedIn)")
        }
    }
    @Published var isGuest: Bool = UserDefaults.standard.bool(forKey: "isGuest") {
        didSet {
            UserDefaults.standard.set(isGuest, forKey: "isGuest")
            print("AuthManager: isGuest didSet to \(isGuest)")
        }
    }
    @Published var idToken: String? = UserDefaults.standard.string(forKey: "idToken") {
        didSet {
            UserDefaults.standard.set(idToken, forKey: "idToken")
            print("AuthManager: idToken didSet")
        }
    }
    @Published var userId: Int? = UserDefaults.standard.object(forKey: "userId") as? Int {
        didSet {
            if let userId = userId {
                UserDefaults.standard.set(userId, forKey: "userId")
            } else {
                UserDefaults.standard.removeObject(forKey: "userId")
            }
            print("AuthManager: userId didSet to \(String(describing: userId))")
        }
    }
    @Published var firebaseUid: String? = UserDefaults.standard.string(forKey: "firebaseUid") {
        didSet {
            UserDefaults.standard.set(firebaseUid, forKey: "firebaseUid")
            print("AuthManager: firebaseUid didSet")
        }
    }
    @Published var errorMessage: String?

    private var cancellables = Set<AnyCancellable>()

    // Replace with your actual API endpoint
    private let loginURL = URL(string: "https://api.stoyse.hackclub.app/auth/login")!
    private let guestLoginURL = URL(string: "https://api.stoyse.hackclub.app/auth/firebase-anonymous-login")! // Corrected guest login URL

    init() {
        // Werte werden durch @Published Initialisierer geladen.
        // Hinzufügen von print-Anweisungen, um den initialen Zustand zu überprüfen.
        print("AuthManager init: isLoggedIn = \\(isLoggedIn), isGuest = \\(isGuest), userId = \\(String(describing: userId)), idToken isNil = \\(idToken == nil), firebaseUid isNil = \\(firebaseUid == nil)")
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

    func signInAnonymouslyWithFirebase() {
        Auth.auth().signInAnonymously { [weak self] authResult, error in
            guard let self = self else { return }

            if let error = error {
                self.errorMessage = "Firebase Anonymous Sign-In Error: \(error.localizedDescription)"
                // Ensure UI updates on the main thread
                DispatchQueue.main.async {
                    self.isLoggedIn = false
                    self.isGuest = false
                }
                print("Firebase Anonymous Sign-In Error: \(error)")
                return
            }

            guard let user = authResult?.user else {
                self.errorMessage = "Firebase Anonymous Sign-In Error: No user data."
                DispatchQueue.main.async {
                    self.isLoggedIn = false
                    self.isGuest = false
                }
                print("Firebase Anonymous Sign-In Error: No user data.")
                return
            }

            user.getIDTokenResult(forcingRefresh: true) { idTokenResult, error in
                if let error = error {
                    self.errorMessage = "Error fetching Firebase ID Token: \(error.localizedDescription)"
                    DispatchQueue.main.async {
                        self.isLoggedIn = false
                        self.isGuest = false
                    }
                    print("Error fetching Firebase ID Token: \(error)")
                    return
                }

                guard let firebaseIdToken = idTokenResult?.token else {
                    self.errorMessage = "Could not get Firebase ID Token."
                    DispatchQueue.main.async {
                        self.isLoggedIn = false
                        self.isGuest = false
                    }
                    print("Could not get Firebase ID Token.")
                    return
                }

                // Now call your backend with this token
                self.callBackendForAnonymousLogin(firebaseIdToken: firebaseIdToken)
            }
        }
    }

    private func callBackendForAnonymousLogin(firebaseIdToken: String) {
        let requestData = FirebaseAnonymousLoginRequest(id_token: firebaseIdToken)

        guard let encoded = try? JSONEncoder().encode(requestData) else {
            self.errorMessage = "Failed to encode anonymous login request."
            DispatchQueue.main.async {
                self.isLoggedIn = false
                self.isGuest = false
            }
            return
        }

        var request = URLRequest(url: guestLoginURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = encoded

        URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { output -> Data in
                let httpResponse = output.response as? HTTPURLResponse
                if let responseString = String(data: output.data, encoding: .utf8) {
                    print("AuthManager (Guest) - Raw server response [Status: \(httpResponse?.statusCode ?? 0)]:\n\(responseString)")
                }
                guard let validResponse = httpResponse, validResponse.statusCode == 200 else {
                    if let errorData = try? JSONDecoder().decode(LoginErrorResponse.self, from: output.data) {
                         throw LoginError.custom(message: errorData.detail)
                    }
                    throw LoginError.invalidResponse
                }
                return output.data
            }
            .decode(type: FirebaseAnonymousLoginResponse.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { [weak self] completion in
                switch completion {
                case .failure(let error):
                    print("AuthManager (Guest) - Login pipeline error: \(error)")
                    if let loginError = error as? LoginError {
                        switch loginError {
                        case .custom(let message):
                            self?.errorMessage = message
                        default:
                            self?.errorMessage = "Guest login failed: \(error.localizedDescription)"
                        }
                    } else {
                         self?.errorMessage = "Guest login failed: \(error.localizedDescription)"
                    }
                    self?.isLoggedIn = false
                    self?.isGuest = false
                case .finished:
                    // Error message is handled in receiveValue based on response.success
                    break
                }
            }, receiveValue: { [weak self] response in
                if response.success {
                    self?.isLoggedIn = true
                    self?.isGuest = response.isGuest 
                    self?.idToken = response.id_token // Store the backend-provided token
                    self?.userId = response.userId
                    self?.firebaseUid = response.firebase_uid
                    self?.errorMessage = nil
                    // Corrected print statement by properly escaping the inner quote
                    print("AuthManager (Guest) - Successfully logged in as guest. UserID: \(response.userId ?? -1), FirebaseUID: \(response.firebase_uid ?? "N/A")")
                } else {
                    self?.errorMessage = response.message ?? "Guest login failed. Please try again."
                    self?.isLoggedIn = false
                    self?.isGuest = false
                }
            })
            .store(in: &cancellables)
    }

    //  Token Refresh Functions
    
    func getValidToken() async -> String? {
        guard let currentUser = Auth.auth().currentUser else {
            print("AuthManager: No current Firebase user")
            await MainActor.run {
                self.logout()
            }
            return nil
        }
        
        do {
            // Use completion handler version for compatibility
            return try await withCheckedThrowingContinuation { continuation in
                currentUser.getIDTokenForcingRefresh(true) { token, error in
                    if let error = error {
                        continuation.resume(throwing: error)
                    } else if let token = token {
                        Task { @MainActor in
                            self.idToken = token
                            print("AuthManager: Token refreshed successfully")
                        }
                        continuation.resume(returning: token)
                    } else {
                        continuation.resume(throwing: NSError(domain: "AuthManager", code: -1, userInfo: [NSLocalizedDescriptionKey: "No token received"]))
                    }
                }
            }
        } catch {
            print("AuthManager: Error refreshing token: \(error.localizedDescription)")
            await MainActor.run {
                self.logout()
            }
            return nil
        }
    }
    
    /// Check if current token is expired (simplified check)
    func isTokenExpired() -> Bool {
        guard let token = idToken else { return true }
        
        // Simple check: if we have a Firebase user and token, assume it's valid
        // Firebase handles token expiration internally
        return Auth.auth().currentUser == nil
    }
    
    /// Refresh token and update state
    func refreshTokenAndUpdateState() {
        guard let currentUser = Auth.auth().currentUser else {
            print("AuthManager: No current user found")
            logout()
            return
        }
        
        // Force refresh the token to get a new one with extended expiry
        currentUser.getIDTokenForcingRefresh(true) { [weak self] token, error in
            DispatchQueue.main.async {
                if let error = error {
                    print("AuthManager: Error refreshing token: \(error.localizedDescription)")
                    self?.logout()
                    return
                }
                
                guard let token = token else {
                    print("AuthManager: No token received")
                    self?.logout()
                    return
                }
                
                print("AuthManager: Token refreshed successfully")
                self?.idToken = token
            }
        }
    }

    func logout() {
        print("AuthManager: logout() called")
        // Firebase Auth ausloggen, falls ein User angemeldet war (auch anonym)
        do {
            try Auth.auth().signOut()
            print("AuthManager: Successfully signed out from Firebase Auth.")
        } catch let error as NSError {
            print("AuthManager: Error signing out from Firebase Auth: \\(error.localizedDescription)")
        }

        
        self.isLoggedIn = false
        self.isGuest = false
        self.idToken = nil
        self.userId = nil
        self.firebaseUid = nil
        self.errorMessage = nil
        
        print("AuthManager: All local state cleared for logout. isLoggedIn=\(self.isLoggedIn), isGuest=\\(self.isGuest)")
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

// Added structs for Firebase Anonymous Login
struct FirebaseAnonymousLoginRequest: Codable {
    let id_token: String
}

struct FirebaseAnonymousLoginResponse: Codable {
    let success: Bool
    let message: String?
    let userId: Int?
    let firebase_uid: String?
    let email: String? // email might be returned by backend
    let username: String? // username might be returned by backend
    let id_token: String? // Backend might return its own session token or echo Firebase's
    let isGuest: Bool
}

struct LoginErrorResponse: Codable {
    let detail: String
}

enum LoginError: Error {
    case invalidResponse
    case custom(message: String)
}
