# BuyHigh.io FastAPI Backend

Dieses Verzeichnis enthält das FastAPI-Backend für die BuyHigh.io-Anwendung. Es ist dafür zuständig, API-Endpunkte bereitzustellen, Benutzeranfragen zu verarbeiten, mit der Datenbank zu interagieren und Geschäftslogik auszuführen.

## Projektstruktur

```
buy_high_backend/
├── api_router.py       # Definiert die API-Routen und deren Logik
├── auth_utils.py       # Hilfsfunktionen für Authentifizierung und Benutzerverwaltung
├── main.py             # Hauptanwendungspunkt, initialisiert FastAPI
├── pydantic_models.py  # Pydantic-Modelle für Datenvalidierung
└── README.md           # Diese Datei
```

### `main.py`

Dies ist der Haupteinstiegspunkt für die FastAPI-Anwendung.
-   Initialisiert die `FastAPI`-Instanz.
-   Bindet den `api_router` aus `api_router.py` ein, der alle API-Endpunkte unter dem Präfix `/api` bereitstellt.
-   Konfiguriert das Servieren von statischen Dateien (z.B. hochgeladene Profilbilder) aus dem Verzeichnis `static/`. Das `static`-Verzeichnis wird relativ zum Projektstamm erwartet (eine Ebene über `buy_high_backend`).
-   Definiert eine Root-Route (`/`) für einen einfachen Willkommens-Check.
-   Enthält einen Kommentar, wie die Anwendung mit `uvicorn` gestartet werden kann.

### `api_router.py`

Diese Datei enthält die Logik für alle API-Endpunkte. Die Routen wurden von einer früheren Flask-Implementierung (`routes/api_routes.py`) zu FastAPI konvertiert.
-   Verwendet `APIRouter` um Endpunkte zu gruppieren.
-   Implementiert Endpunkte für:
    -   Benutzerauthentifizierung (`/login`)
    -   Abrufen von Aktiendaten (`/stock-data`)
    -   Handelsoperationen (`/trade/buy`, `/trade/sell`)
    -   Verwaltung von Assets (`/assets`, `/assets/{symbol}`)
    -   Abrufen von "Funny Tips" (`/funny-tips`)
    -   API-Status (`/status`)
    -   Hochladen und Abrufen von Profilbildern (`/upload/profile-picture`, `/get/profile-picture/{user_id}`)
    -   Tägliches Quiz (`/daily-quiz`)
    -   Benutzerdaten und Transaktionen (`/user/{user_id}`, `/user/transactions/{user_id}`, `/user/portfolio/{user_id}`)
    -   Einlösen von Easter-Egg-Codes (`/easter-egg/redeem`, `/redeem-code`)
    -   Gesundheitscheck (`/health`)
-   Nutzt `Depends` für Dependency Injection, insbesondere für `get_current_user` aus `auth_utils.py` zur Absicherung von Routen.
-   Verwendet Pydantic-Modelle aus `pydantic_models.py` für die Validierung von Anfrage- und Antwortdaten.
-   Interagiert mit verschiedenen Modulen für Datenbankoperationen (`db_handler`, `transactions_handler`, `education_handler`), Aktiendaten (`stock_data_api`) und Authentifizierung (`auth_module`).
-   Implementiert Logging und Fehlerbehandlung über `HTTPException`.

### `auth_utils.py`

Diese Datei stellt Hilfsfunktionen für die Authentifizierung bereit.
-   `oauth2_scheme`: Definiert das OAuth2 Password Bearer Flow für die Token-basierte Authentifizierung. Der Token-URL verweist auf `/api/login`.
-   `get_current_user`: Eine asynchrone Funktion, die als FastAPI-Dependency dient. Sie ist dafür zuständig, den aktuellen Benutzer basierend auf dem bereitgestellten Token zu identifizieren.
    -   **Wichtiger Hinweis:** Die aktuelle Implementierung ist ein **Platzhalter** und **nicht sicher für den Produktionseinsatz**. Sie simuliert die Benutzerauthentifizierung, indem sie prüft, ob ein Token mit `firebase_uid_` beginnt oder greift auf einen Testbenutzer zurück. Eine echte Implementierung würde JWT-Token-Dekodierung und -Verifizierung beinhalten.
-   `AuthenticatedUser`: Eine Pydantic-Modellklasse, die von `User` (aus `pydantic_models.py`) erbt und den Typ des authentifizierten Benutzers repräsentiert.
-   Enthält auskommentierte Beispiele für eine robustere `get_current_user`-Implementierung mit `jose` für JWTs.

### `pydantic_models.py`

Diese Datei definiert Pydantic-Modelle, die für die Datenvalidierung und -serialisierung in den API-Routen verwendet werden.
-   Für jeden komplexen Request-Body oder jede strukturierte Response gibt es ein entsprechendes Modell (z.B. `LoginRequest`, `StockDataPoint`, `TradeRequest`, `AssetResponse`).
-   Dies stellt sicher, dass die API typsichere Daten empfängt und sendet, und ermöglicht automatische Validierung und Generierung von OpenAPI-Dokumentation.

## Externe Abhängigkeiten und Module

Das Backend interagiert mit mehreren externen oder projektinternen Modulen, die nicht Teil dieses spezifischen `buy_high_backend`-Verzeichnisses sind, aber für seine Funktion entscheidend sind:

-   `database.handler.postgres.postgres_db_handler` (`db_handler`): Für allgemeine Datenbankoperationen (Benutzerverwaltung, etc.).
-   `database.handler.postgres.postgre_transactions_handler` (`transactions_handler`): Speziell für Transaktions- und Asset-bezogene Datenbankoperationen.
-   `database.handler.postgres.postgre_education_handler` (`education_handler`): Für Logik im Zusammenhang mit Lerninhalten wie dem täglichen Quiz.
-   `stock_data_api`: Modul zum Abrufen von Aktiendaten von externen APIs oder aus einem Cache.
-   `auth` (`auth_module`): Das ursprüngliche Modul zur Firebase-Authentifizierung.
-   `add_analytics`: Eine Funktion (vermutlich aus `postgres_db_handler`), um Analyseereignisse zu protokollieren.

## Starten der Anwendung

Um die FastAPI-Anwendung lokal zu starten, verwenden Sie `uvicorn`. Stellen Sie sicher, dass Sie sich im Hauptverzeichnis des Projekts (`BuyHigh.io`) befinden:

```bash
uvicorn buy_high_backend.main:app --reload
```

-   `buy_high_backend.main`: Verweist auf die Datei `main.py` im Verzeichnis `buy_high_backend`.
-   `app`: Ist die FastAPI-Instanz, die in `main.py` erstellt wurde.
-   `--reload`: Sorgt dafür, dass der Server bei Codeänderungen automatisch neu startet (nützlich für die Entwicklung).

Die API ist dann standardmäßig unter `http://127.0.0.1:8000` erreichbar. Die API-Dokumentation (Swagger UI) finden Sie unter `http://127.0.0.1:8000/docs` und alternative Dokumentation (ReDoc) unter `http://127.0.0.1:8000/redoc`.
