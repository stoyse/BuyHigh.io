//
//  CardDailyQuiz.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import SwiftUI

struct CardDailyQuiz: View {
    @EnvironmentObject var authManager: AuthManager
    @State private var dailyQuiz: DailyQuiz?
    @State private var isLoading = true // Start with loading true
    @State private var errorMessage: String?
    @State private var selectedAnswer: String?
    @State private var isSubmitting: Bool = false
    @State private var attemptResult: DailyQuizAttemptResponse?
    @State private var hasAttemptedToday: Bool = false

    private var possibleAnswers: [String] {
        guard let quiz = dailyQuiz else { return [] }
        return [quiz.possibleAnswer1, quiz.possibleAnswer2, quiz.possibleAnswer3]
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Daily Quiz")
                .font(.title2)
                .fontWeight(.bold)
                .padding(.bottom, 5)

            if isLoading {
                ProgressView("Loading Quiz...")
                    .frame(maxWidth: .infinity, alignment: .center)
            } else if let errorMessage = errorMessage {
                VStack {
                    Text("Error: \(errorMessage)")
                        .foregroundColor(.red)
                    Button("Retry") {
                        Task {
                            await loadInitialData()
                        }
                    }
                    .padding(.top)
                }
            } else if let quiz = dailyQuiz {
                VStack(alignment: .leading, spacing: 10) {
                    Text(quiz.question)
                        .font(.headline)
                        .fixedSize(horizontal: false, vertical: true) // Allow text to wrap

                    ForEach(possibleAnswers, id: \.self) { answer in
                        Button(action: {
                            if !hasAttemptedToday {
                                self.selectedAnswer = answer
                                Task {
                                    await handleSubmitAnswer(quizId: quiz.id, answer: answer)
                                }
                            }
                        }) {
                            HStack {
                                Text(answer)
                                    .foregroundColor(determineButtonForegroundColor(for: answer))
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(.vertical, 8)
                                    .padding(.horizontal, 12)
                                if hasAttemptedToday && attemptResult?.selectedAnswer == answer {
                                    if attemptResult?.isCorrect == true {
                                        Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                                    } else {
                                        Image(systemName: "xmark.circle.fill").foregroundColor(.red)
                                    }
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .background(determineButtonBackgroundColor(for: answer))
                            .cornerRadius(8)
                        }
                        .disabled(isSubmitting || hasAttemptedToday)
                    }

                    if isSubmitting {
                        ProgressView("Submitting...")
                            .padding(.top)
                    }

                    if hasAttemptedToday, let result = attemptResult {
                        VStack(alignment: .leading, spacing: 5) {
                            Text(result.isCorrect ? "Correct!" : "Incorrect")
                                .font(.headline)
                                .foregroundColor(result.isCorrect ? .green : .red)
                            if !result.isCorrect {
                                Text("Correct Answer: \(result.correctAnswer)")
                            }
                            if let explanation = result.explanation, !explanation.isEmpty {
                                Text("Explanation: \(explanation)")
                                    .font(.caption)
                            }
                            if let xp = result.xpGained, xp > 0 {
                                Text("XP Gained: \(xp)")
                                    .font(.caption)
                                    .foregroundColor(.blue)
                            }
                            if let message = result.message, result.message != "Attempt recorded successfully." && result.message != "Quiz already attempted today." {
                                Text(message)
                                    .font(.caption)
                                    .foregroundColor(.orange)
                            }
                        }
                        .padding(.top)
                    }
                }
            } else {
                Text("No quiz data available for today.")
                    .frame(maxWidth: .infinity, alignment: .center)
            }
        }
        .padding()
        .background(Color(UIColor.systemGray6)) // Explicitly use UIColor for systemGray6
        .cornerRadius(10)
        .shadow(radius: 3)
        .task {
            await loadInitialData()
        }
    }

    func loadInitialData() async {
        isLoading = true
        errorMessage = nil
        attemptResult = nil
        hasAttemptedToday = false
        selectedAnswer = nil
        
        do {
            // 1. Check for today's attempt first
            let existingAttempt = try await DailyQuiz.getDailyQuizAttemptToday(authManager: authManager)
            if let attempt = existingAttempt, attempt.success {
                // An attempt was found (either successful submission or already attempted)
                self.dailyQuiz = try await DailyQuiz.loadDailyQuizData(authManager: authManager) // Load quiz details to show question etc.
                self.attemptResult = attempt
                self.hasAttemptedToday = true
                self.selectedAnswer = attempt.selectedAnswer // Pre-fill selected answer if available
                print("Existing attempt found for today: \(attempt.message ?? "") Selected: \(attempt.selectedAnswer ?? "N/A") Correct: \(attempt.isCorrect)")
            } else if let attempt = existingAttempt, !attempt.success, attempt.message == "No daily quiz available for today." {
                // No quiz is available for today according to the attempt check endpoint
                self.errorMessage = attempt.message
                self.dailyQuiz = nil // Ensure no quiz is shown
                print("No daily quiz available for today (checked via attempt endpoint).")
            } else {
                // No attempt found, or attempt check failed in a way that means we should load the quiz
                self.dailyQuiz = try await DailyQuiz.loadDailyQuizData(authManager: authManager)
                self.hasAttemptedToday = false // Explicitly set to false
                print("No existing attempt, loaded fresh quiz.")
            }
        } catch let error as DailyQuizLoadError {
            handleLoadError(error)
        } catch {
            errorMessage = "An unexpected error occurred: \(error.localizedDescription)"
            print("Unexpected error in loadInitialData: \(error.localizedDescription)")
        }
        isLoading = false
    }

    func handleSubmitAnswer(quizId: Int, answer: String) async {
        isSubmitting = true
        errorMessage = nil
        do {
            let result = try await DailyQuiz.submitDailyQuizAnswer(quizId: quizId, selectedAnswer: answer, authManager: authManager)
            self.attemptResult = result
            self.hasAttemptedToday = true // Mark as attempted
            if result.success {
                print("Answer submitted successfully. Correct: \(result.isCorrect)")
                // Optionally, update user XP or other relevant data here if needed
            } else {
                errorMessage = result.message ?? "Failed to submit answer."
                print("Failed to submit answer: \(result.message ?? "No specific message")")
            }
        } catch let error as DailyQuizLoadError {
            handleLoadError(error)
        } catch {
            errorMessage = "An unexpected error occurred while submitting: \(error.localizedDescription)"
            print("Unexpected error in handleSubmitAnswer: \(error.localizedDescription)")
        }
        isSubmitting = false
    }
    
    func handleLoadError(_ error: DailyQuizLoadError) {
        switch error {
        case .badURL:
            errorMessage = "Invalid API URL."
        case .requestFailed(let underlyingError):
            errorMessage = "Request failed: \(underlyingError.localizedDescription)"
        case .authenticationTokenMissing:
            errorMessage = "Authentication token is missing. Please log in."
        case .invalidResponse(let statusCode, _):
            errorMessage = "Invalid server response (Status: \(statusCode))."
        case .decodingError(let underlyingError):
            errorMessage = "Failed to decode data: \(underlyingError.localizedDescription)"
        case .unknown(let underlyingError):
            errorMessage = "An unknown error occurred: \(underlyingError.localizedDescription)"
        }
        print("Error: \(errorMessage ?? "Unknown error") Details: \(error)")
    }

    func determineButtonBackgroundColor(for answer: String) -> Color {
        guard hasAttemptedToday, let result = attemptResult, let currentQuiz = dailyQuiz else {
            return selectedAnswer == answer ? Color.blue.opacity(0.7) : Color.blue.opacity(0.4)
        }
        
        if answer == result.correctAnswer {
            return Color.green.opacity(0.7)
        }
        if answer == selectedAnswer && !result.isCorrect {
            return Color.red.opacity(0.7)
        }
        return Color.gray.opacity(0.3) // Default for other answers after attempt
    }

    func determineButtonForegroundColor(for answer: String) -> Color {
        guard hasAttemptedToday, let result = attemptResult, let currentQuiz = dailyQuiz else {
            return .white
        }
        if answer == result.correctAnswer || (answer == selectedAnswer && !result.isCorrect) {
            return .white
        }
        return .primary // Default for other answers after attempt
    }
}

#Preview {
    // Create a mock AuthManager for the preview
    let mockAuthManager = AuthManager()
    // Optionally set a dummy token if your load functions require it for previewing data
    // mockAuthManager.idToken = "dummy_token_for_preview"

    return CardDailyQuiz()
        .environmentObject(mockAuthManager)
        // You might want to mock a DailyQuiz and DailyQuizAttemptResponse for different preview states
}
