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
    @State private var isLoading = true
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
        VStack(alignment: .leading, spacing: 20) {
            // Header with Glass Icon
            HStack {
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(.thinMaterial)
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                        )
                        .frame(width: 45, height: 45)
                    
                    Image(systemName: "questionmark.circle.fill")
                        .foregroundStyle(
                            LinearGradient(
                                colors: [Color.mint, Color.green],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .font(.title2)
                        .shadow(color: .mint.opacity(0.3), radius: 3, x: 0, y: 2)
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text("Daily Quiz")
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(.primary)
                    
                    Text("Test your knowledge")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
            }

            if isLoading {
                HStack {
                    Spacer()
                    VStack(spacing: 12) {
                        ProgressView()
                            .scaleEffect(1.2)
                        Text("Loading Quiz...")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                }
                .padding(.vertical, 20)
            } else if let errorMessage = errorMessage {
                VStack(spacing: 16) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.title)
                        .foregroundStyle(.orange)
                        .shadow(color: .orange.opacity(0.3), radius: 5, x: 0, y: 2)
                    
                    Text("Error: \(errorMessage)")
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                    
                    Button("Retry") {
                        Task {
                            await loadInitialData()
                        }
                    }
                    .glassButton()
                }
                .padding(.vertical, 16)
            } else if let quiz = dailyQuiz {
                VStack(alignment: .leading, spacing: 16) {
                    // Question
                    Text(quiz.question)
                        .font(.headline)
                        .fontWeight(.medium)
                        .foregroundStyle(.primary)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.bottom, 8)

                    // Answer Options
                    VStack(spacing: 12) {
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
                                        .foregroundStyle(determineButtonForegroundColor(for: answer))
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                    
                                    if hasAttemptedToday && attemptResult?.selectedAnswer == answer {
                                        if attemptResult?.isCorrect == true {
                                            Image(systemName: "checkmark.circle.fill")
                                                .foregroundStyle(.green)
                                                .font(.title3)
                                        } else {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundStyle(.red)
                                                .font(.title3)
                                        }
                                    }
                                }
                                .padding(.horizontal, 16)
                                .padding(.vertical, 14)
                                .background(
                                    ZStack {
                                        // Base material background
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(determineButtonBackgroundMaterial(for: answer))
                                        
                                        // Color overlay for states
                                        determineButtonBackgroundOverlay(for: answer)
                                    }
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 12)
                                            .stroke(determineButtonBorderColor(for: answer), lineWidth: 1.5)
                                    )
                                    .shadow(color: determineButtonShadowColor(for: answer), radius: 8, x: 0, y: 4)
                                )
                            }
                            .disabled(isSubmitting || hasAttemptedToday)
                        }
                    }

                    if isSubmitting {
                        HStack {
                            Spacer()
                            HStack(spacing: 8) {
                                ProgressView()
                                    .scaleEffect(0.8)
                                Text("Submitting...")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                        }
                        .padding(.top, 8)
                    }

                    if hasAttemptedToday, let result = attemptResult {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack {
                                Image(systemName: result.isCorrect ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundStyle(result.isCorrect ? .green : .red)
                                    .font(.title3)
                                
                                Text(result.isCorrect ? "Correct!" : "Incorrect")
                                    .font(.headline)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(result.isCorrect ? .green : .red)
                                
                                Spacer()
                            }
                            
                            if !result.isCorrect {
                                Text("Correct Answer: \(result.correctAnswer)")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            
                            if let explanation = result.explanation, !explanation.isEmpty {
                                Text("Explanation: \(explanation)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                            
                            if let xp = result.xpGained, xp > 0 {
                                HStack {
                                    Image(systemName: "star.fill")
                                        .foregroundStyle(.orange)
                                        .font(.caption)
                                    Text("XP Gained: \(xp)")
                                        .font(.caption)
                                        .fontWeight(.medium)
                                        .foregroundStyle(.orange)
                                }
                            }
                        }
                        .padding(16)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(.ultraThinMaterial)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                )
                        )
                    }
                }
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "questionmark.circle")
                        .font(.title)
                        .foregroundStyle(.secondary)
                    
                    Text("No quiz data available for today.")
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(.vertical, 20)
            }
        }
        .glassCard(cornerRadius: 20)
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
        guard hasAttemptedToday, let result = attemptResult else {
            return .primary // Use primary color for better light/dark mode adaptation
        }
        
        if answer == result.correctAnswer {
            return .white // White text on green background
        }
        if answer == selectedAnswer && !result.isCorrect {
            return .white // White text on red background
        }
        return .primary // Use primary color for other answers after attempt
    }
    
    func determineButtonBackgroundMaterial(for answer: String) -> Material {
        guard hasAttemptedToday, let result = attemptResult else {
            return selectedAnswer == answer ? .regularMaterial : .ultraThinMaterial
        }
        
        if answer == result.correctAnswer {
            return .regularMaterial // Use regular material for correct answer
        }
        if answer == selectedAnswer && !result.isCorrect {
            return .regularMaterial // Use regular material for incorrect answer
        }
        return .ultraThinMaterial
    }

    func determineButtonBorderColor(for answer: String) -> Color {
        guard hasAttemptedToday, let result = attemptResult else {
            return selectedAnswer == answer ? 
                Color.accentColor.opacity(0.6) : // Use accent color for selection
                Color.primary.opacity(0.2) // Use primary color with opacity for borders
        }
        
        if answer == result.correctAnswer {
            return Color.green.opacity(0.8)
        }
        if answer == selectedAnswer && !result.isCorrect {
            return Color.red.opacity(0.8)
        }
        return Color.primary.opacity(0.2)
    }

    func determineButtonShadowColor(for answer: String) -> Color {
        guard hasAttemptedToday, let result = attemptResult else {
            return selectedAnswer == answer ? 
                Color.accentColor.opacity(0.3) : // Use accent color for selection shadow
                Color.primary.opacity(0.1) // Use primary color for normal shadow
        }
        
        if answer == result.correctAnswer {
            return Color.green.opacity(0.4)
        }
        if answer == selectedAnswer && !result.isCorrect {
            return Color.red.opacity(0.4)
        }
        return Color.primary.opacity(0.1)
    }
    
    // Add new function for background overlay when answer is selected/correct/incorrect
    func determineButtonBackgroundOverlay(for answer: String) -> some View {
        Group {
            if hasAttemptedToday, let result = attemptResult {
                if answer == result.correctAnswer {
                    // Green overlay for correct answer
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color.green.opacity(0.2))
                } else if answer == selectedAnswer && !result.isCorrect {
                    // Red overlay for incorrect selected answer
                    RoundedRectangle(cornerRadius: 12)
                        .fill(Color.red.opacity(0.2))
                } else {
                    // No overlay for other answers
                    Color.clear
                }
            } else if selectedAnswer == answer {
                // Blue/accent overlay for currently selected answer before submission
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.accentColor.opacity(0.15))
            } else {
                Color.clear
            }
        }
    }
}

// Update the button background in the main body
extension CardDailyQuiz {
    var adaptiveButtonBackground: some View {
        // This would be used in the button styling within the main body
        EmptyView()
    }
}

#Preview {
    let mockAuthManager = AuthManager()
    CardDailyQuiz()
        .environmentObject(mockAuthManager)
}
