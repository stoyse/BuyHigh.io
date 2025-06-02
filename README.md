# BuyHigh.io – Feature Overview & Codebase Documentation

![Hackatime Badge](https://hackatime-badge.hackclub.com/U08RM2BCLBU/BuyHigh.io)

## Overview

BuyHigh.io is a gamified stock trading platform designed for learning and entertainment. It combines trading mechanics with playful elements like XP, badges, and a mood pet to engage users. The app is built using a modular architecture with FastAPI for the backend and React for the frontend.

---

## Features

### Core Features
- **User Authentication**: Register, login, and manage accounts with secure password hashing.
- **Portfolio Management**: Track your assets, view performance, and calculate gains/losses.
- **Stock Trading**: Buy and sell stocks with real-time or demo data.
- **Dashboard**: Overview of account balance, portfolio, recent transactions, and achievements.
- **Gamification**: Earn XP, unlock badges, and level up as you trade.
- **Mood Pet**: A virtual companion reflecting your trading success.
- **Meme Mode**: Activate fun, meme-inspired features for a lighthearted experience.

### Advanced Features
- **Chat System**: Real-time messaging with Firebase integration and SQLite fallback.
- **Interactive Charts**: Candlestick charts with multiple timeframes and live updates.
- **API Endpoints**: RESTful APIs for stock data, trading, and portfolio management.
- **Management CLI**: Tools for database setup, Firebase migration, and status checks.

### Planned Features
- **Stripe Integration**: Add real money to purchase virtual currency.
- **Passkey Login**: Secure authentication using passkeys.
- **Electron Support**: Desktop application for enhanced usability.
- **Multilingual Support**: Localization for a global audience.

---

## Codebase Overview

### Backend (FastAPI)
- **`main.py`**: Initializes the FastAPI app and includes API routes.
- **`auth_utils.py`**: Helper functions for authentication and user management.
- **`pydantic_models.py`**: Defines Pydantic models for data validation.
- **Routers**: Modular route definitions for trading, user management, and more.
  - Example: `trade_router.py` handles buy/sell operations.
- **Middleware**: Custom middleware for request handling.

### Frontend (React)
- **`src/`**: Contains React components and application logic.
- **`public/`**: Static assets like images and the `index.html` file.
- **`package.json`**: Manages dependencies and scripts.
- **Tailwind CSS**: Used for styling.

### iOS App (SwiftUI)
- **`BuyHigh/BuyHighApp.swift`**: The main entry point of the iOS application, sets up the environment.
- **`BuyHigh/ContentView.swift`**: Root view that handles navigation based on authentication state.
- **`BuyHigh/AuthManager.swift`**: Manages user authentication state and API token handling.
- **`BuyHigh/View/`**: Directory containing SwiftUI views for different screens of the app (e.g., `ViewDashboard.swift`, `ViewTrade.swift`).
- **`BuyHigh/Load/`**: Directory for data loading classes that interact with the backend API (e.g., `LoadUser.swift`, `LoadTrade.swift`).
- **`BuyHigh/Components/`**: Directory for reusable SwiftUI components (e.g., `CardTrade.swift`).
- **`BuyHigh.xcodeproj`**: Xcode project file to build and run the iOS application.

### Database
- **Schema**: Defined in `postgres_schema.sql`.
- **Tables**:
  - `users`: Stores user details, balance, and preferences.
  - `transactions`: Records buy/sell actions.
  - `portfolio`: Tracks user holdings and investments.
- **Entity-Relationship Diagram**: See `erd_diagram.png` for a visual representation.

### Utilities
- **`auth.py`**: Firebase authentication integration.
- **`utils.py`**: General utility functions.

---

## Running the Project

### Backend
Use the `start_fastapi.sh` script to start the FastAPI server:
```bash
./start_fastapi.sh
```
This script:
- Activates the virtual environment.
- Installs dependencies from `requirements.txt`.
- Starts the FastAPI server on `http://127.0.0.1:9877`.

### Frontend
Run the following commands in the `buyhigh_frontend` directory:
```bash
yarn install
yarn start
```
This starts the React development server on `http://localhost:3000`.

### iOS App
To run the iOS application:
1. Navigate to the `BuyHigh/` directory.
2. Open the `BuyHigh.xcodeproj` file in Xcode.
3. Select a simulator or a connected device.
4. Click the "Run" button (or press Cmd+R).

---

## Notes

- Prices are stored in USD, while account balances are in EUR.
- Demo data is used when API data is unavailable.
- The app is for educational purposes and not for real trading.
