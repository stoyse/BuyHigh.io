# BuyHigh.io API Endpoints Overview

This table lists all main API endpoints found in the `/router` package, their HTTP methods, and their purpose.

| Endpoint                                      | Method(s) | Purpose                                                                                   | Router File            |
|------------------------------------------------|-----------|-------------------------------------------------------------------------------------------|------------------------|
| `/auth/login`                                  | POST      | User login with credentials                                                               | auth_router.py         |
| `/auth/register`                               | POST      | User registration                                                                         | auth_router.py         |
| `/auth/google-login`                           | POST      | Login with Google token                                                                   | auth_router.py         |
| `/auth/firebase-login`                         | POST      | Login with Firebase token                                                                 | auth_router.py         |
| `/auth/anonymous-login`                        | POST      | Anonymous login with Firebase                                                             | auth_router.py         |
| `/auth/logout`                                 | POST      | User logout                                                                               | auth_router.py         |
| `/user/{user_id_param}`                        | GET       | Get user data by user ID                                                                  | user_router.py         |
| `/user/transactions/{user_id_param}`           | GET       | Get recent transactions for a user                                                        | user_router.py         |
| `/user/portfolio/{user_id_param}`              | GET       | Get portfolio data for a user                                                             | user_router.py         |
| `/users/all`                                   | GET       | Get all users (admin only)                                                                | user_router.py         |
| `/upload/profile-picture`                      | POST      | Upload a new profile picture                                                              | user_router.py         |
| `/get/profile-picture/{user_id_param}`         | GET       | Get profile picture for a user                                                            | user_router.py         |
| `/assets`                                      | GET       | Get all assets (optionally filtered)                                                      | asset_router.py        |
| `/assets/{symbol}`                             | GET       | Get data for a specific asset                                                             | asset_router.py        |
| `/trade/buy`                                   | POST      | Buy an asset (stock, crypto, etc.)                                                        | trade_router.py        |
| `/trade/sell`                                  | POST      | Sell an asset                                                                             | trade_router.py        |
| `/news/`                                       | GET       | Get news for all assets                                                                   | news_router.py         |
| `/funny-tips`                                  | GET       | Get a list of funny trading tips                                                          | misc_router.py         |
| `/status`                                      | GET       | Get API status (health, config)                                                           | misc_router.py         |
| `/health`                                      | GET       | Health check endpoint                                                                     | misc_router.py         |
| `/easter-egg`                                  | GET       | Get an easter egg (hidden feature)                                                        | easter_egg_router.py   |
| `/gamble/coinflip`                             | POST      | Record result of a coinflip game                                                          | gamble.py              |
| `/gamble/slots`                                | POST      | Record result of a slots game                                                             | gamble.py              |
| `/gamble/slots/play`                           | POST      | Play slots game (server calculates result)                                                | gamble.py              |
| `/gamble/test`                                 | GET       | Test endpoint for gamble router                                                           | gamble.py              |
| `/daily-quiz`                                  | GET       | Get the daily quiz                                                                        | education_router.py    |
| `/daily-quiz/attempt`                          | POST      | Submit an attempt for the daily quiz                                                      | education_router.py    |
| `/daily-quiz/attempt/today`                    | GET       | Get today's daily quiz attempt for the current user                                       | education_router.py    |
| `/roadmap`                                     | GET       | Get all educational roadmaps                                                              | education_router.py    |
| `/roadmap/{roadmap_id}/steps`                  | GET       | Get steps (with quizzes) for a specific roadmap                                           | education_router.py    |
| `/roadmap/quiz/attempt`                        | POST      | Submit an attempt for a roadmap quiz                                                      | education_router.py    |

> **Note:**  
> Some endpoints may require authentication or specific user roles (e.g., admin).  
> This table is based on the router structure and code comments as of the current codebase.
