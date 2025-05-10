# BuyHigh.io – Feature Overview & Codebase Documentation

![Hackatime Badge](https://hackatime-badge.hackclub.com/U08RM2BCLBU/BuyHigh.io)

---

## Overview

BuyHigh.io is a Flask-based web application for playful stock trading with gamification elements, pixel-art design, and user profiles. The app supports registration, login, portfolio management, stock trading (buy/sell), dashboard, settings (including theme), chat features, and API endpoints for AJAX/JS interactions.

---

## Main Features & Pages

### 1. Authentication & User Management

- **Registration (`/register`)**
  - Username, email, password
  - Validation, password hashing (bcrypt)
- **Login (`/login`)**
  - Session handling, password verification
- **Logout (`/logout`)**
  - Session clearing, redirect

### 2. Main Pages

- **Home (`/`)**
  - Welcome message, user info, account balance, mood pet, meme mode, statistics
  - Quick summary of your account and playful elements
- **Dashboard (`/dashboard`)**
  - **Account Overview:** Shows current balance (in EUR), total trades, and realized profit/loss (in EUR)
  - **Portfolio:** List of all assets (stocks, crypto, etc.) you currently hold, with quantities and types
  - **Mood Pet & Energy:** Displays your mood pet and its current energy (out of 100)
  - **Meme Mode:** Indicates whether meme mode is enabled for your account
  - **Recent Activity:** List of your latest buy/sell transactions, with date, symbol, quantity, and price
  - **Player Status:** Shows your trader level, XP progress, and unlocked badges (e.g., first trade, streaks)
  - **Market Mood (Coming Soon):** Placeholder for future market sentiment features
- **Trade (`/trade`)**
  - **Stock List & Search:** Browse and search for stocks, ETFs, indices, and crypto. Click to select.
  - **Candlestick Chart:** Interactive chart (ApexCharts) for the selected symbol and timeframe
  - **Timeframe Selection:** Choose between 1MIN, 1W, 1M, 3M, 6M, 1Y, ALL for chart data
  - **Trade Form:** Buy/sell form with quantity, price, total, and potential gain/loss calculation
  - **Stats:** Shows volume, high, low, and market cap for the selected asset
  - **Live Updates:** For 1MIN timeframe, chart updates live every minute
- **Settings (`/settings`)**
  - **Theme Selection:** Choose between light and dark mode for your account
  - **Change Password:** Update your account password with validation
  - **Delete Account:** Permanently delete your account and all associated data (requires password confirmation).
- **Chat (`/chat/chats`)**
  - **Chat List:** Browse all your chat rooms with last messages and activity times
  - **Chat Search:** Filter chats by name
  - **Create Chat:** Create new chat rooms with custom names
  - **Chat Room (`/chat/<chat_id>`):** Real-time messaging with other users 
  - **Default General Chat:** System ensures users are added to a default "General" chat room

---

## API Endpoints (`/api/...`)

- **/api/stock-data**
  - Returns price data (historical or intraday) for a symbol and timeframe (JSON)
- **/api/trade/buy**
  - POST: Buy a stock (symbol, quantity, price)
- **/api/trade/sell**
  - POST: Sell a stock (symbol, quantity, price)
- **/api/portfolio**
  - Returns the user's portfolio and account balance

---

## Backend Modules & Functions

### `app.py`
- Flask app setup, routing, session handling, login decorator, API endpoints

### `routes/`
- **main_routes.py**: Main page routes (index, dashboard, trade, settings)
- **auth_routes.py**: Authentication (register, login, logout)
- **api_routes.py**: API endpoints for AJAX/JS
- **chat_routes.py**: Chat-related routes and WebSocket handlers

### `db_handler.py`
- SQLite DB initialization (users, asset_types, transactions)
- User management (CRUD)
- Theme and password update
- Timestamp parsing

### `chat_db_handler.py`
- SQLite-based chat operations (fallback)
- Chat room and message management

### `firebase_db_handler.py`
- Firebase Realtime Database integration for chat features
- Handles chat rooms, messages, and participants
- Provides automatic failover to SQLite

### `manage.py`
- Management CLI for BuyHigh.io
- Database setup, migration, and status checks
- Firebase chat maintenance and reset

### `transactions_handler.py`
- Buy/sell logic (with EUR/USD conversion)
- FIFO profit/loss calculation
- Portfolio display
- Recent transactions
- Asset type initialization

### `stock_data.py`
- Price data from Alpha Vantage (historical, intraday)
- Demo data generator (synthetic, for development)

### `auth.py`
- Password hashing and verification (bcrypt)

### `utils.py`
- Login decorator for Flask routes

---

## Firebase Integration

BuyHigh.io uses Firebase Realtime Database for chat features, with automatic fallback to SQLite:

- **Database Structure**
  - `/chats` - Chat room information and metadata
  - `/chat_participants` - User participation in chats
  - `/messages` - Chat messages with timestamps

- **Management**
  - Use `python manage.py status` to check Firebase connection status
  - Use `python manage.py reset-firebase-chat` to reset chat data
  - Use `python manage.py migrate` to copy SQLite chat data to Firebase

For complete documentation on Firebase integration, see [firebase.md](firebase.md).

---

## Frontend

### Templates (`/templates/`)

- **base.html**: Layout, navigation, theme, flash messages
- **index.html**: Home page with user summary and playful info
- **dashboard.html**: Dashboard with account stats, portfolio, activities, player status, and mood pet
- **trade.html**: Trading interface with stock list, chart, trade form, and stats
- **settings.html**: Settings (theme, password)
- **login.html / register.html**: Authentication pages
- **chat_collection.html**: List of all chat rooms for the user
- **chat_details.html**: Individual chat room with messaging interface
- **new_chat.html**: Form to create new chat rooms

#### Page Details

- **index.html**
  - Shows a welcome message, user greeting, balance, mood pet, meme mode status, and quick stats.
  - If not logged in, prompts to log in or register.

- **dashboard.html**
  - Account overview: EUR balance, total trades, realized profit/loss.
  - Portfolio: List of all assets with symbol, quantity, and type.
  - Mood pet: Name and energy bar.
  - Meme mode: Toggle status.
  - Recent activity: List of last transactions (buy/sell, date, symbol, price).
  - Player status: Level, XP, badges, and progress bars.
  - Market mood: Placeholder for future features.

- **trade.html**
  - Left: Searchable stock list with pixel-art mini-charts.
  - Right: Candlestick chart (ApexCharts), timeframe selection, trade form (buy/sell), and stats (volume, high, low, market cap).
  - Live chart updates for 1MIN timeframe.
  - Shows your current EUR balance.

- **settings.html**
  - Theme selection (light/dark) with immediate effect.
  - Change password form with validation and feedback.
  - Delete account form with password confirmation.

- **login.html / register.html**
  - Clean forms for authentication, with dark mode support.

- **chat_collection.html**
  - List of all chat rooms the user participates in
  - Search functionality to filter chats
  - Button to create new chats

- **chat_details.html**
  - Real-time messaging interface 
  - WebSocket-based updates
  - Message history

### Static Files

- **/static/js/trade.js**: 
  - Handles chart rendering (ApexCharts)
  - AJAX for price data, portfolio, and trades
  - UI updates, search, timeframe switching, live updates
- **/static/js/chat.js**:
  - WebSocket handling for real-time messaging
  - Message formatting and display

---

## Database Structure

- **users**: id, username, email, password_hash, balance, created_at, last_login, mood_pet, pet_energy, is_meme_mode, email_verified, theme, total_trades, profit_loss
- **asset_types**: id, name
- **transactions**: id, user_id, asset_type_id, asset_symbol, quantity, price_per_unit, transaction_type, timestamp
- **chat_rooms**: id, name, created_at, created_by, members_can_invite
- **chat_room_participants**: chat_room_id, user_id, chat_name, joined_at
- **messages**: id, chat_room_id, user_id, message_text, sent_at

---

## Management Commands

- **python manage.py setup** - Initialize the database schema
- **python manage.py status** - Check Firebase connection status
- **python manage.py migrate** - Migrate chat data from SQLite to Firebase
- **python manage.py reset-firebase-chat** - Reset Firebase chat data and create default chat

---

## Notes

- All prices and transactions are stored in USD; account balance and profit/loss are in EUR (with a fixed conversion rate).
- Demo data is used if no API data is available.
- The application is for learning and demo purposes only, not for real trading.
- Chat features support automatic fallback to SQLite if Firebase is unavailable.

---
