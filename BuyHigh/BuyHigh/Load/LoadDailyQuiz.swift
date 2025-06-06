//
//  LoadDailyQuiz.swift
//  BuyHigh
//
//  Created by Julian Stosse on 30.05.25.
//

import Foundation
import SwiftUI

struct DailyQuiz: Codable, Identifiable {
    let id: Int
    let date: String
    let question: String
    let possibleAnswer1: String
    let possibleAnswer2: String
    let possibleAnswer3: String
    let correctAnswer: String
    // let createdAt: String // Uncomment if you need this field from the JSON

    enum CodingKeys: String, CodingKey {
        case id, date, question
        case possibleAnswer1 = "possible_answer_1"
        case possibleAnswer2 = "possible_answer_2"
        case possibleAnswer3 = "possible_answer_3"
        case correctAnswer = "correct_answer"
        // case createdAt = "created_at" // Uncomment if you need this field
    }
}

// Custom error type for loading daily quiz data
enum DailyQuizLoadError: Error {
    case badURL
    case requestFailed(Error)
    case authenticationTokenMissing
    case invalidResponse(statusCode: Int, data: Data?)
    case decodingError(Error)
    case unknown(Error)
}

// MARK: - Daily Quiz Attempt Structures
struct DailyQuizAttemptRequest: Codable {
    let quizId: Int
    let selectedAnswer: String

    enum CodingKeys: String, CodingKey {
        case quizId = "quiz_id"
        case selectedAnswer = "selected_answer"
    }
}

struct DailyQuizAttemptResponse: Codable, Identifiable {
    // Adding Identifiable conformance for potential use in lists, using a computed id.
    var id: String { "\(success)-\(isCorrect)-\(correctAnswer)-\(selectedAnswer ?? "")" }
    
    let success: Bool
    let isCorrect: Bool
    let correctAnswer: String
    let explanation: String?
    let xpGained: Int?
    let message: String?
    let selectedAnswer: String?

    enum CodingKeys: String, CodingKey {
        case success
        case isCorrect = "is_correct"
        case correctAnswer = "correct_answer"
        case explanation
        case xpGained = "xp_gained"
        case message
        case selectedAnswer = "selected_answer"
    }
}

extension DailyQuiz {


    private static let apiBaseURL = "https://api.stoyse.hackclub.app" // Ensure this is your actual API base URL

    static func loadDailyQuizData(authManager: AuthManager) async throws -> DailyQuiz {
        guard let url = URL(string: "\(apiBaseURL)/daily-quiz") else {
            print("Error: Invalid URL constructed: \(apiBaseURL)/daily-quiz")
            throw DailyQuizLoadError.badURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 30.0

        // Get a fresh token using the new getValidToken method
        guard let authToken = await authManager.getValidToken() else {
            print("Error: Failed to get valid authentication token. Ensure the user is logged in.")
            throw DailyQuizLoadError.authenticationTokenMissing
        }
        request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        
        print("DailyQuiz: Using fresh token for daily quiz request")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("Error: Did not receive a valid HTTP response object.")
                throw DailyQuizLoadError.invalidResponse(statusCode: 0, data: data)
            }
            
            // print("Received HTTP status code: \(httpResponse.statusCode)") // For debugging
            // if let responseString = String(data: data, encoding: .utf8) { // For debugging
            //     print("Raw response data (first 500 chars): \(String(responseString.prefix(500)))")
            // }

            guard (200...299).contains(httpResponse.statusCode) else {
                var errorMessage = "Error: Server returned status code \(httpResponse.statusCode)."
                if let responseString = String(data: data, encoding: .utf8), !responseString.isEmpty {
                    errorMessage += " Response: \(responseString)"
                } else {
                    errorMessage += " No response body."
                }
                print(errorMessage)
                throw DailyQuizLoadError.invalidResponse(statusCode: httpResponse.statusCode, data: data)
            }

            let decoder = JSONDecoder()
            let dailyQuiz = try decoder.decode(DailyQuiz.self, from: data)
            // print("Successfully decoded DailyQuiz data for date: \(dailyQuiz.date)") // For debugging
            return dailyQuiz
        } catch let error as DecodingError {
            print("Error: Failed to decode JSON for DailyQuiz: \(error.localizedDescription)")
            // Log detailed decoding error information
            switch error {
            case .typeMismatch(let type, let context):
                print("Type \'\(type)\' mismatch: \(context.debugDescription) at codingPath: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))")
            case .valueNotFound(let value, let context):
                print("Value \'\(value)\' not found: \(context.debugDescription) at codingPath: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))")
            case .keyNotFound(let key, let context):
                print("Key \'\(key)\' not found: \(context.debugDescription) at codingPath: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))")
            case .dataCorrupted(let context):
                print("Data corrupted: \(context.debugDescription) at codingPath: \(context.codingPath.map { $0.stringValue }.joined(separator: "."))")
            @unknown default:
                print("Unknown decoding error: \(error.localizedDescription)")
            }
            // Optionally, log the data that failed to decode (be careful with sensitive data in production logs)
            // if let responseString = String(data: (try? URLSession.shared.data(for: request).0) ?? Data(), encoding: .utf8) {
            //      print("Data that failed to decode (first 500 chars): \(String(responseString.prefix(500)))")
            // }
            throw DailyQuizLoadError.decodingError(error)
        } catch let specificError as DailyQuizLoadError {
             throw specificError // Re-throw known errors like authenticationTokenMissing
        }
        catch {
            print("Error: Network request or other unexpected error for \(url.absoluteString): \(error.localizedDescription)")
            throw DailyQuizLoadError.unknown(error)
        }
    }

    static func submitDailyQuizAnswer(quizId: Int, selectedAnswer: String, authManager: AuthManager) async throws -> DailyQuizAttemptResponse {
        guard let url = URL(string: "\(apiBaseURL)/daily-quiz/attempt") else {
            throw DailyQuizLoadError.badURL
        }

        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            throw DailyQuizLoadError.authenticationTokenMissing
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.timeoutInterval = 30.0

        let requestBody = DailyQuizAttemptRequest(quizId: quizId, selectedAnswer: selectedAnswer)
        do {
            request.httpBody = try JSONEncoder().encode(requestBody)
        } catch {
            print("Error encoding DailyQuizAttemptRequest: \(error)")
            throw DailyQuizLoadError.unknown(error)
        }
        
        print("DailyQuiz: Submitting answer with fresh token to \(url.absoluteString) with quizId: \(quizId), answer: \(selectedAnswer)")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw DailyQuizLoadError.invalidResponse(statusCode: 0, data: data)
        }
        
        print("Submit Quiz Response Status: \(httpResponse.statusCode)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("Submit Quiz Raw Response: \(responseString)")
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            // Attempt to decode a more specific error message from backend if available
            // This part can be enhanced if your backend sends structured error messages for failed attempts
            print("Error submitting quiz. Status: \(httpResponse.statusCode). Data: \(String(data: data, encoding: .utf8) ?? "No data")")
            throw DailyQuizLoadError.invalidResponse(statusCode: httpResponse.statusCode, data: data)
        }

        do {
            let decodedResponse = try JSONDecoder().decode(DailyQuizAttemptResponse.self, from: data)
            print("Successfully decoded DailyQuizAttemptResponse.")
            return decodedResponse
        } catch {
            print("Error decoding DailyQuizAttemptResponse: \(error)")
            if let responseString = String(data: data, encoding: .utf8) {
                print("Data that failed to decode: \(responseString)")
            }
            throw DailyQuizLoadError.decodingError(error)
        }
    }

    static func getDailyQuizAttemptToday(authManager: AuthManager) async throws -> DailyQuizAttemptResponse? {
        guard let url = URL(string: "\(apiBaseURL)/daily-quiz/attempt/today") else {
            throw DailyQuizLoadError.badURL
        }

        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            throw DailyQuizLoadError.authenticationTokenMissing
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.timeoutInterval = 30.0
        
        print("DailyQuiz: Fetching today's quiz attempt with fresh token from \(url.absoluteString)")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw DailyQuizLoadError.invalidResponse(statusCode: 0, data: data)
        }
        
        print("Get Today's Attempt Response Status: \(httpResponse.statusCode)")
        if let responseString = String(data: data, encoding: .utf8) {
            print("Get Today's Attempt Raw Response: \(responseString)")
        }


        guard (200...299).contains(httpResponse.statusCode) else {

            print("Error fetching today's attempt. Status: \(httpResponse.statusCode). Data: \(String(data: data, encoding: .utf8) ?? "No data")")
            throw DailyQuizLoadError.invalidResponse(statusCode: httpResponse.statusCode, data: data)
        }

        do {
            let decodedResponse = try JSONDecoder().decode(DailyQuizAttemptResponse.self, from: data)
            print("Successfully decoded DailyQuizAttemptResponse for today's attempt.")
            return decodedResponse
        } catch {
            print("Error decoding DailyQuizAttemptResponse for today's attempt: \(error)")
            if let responseString = String(data: data, encoding: .utf8) {
                print("Data that failed to decode: \(responseString)")
            }
            throw DailyQuizLoadError.decodingError(error)
        }
    }
}

