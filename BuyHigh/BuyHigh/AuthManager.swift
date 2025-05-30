import SwiftUI
import Combine
import FirebaseAuth // Import FirebaseAuth - Ensure this is correctly linked in your project

class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool = UserDefaults.standard.bool(forKey: "isLoggedIn") {
        didSet {
            UserDefaults.standard.set(isLoggedIn, forKey: "isLoggedIn")
            print("AuthManager: isLoggedIn didSet to \\(isLoggedIn)")
        }
    }
    @Published var isGuest: Bool = UserDefaults.standard.bool(forKey: "isGuest") {
        didSet {
            UserDefaults.standard.set(isGuest, forKey: "isGuest")
            print("AuthManager: isGuest didSet to \\(isGuest)")
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
            print("AuthManager: userId didSet to \\(String(describing: userId))")
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

    func logout() {
        print("AuthManager: logout() called")
        // Firebase Auth ausloggen, falls ein User angemeldet war (auch anonym)
        do {
            try Auth.auth().signOut()
            print("AuthManager: Successfully signed out from Firebase Auth.")
        } catch let signOutError as NSError {
            print("AuthManager: Error signing out from Firebase Auth: \\(signOutError.localizedDescription)")
            // Hier könntest du dem User eine Fehlermeldung anzeigen, falls das Ausloggen bei Firebase fehlschlägt,
            // aber für den lokalen Zustand fahren wir trotzdem fort.
        }

        // Lokalen Zustand und UserDefaults zurücksetzen
        // Wichtig: UI-Updates (durch @Published Änderungen) sollten auf dem Main-Thread erfolgen.
        // Die Zuweisungen hier lösen die didSet-Observer aus, die bereits auf dem Main-Thread laufen sollten,
        // da AuthManager ein ObservableObject ist und Änderungen von Views auf dem Main-Thread konsumiert werden.
        // Ein explizites DispatchQueue.main.async ist hier meist nicht nötig, schadet aber auch nicht für die reine Zustandsänderung.
        
        self.isLoggedIn = false
        self.isGuest = false
        self.idToken = nil
        self.userId = nil
        self.firebaseUid = nil
        self.errorMessage = nil // Fehlermeldungen beim Logout löschen

        // Obwohl die didSet-Observer die UserDefaults aktualisieren sollten,
        // ist ein explizites Entfernen hier eine zusätzliche Sicherheitsebene,
        // besonders wenn die didSet-Logik komplexer wird oder Fehler enthält.
        // UserDefaults.standard.removeObject(forKey: "isLoggedIn") // Wird durch isLoggedIn.didSet erledigt
        // UserDefaults.standard.removeObject(forKey: "isGuest")    // Wird durch isGuest.didSet erledigt
        // UserDefaults.standard.removeObject(forKey: "idToken")   // Wird durch idToken.didSet erledigt
        // UserDefaults.standard.removeObject(forKey: "userId")    // Wird durch userId.didSet erledigt
        // UserDefaults.standard.removeObject(forKey: "firebaseUid")// Wird durch firebaseUid.didSet erledigt
        
        // Ein synchronize() ist in modernen iOS-Versionen normalerweise nicht mehr nötig,
        // da UserDefaults Änderungen periodisch und bei wichtigen App-Lebenszyklusereignissen speichert.
        // UserDefaults.standard.synchronize() 
        
        print("AuthManager: All local state cleared for logout. isLoggedIn=\\(self.isLoggedIn), isGuest=\\(self.isGuest)")
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
