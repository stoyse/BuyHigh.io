# BuyHigh.io FastAPI Backend

This directory contains the FastAPI backend for the BuyHigh.io application. It is responsible for providing API endpoints, processing user requests, interacting with the database, and executing business logic.

## Project Structure

```
buy_high_backend/
├── api_router.py       # Defines the API routes and their logic
├── auth_utils.py       # Helper functions for authentication and user management
├── main.py             # Main entry point, initializes FastAPI
├── pydantic_models.py  # Pydantic models for data validation
└── README.md           # This file
```

### `main.py`

This is the main entry point for the FastAPI application.
-   Initializes the `FastAPI` instance.
-   Includes the `api_router` from `api_router.py`, which provides all API endpoints under the `/api` prefix.
-   Configures the serving of static files (e.g., uploaded profile pictures) from the `static/` directory. The `static` directory is expected to be relative to the project root (one level above `buy_high_backend`).
-   Defines a root route (`/`) for a simple welcome check.
-   Contains a comment on how to start the application using `uvicorn`.

### `api_router.py`

This file contains the logic for all API endpoints. The routes were converted from a previous Flask implementation (`routes/api_routes.py`) to FastAPI.
-   Uses `APIRouter` to group endpoints.
-   Implements endpoints for:
    -   User authentication (`/login`)
    -   Retrieving stock data (`/stock-data`)
    -   Trading operations (`/trade/buy`, `/trade/sell`)
    -   Managing assets (`/assets`, `/assets/{symbol}`)
    -   Retrieving "Funny Tips" (`/funny-tips`)
    -   API status (`/status`)
    -   Uploading and retrieving profile pictures (`/upload/profile-picture`, `/get/profile-picture/{user_id}`)
    -   Daily quiz (`/daily-quiz`)
    -   User data and transactions (`/user/{user_id}`, `/user/transactions/{user_id}`, `/user/portfolio/{user_id}`)
    -   Redeeming Easter egg codes (`/easter-egg/redeem`, `/redeem-code`)
    -   Health check (`/health`)
-   Uses `Depends` for dependency injection, particularly for `get_current_user` from `auth_utils.py` to secure routes.
-   Uses Pydantic models from `pydantic_models.py` for request and response data validation.
-   Interacts with various modules for database operations (`db_handler`, `transactions_handler`, `education_handler`), stock data (`stock_data_api`), and authentication (`auth_module`).
-   Implements logging and error handling via `HTTPException`.

### `auth_utils.py`

This file provides helper functions for authentication.
-   `oauth2_scheme`: Defines the OAuth2 Password Bearer Flow for token-based authentication. The token URL points to `/api/login`.
-   `get_current_user`: An asynchronous function that serves as a FastAPI dependency. It is responsible for identifying the current user based on the provided token.
    -   **Important Note:** The current implementation is a **placeholder** and **not secure for production use**. It simulates user authentication by checking if a token starts with `firebase_uid_` or falls back to a test user. A real implementation would involve JWT token decoding and verification.
-   `AuthenticatedUser`: A Pydantic model class that inherits from `User` (from `pydantic_models.py`) and represents the type of the authenticated user.
-   Contains commented-out examples for a more robust `get_current_user` implementation using `jose` for JWTs.

### `pydantic_models.py`

This file defines Pydantic models used for data validation and serialization in the API routes.
-   For every complex request body or structured response, there is a corresponding model (e.g., `LoginRequest`, `StockDataPoint`, `TradeRequest`, `AssetResponse`).
-   This ensures that the API receives and sends type-safe data and enables automatic validation and generation of OpenAPI documentation.

## External Dependencies and Modules

The backend interacts with several external or project-internal modules that are not part of this specific `buy_high_backend` directory but are crucial for its functionality:

-   `database.handler.postgres.postgres_db_handler` (`db_handler`): For general database operations (user management, etc.).
-   `database.handler.postgres.postgre_transactions_handler` (`transactions_handler`): Specifically for transaction- and asset-related database operations.
-   `database.handler.postgres.postgre_education_handler` (`education_handler`): For logic related to educational content like the daily quiz.
-   `stock_data_api`: Module for retrieving stock data from external APIs or a cache.
-   `auth` (`auth_module`): The original module for Firebase authentication.
-   `add_analytics`: A function (presumably from `postgres_db_handler`) to log analytics events.

## Starting the Application

To start the FastAPI application locally, use `uvicorn`. Ensure you are in the project's root directory (`BuyHigh.io`):

```bash
uvicorn buy_high_backend.main:app --reload
```

-   `buy_high_backend.main`: Refers to the `main.py` file in the `buy_high_backend` directory.
-   `app`: Is the FastAPI instance created in `main.py`.
-   `--reload`: Ensures the server restarts automatically on code changes (useful for development).

The API will then be accessible by default at `http://127.0.0.1:8000`. The API documentation (Swagger UI) can be found at `http://127.0.0.1:8000/docs` and alternative documentation (ReDoc) at `http://127.0.0.1:8000/redoc`.
