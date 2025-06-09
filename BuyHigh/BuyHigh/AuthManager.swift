import SwiftUI
import Combine
import FirebaseAuth // Import FirebaseAuth - Ensure this is correctly linked in your project

class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool = false {
        didSet {
            UserDefaults.standard.set(isLoggedIn, forKey: "isLoggedIn")
            print("AuthManager: isLoggedIn didSet to \(isLoggedIn)")
        }
    }
    @Published var isGuest: Bool = false {
        didSet {
            UserDefaults.standard.set(isGuest, forKey: "isGuest")
            print("AuthManager: isGuest didSet to \(isGuest)")
        }
    }
    @Published var idToken: String? = nil {
        didSet {
            if let idToken = idToken {
                UserDefaults.standard.set(idToken, forKey: "idToken")
            } else {
                UserDefaults.standard.removeObject(forKey: "idToken")
            }
            print("AuthManager: idToken didSet")
        }
    }
    @Published var userId: Int? = nil {
        didSet {
            if let userId = userId {
                UserDefaults.standard.set(userId, forKey: "userId")
            } else {
                UserDefaults.standard.removeObject(forKey: "userId")
            }
            print("AuthManager: userId didSet to \(String(describing: userId))")
        }
    }
    @Published var firebaseUid: String? = nil {
        didSet {
            if let firebaseUid = firebaseUid {
                UserDefaults.standard.set(firebaseUid, forKey: "firebaseUid")
            } else {
                UserDefaults.standard.removeObject(forKey: "firebaseUid")
            }
            print("AuthManager: firebaseUid didSet")
        }
    }
    @Published var errorMessage: String?

    private var cancellables = Set<AnyCancellable>()
    private var authStateHandler: AuthStateDidChangeListenerHandle?

    // Replace with your actual API endpoint
    private let loginURL = URL(string: "https://api.stoyse.hackclub.app/auth/login")!
    private let guestLoginURL = URL(string: "https://api.stoyse.hackclub.app/auth/firebase-anonymous-login")! // Corrected guest login URL

    init() {
        // Werte werden durch @Published Initialisierer geladen.
        print("AuthManager init: isLoggedIn = \(isLoggedIn), isGuest = \(isGuest), userId = \(String(describing: userId)), idToken isNil = \(idToken == nil), firebaseUid isNil = \(firebaseUid == nil)")
        addAuthStateListener()
    }

    deinit {
        removeAuthStateListener()
    }

    private func addAuthStateListener() {
        authStateHandler = Auth.auth().addStateDidChangeListener { [weak self] (auth, user) in
            guard let self = self else { return }
            print("AuthManager: AuthStateDidChange - User: \(user?.uid ?? "nil"), current app isLoggedIn: \(self.isLoggedIn)")

            if let fbUser = user { // Firebase user is present
                self.firebaseUid = fbUser.uid // Keep firebaseUid in sync

                Task { // Perform async operations in a Task
                    print("AuthManager: AuthStateDidChange: Firebase user \(fbUser.uid) detected. Attempting to get/refresh Firebase token.")
                    if let firebaseToken = await self.getFirebaseToken(user: fbUser) {
                        await MainActor.run {
                            self.idToken = firebaseToken // Store/update Firebase token
                            
                            // Check if we have stored login state and restore it
                            let storedIsLoggedIn = UserDefaults.standard.bool(forKey: "isLoggedIn")
                            let storedIsGuest = UserDefaults.standard.bool(forKey: "isGuest")
                            let storedUserId = UserDefaults.standard.object(forKey: "userId") as? Int
                            
                            if storedIsLoggedIn && storedUserId != nil {
                                // Restore previous session
                                self.isLoggedIn = true
                                self.isGuest = storedIsGuest
                                self.userId = storedUserId
                                print("AuthManager: Restored previous session - UserId: \(storedUserId ?? -1), isGuest: \(storedIsGuest)")
                            } else {
                                print("AuthManager: Firebase user exists but no valid stored session found.")
                            }
                        }
                    } else {
                        print("AuthManager: AuthStateDidChange: Failed to get/refresh Firebase token for user \(fbUser.uid). Logging out.")
                        DispatchQueue.main.async { self.logout() } // Logout if we can't get a token
                    }
                }
            } else { // Firebase user is nil
                print("AuthManager: AuthStateDidChange: Firebase user is nil.")
                if self.isLoggedIn {
                    print("AuthManager: AuthStateDidChange: Firebase user is nil, but app thought we were logged in. Logging out.")
                    DispatchQueue.main.async {
                        self.logout()
                    }
                } else {
                    // Consistent state: Firebase user is nil, and app isLoggedIn is false.
                    // Clear any potentially stale local tokens/UIDs.
                    self.idToken = nil
                    self.firebaseUid = nil
                }
            }
        }
    }

    private func removeAuthStateListener() {
        if let handle = authStateHandler {
            Auth.auth().removeStateDidChangeListener(handle)
        }
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
                DispatchQueue.main.async {
                    self.isLoggedIn = false
                    self.isGuest = false
                }
                print("Firebase Anonymous Sign-In Error: \(error.localizedDescription)")
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

            // Successfully signed in with Firebase. The AuthStateChangeListener will also pick this up.
            // Get the token to send to your backend.
            user.getIDTokenResult(forcingRefresh: true) { [weak self] idTokenResult, tokenFetchingError in
                guard let self = self else { return }

                if let actualError = tokenFetchingError {
                    self.errorMessage = "Error fetching Firebase ID Token: \(actualError.localizedDescription)"
                    DispatchQueue.main.async {
                        // self.isLoggedIn = false; self.isGuest = false; // Let AuthStateChangeListener handle logout on token failure
                        print("AuthManager: Error fetching Firebase ID Token for backend call: \(actualError.localizedDescription). Logging out.")
                        self.logout() // If we can't get a token to send to backend, abort login.
                    }
                    return
                }

                guard let firebaseIdToken = idTokenResult?.token else {
                    self.errorMessage = "Could not get Firebase ID Token for backend call."
                    DispatchQueue.main.async {
                        print("AuthManager: Could not get Firebase ID Token for backend call. Logging out.")
                        self.logout() // If we can't get a token, abort.
                    }
                    return
                }

                // Explicitly set token and UID here before backend call,
                // though AuthStateChangeListener should also set them.
                self.idToken = firebaseIdToken
                self.firebaseUid = user.uid

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
                guard let self = self else { return }
                if response.success {
                    // Backend login successful.
                    // self.idToken should already be the Firebase token.
                    // self.firebaseUid should also be set.
                    self.isLoggedIn = true
                    self.isGuest = response.isGuest
                    self.userId = response.userId
                    self.errorMessage = nil
                    print("AuthManager (Guest) - Backend login successful. UserID: \(response.userId ?? -1), FirebaseUID from AuthManager: \(self.firebaseUid ?? "N/A")")
                } else {
                    self.errorMessage = response.message ?? "Guest login failed. Please try again."
                    self.isLoggedIn = false // Ensure this is set on failure
                    self.isGuest = false
                }
            })
            .store(in: &cancellables)
    }

    // New helper function to get Firebase token
    private func getFirebaseToken(user: FirebaseAuth.User) async -> String? {
        return await withCheckedContinuation { continuation in
            user.getIDTokenForcingRefresh(true) { token, error in
                if let error = error {
                    print("AuthManager: Error refreshing Firebase token for user \(user.uid): \(error.localizedDescription)")
                    continuation.resume(returning: nil)
                } else if let token = token {
                    print("AuthManager: Firebase token obtained/refreshed successfully for user \(user.uid)")
                    continuation.resume(returning: token)
                } else {
                    print("AuthManager: No token received for user \(user.uid)")
                    continuation.resume(returning: nil)
                }
            }
        }
    }
    
    func getValidToken() async -> String? {
        guard let currentUser = Auth.auth().currentUser else {
            print("AuthManager: getValidToken: No current Firebase user. Current app isLoggedIn state: \(self.isLoggedIn)")
            // If isLoggedIn is true here, AuthStateChangeListener should eventually correct it by calling logout.
            return nil
        }
        // currentUser exists, try to get/refresh its token.
        // This will also update self.idToken via the AuthStateChangeListener if successful.
        return await getFirebaseToken(user: currentUser)
    }
    
    // Removing isTokenExpired and refreshTokenAndUpdateState as their logic is covered
    // by getValidToken and the AuthStateDidChangeListener.

    func logout() {
        print("AuthManager: logout() called")
        do {
            try Auth.auth().signOut()
            print("AuthManager: Successfully signed out from Firebase Auth.")
        } catch let signOutError as NSError {
            print("AuthManager: Error signing out from Firebase Auth: \(signOutError.localizedDescription)")
        }

        // Reset local authentication state
        self.isLoggedIn = false
        self.isGuest = false
        self.idToken = nil
        self.userId = nil
        self.firebaseUid = nil
        self.errorMessage = nil
        
        print("AuthManager: All local state cleared for logout. isLoggedIn=\(self.isLoggedIn), isGuest=\(self.isGuest)")
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
