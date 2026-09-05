# VoxVision AI — System Architecture

## Overview

VoxVision AI is a real-time meeting assistant built as a **Chrome Extension** paired with a **FastAPI backend**. During a Google Meet session, the extension captures microphone speech using the Web Speech API, periodically screenshots the shared screen for OCR text extraction, and lets users mark important moments—all streamed to the backend. When the meeting ends, the backend aggregates all captured data and sends it to an AI provider (Gemini, OpenAI, OpenRouter, or a built-in Demo provider) to generate a structured, editable meeting report. The final report can be exported as a `.docx` Word document.

The architecture follows a clear separation of concerns:
- **Chrome Extension** — Handles all client-side UI, speech capture, screen capture, and user interactions within the Google Meet page.
- **FastAPI Backend** — Provides the REST API, manages data persistence in MongoDB, performs OCR via Tesseract, and orchestrates AI report generation.

---

## Meeting Flow — Sequence Diagram

The following diagram shows the end-to-end flow of a meeting session, from creation to report export:

```mermaid
sequenceDiagram
    actor User
    participant Ext as Chrome Extension
    participant API as FastAPI Backend
    participant DB as MongoDB
    participant OCR as Tesseract OCR
    participant AI as AI Provider<br/>(Gemini/OpenAI/OpenRouter/Demo)

    User->>Ext: Start meeting
    Ext->>API: POST /api/meetings
    API->>DB: Insert meeting document
    DB-->>API: Meeting ID
    API-->>Ext: Meeting created (ID)

    loop During meeting
        User->>Ext: Speak (microphone)
        Ext->>Ext: Web Speech API captures audio
        Ext->>API: POST /api/meetings/{id}/transcripts/batch
        API->>DB: Store transcript entries
        API-->>Ext: Transcripts saved

        Ext->>Ext: Capture screen periodically
        Ext->>API: POST /api/meetings/{id}/screen/analyze
        API->>OCR: Extract text from image
        OCR-->>API: Extracted text + metadata
        API->>DB: Store screen text entry
        API-->>Ext: Screen analysis result

        opt User marks important point
            User->>Ext: Click "Mark Important"
            Ext->>API: POST /api/meetings/{id}/important-points
            API->>DB: Store important point
            API-->>Ext: Important point saved
        end
    end

    User->>Ext: Stop meeting
    Ext->>API: POST /api/meetings/{id}/stop
    API->>DB: Update meeting status
    API-->>Ext: Meeting stopped

    User->>Ext: Generate report
    Ext->>API: POST /api/meetings/{id}/reports/generate
    API->>DB: Fetch all transcripts, screen text, important points
    DB-->>API: Meeting data
    API->>AI: Send aggregated data for report generation
    AI-->>API: Structured report (summary, insights, tasks, etc.)
    API->>DB: Store generated report
    API-->>Ext: Report ready

    Ext-->>User: Display editable report

    opt Export report
        User->>Ext: Click "Export DOCX"
        Ext->>API: GET /api/meetings/{id}/export/docx
        API->>DB: Fetch report
        API-->>Ext: .docx binary file
        Ext-->>User: Download Word document
    end
```

---

## Component Architecture

The following diagram shows the internal component structure of both the Chrome Extension and the FastAPI Backend:

```mermaid
graph TB
    subgraph chrome["Chrome Extension"]
        CS[Content Script]
        SW[Service Worker]
        SD[Shadow DOM Widget]
        WSA[Web Speech API]
        SC[Screen Capture]

        CS --- SD
        CS --- WSA
        CS --- SC
        CS <--> SW
    end

    subgraph backend["FastAPI Backend"]
        subgraph routes["API Routes"]
            MR[Meeting Routes]
            TR[Transcript Routes]
            SR[Screen Routes]
            IP[Important Point Routes]
            RR[Report Routes]
            ER[Export Routes]
        end

        subgraph services["Services"]
            MS[Meeting Service]
            TS[Transcript Service]
            SS[Screen Analysis Service]
            RS[Report Service]
            ES[Export Service]
        end

        subgraph ai["AI Providers"]
            GEM[Gemini]
            OAI[OpenAI]
            OR[OpenRouter]
            DEMO[Demo Provider]
        end

        OCR[Tesseract OCR]
        DB[(MongoDB)]

        routes --> services
        SS --> OCR
        RS --> ai
        services --> DB
    end

    SW <-->|HTTP REST API| routes

    style chrome fill:#1a1a2e,stroke:#6c63ff,color:#e0e0e0
    style backend fill:#16213e,stroke:#00b4d8,color:#e0e0e0
    style routes fill:#0f3460,stroke:#e94560,color:#e0e0e0
    style services fill:#0f3460,stroke:#00b4d8,color:#e0e0e0
    style ai fill:#0f3460,stroke:#ffd700,color:#e0e0e0
```

---

## Technology Stack

### Chrome Extension (Frontend)

| Technology | Purpose |
|---|---|
| **JavaScript (ES6+)** | Core extension logic |
| **Chrome Extensions Manifest V3** | Extension architecture and permissions |
| **Web Speech API** | Real-time browser-based speech-to-text |
| **Shadow DOM** | Encapsulated UI widget injected into Google Meet |
| **Content Scripts** | Interact with the Google Meet page DOM |
| **Service Worker** | Background processing, API communication, lifecycle management |
| **Canvas API** | Screen capture and image processing |

### Backend

| Technology | Purpose |
|---|---|
| **Python 3.10+** | Backend language |
| **FastAPI** | Async REST API framework |
| **Uvicorn** | ASGI server |
| **Motor** | Async MongoDB driver for Python |
| **MongoDB** | NoSQL document database for all persistent data |
| **Tesseract OCR (pytesseract)** | Optical Character Recognition for screen captures |
| **Pillow (PIL)** | Image processing and manipulation |
| **python-docx** | Word document (.docx) generation for report export |
| **Google Generative AI SDK** | Gemini AI provider integration |
| **OpenAI SDK** | OpenAI and OpenRouter provider integration |
| **Pydantic** | Request/response validation and serialization |

### Infrastructure & Tooling

| Technology | Purpose |
|---|---|
| **CORS Middleware** | Cross-origin request handling for extension ↔ backend communication |
| **python-dotenv** | Environment variable management |
| **Git** | Version control |

---

## Data Flow

### 1. Meeting Initialization

When the user starts a meeting from the extension widget, the content script communicates with the service worker, which sends a `POST /api/meetings` request to the backend. The backend creates a meeting document in MongoDB and returns the meeting ID. All subsequent data (transcripts, screen captures, important points) is linked to this meeting ID.

### 2. Real-Time Data Capture

During an active meeting, two parallel data streams flow from the extension to the backend:

- **Speech transcription:** The Web Speech API continuously captures microphone audio, converts it to text, and the extension batches these transcript segments before sending them to the backend via `POST /api/meetings/{id}/transcripts/batch`.
- **Screen analysis:** The extension periodically captures the visible screen content, calculates a change score to avoid redundant captures, and uploads changed frames to `POST /api/meetings/{id}/screen/analyze`. The backend runs Tesseract OCR to extract text, identifies content types (plain text, charts, tables), and stores structured observations.

### 3. User Annotations

At any point during the meeting, the user can click a "Mark Important" button in the widget. The extension captures the current transcript context and screen context and sends them along with the user's label and optional note to `POST /api/meetings/{id}/important-points`.

### 4. Report Generation

After the meeting is stopped, the user triggers report generation. The backend:
1. Fetches all transcripts, screen text entries, and important points for the meeting.
2. Constructs a comprehensive prompt with all the meeting data.
3. Sends the prompt to the configured AI provider.
4. Parses the AI response into structured fields: summary, insights, decisions, tasks, deadlines, graph insights, recommendations, and uncertain information.
5. Stores the generated report in MongoDB.

The user can then view and edit the report directly in the extension UI.

### 5. Export

The user can export the final report as a `.docx` Word document via `GET /api/meetings/{id}/export/docx`. The backend uses `python-docx` to generate a professionally formatted document with sections for each report field and serves it as a downloadable binary file.
