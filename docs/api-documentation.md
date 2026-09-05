# VoxVision AI — API Documentation

## Introduction

The VoxVision AI backend exposes a RESTful API built with **FastAPI** that powers the VoxVision Chrome Extension. It handles meeting lifecycle management, real-time transcript ingestion, screen content analysis via OCR, user-marked important points, AI-powered report generation (via Gemini, OpenAI, OpenRouter, or a Demo provider), and Word document export.

All endpoints accept and return **JSON** unless otherwise noted (e.g., multipart upload for screen analysis, binary `.docx` download for export).

---

## Base URL

| Environment | URL |
|---|---|
| Local development | `http://localhost:8000` |

> [!NOTE]
> The base URL may change depending on your deployment configuration. All endpoint paths below are relative to this base URL.

---

## Authentication

**No authentication is currently required.** All endpoints are publicly accessible. If you plan to deploy VoxVision in a production environment, you should add an authentication layer (e.g., API keys, OAuth 2.0, or JWT tokens) in front of the API.

---

## Endpoint Reference

### Health & Info

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check with database connectivity status |
| `GET` | `/` | Root endpoint returning basic API info |

#### `GET /health`

Returns the health status of the API and its database connection.

**Response `200 OK`**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### `GET /`

Returns basic information about the API.

**Response `200 OK`**
```json
{
  "name": "VoxVision AI",
  "version": "1.0.0",
  "description": "AI-powered meeting assistant backend"
}
```

---

### Meetings

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/meetings` | Create a new meeting |
| `GET` | `/api/meetings` | List all meetings |
| `GET` | `/api/meetings/{id}` | Get a specific meeting by ID |
| `PATCH` | `/api/meetings/{id}` | Update meeting title or status |
| `POST` | `/api/meetings/{id}/pause` | Pause a running meeting |
| `POST` | `/api/meetings/{id}/resume` | Resume a paused meeting |
| `POST` | `/api/meetings/{id}/stop` | Stop a meeting |
| `DELETE` | `/api/meetings/{id}` | Delete a meeting and all associated data |

#### `POST /api/meetings`

Create a new meeting session.

**Request Body**
```json
{
  "title": "Sprint Planning Q3",
  "selected_mode": "detailed",
  "audio_mode": "webspeech",
  "audio_enabled": true,
  "screen_analysis_enabled": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes | Human-readable meeting title |
| `selected_mode` | `string` | Yes | Report generation mode (e.g., `"detailed"`, `"concise"`) |
| `audio_mode` | `string` | No | Audio capture mode (e.g., `"webspeech"`) |
| `audio_enabled` | `boolean` | No | Whether audio capture is enabled |
| `screen_analysis_enabled` | `boolean` | No | Whether screen OCR analysis is enabled |

**Response `201 Created`**
```json
{
  "id": "664f1a2b3c...",
  "title": "Sprint Planning Q3",
  "platform": "google_meet",
  "selected_mode": "detailed",
  "status": "active",
  "audio_mode": "webspeech",
  "audio_enabled": true,
  "screen_analysis_enabled": true,
  "started_at": "2026-07-18T10:00:00Z",
  "ended_at": null
}
```

#### `GET /api/meetings`

List all meetings, ordered by most recent first.

**Response `200 OK`**
```json
[
  {
    "id": "664f1a2b3c...",
    "title": "Sprint Planning Q3",
    "status": "active",
    "started_at": "2026-07-18T10:00:00Z",
    "ended_at": null
  }
]
```

#### `GET /api/meetings/{id}`

Retrieve full details for a specific meeting.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `id` | `string` | MongoDB ObjectId of the meeting |

**Response `200 OK`**
```json
{
  "id": "664f1a2b3c...",
  "title": "Sprint Planning Q3",
  "platform": "google_meet",
  "selected_mode": "detailed",
  "status": "active",
  "audio_mode": "webspeech",
  "audio_enabled": true,
  "screen_analysis_enabled": true,
  "started_at": "2026-07-18T10:00:00Z",
  "ended_at": null
}
```

#### `PATCH /api/meetings/{id}`

Update a meeting's title or status.

**Request Body**
```json
{
  "title": "Updated Meeting Title",
  "status": "paused"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | No | New meeting title |
| `status` | `string` | No | New status value |

**Response `200 OK`** — Returns the updated meeting object.

#### `POST /api/meetings/{id}/pause`

Pause an active meeting. No request body required.

**Response `200 OK`**
```json
{
  "message": "Meeting paused",
  "status": "paused"
}
```

#### `POST /api/meetings/{id}/resume`

Resume a paused meeting. No request body required.

**Response `200 OK`**
```json
{
  "message": "Meeting resumed",
  "status": "active"
}
```

#### `POST /api/meetings/{id}/stop`

Stop a meeting and finalize it. No request body required.

**Response `200 OK`**
```json
{
  "message": "Meeting stopped",
  "status": "stopped"
}
```

#### `DELETE /api/meetings/{id}`

Delete a meeting and **all** associated child records (transcripts, screen text, important points, reports).

**Response `200 OK`**
```json
{
  "message": "Meeting and all associated data deleted"
}
```

---

### Transcripts

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/meetings/{id}/transcripts` | Add a single transcript entry |
| `POST` | `/api/meetings/{id}/transcripts/batch` | Add multiple transcript entries at once |
| `GET` | `/api/meetings/{id}/transcripts` | List all transcripts for a meeting |

#### `POST /api/meetings/{id}/transcripts`

Add a single transcript entry to a meeting.

**Request Body**
```json
{
  "text": "Let's start with the sprint backlog review.",
  "is_final": true,
  "source": "webspeech"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | `string` | Yes | Transcribed speech text |
| `is_final` | `boolean` | No | Whether this is a finalized transcript segment (default: `false`) |
| `source` | `string` | No | Source of the transcript (e.g., `"webspeech"`, `"manual"`) |

**Response `201 Created`** — Returns the created transcript object.

#### `POST /api/meetings/{id}/transcripts/batch`

Add multiple transcript entries in a single request. Useful for buffered ingestion from the extension.

**Request Body**
```json
{
  "items": [
    { "text": "First item of discussion.", "source": "webspeech" },
    { "text": "Moving on to the next topic.", "source": "webspeech" }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `items` | `array` | Yes | Array of transcript objects |
| `items[].text` | `string` | Yes | Transcribed text |
| `items[].source` | `string` | No | Source identifier |

**Response `201 Created`** — Returns the list of created transcript objects.

#### `GET /api/meetings/{id}/transcripts`

Retrieve all transcripts for a meeting.

**Response `200 OK`**
```json
[
  {
    "id": "665a1b...",
    "meeting_id": "664f1a2b3c...",
    "text": "Let's start with the sprint backlog review.",
    "source": "webspeech",
    "is_final": true,
    "processed": false
  }
]
```

---

### Screen Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/meetings/{id}/screen/analyze` | Upload a screenshot for OCR analysis |
| `GET` | `/api/meetings/{id}/screen-text` | List all extracted screen text entries |

#### `POST /api/meetings/{id}/screen/analyze`

Upload a screenshot image for OCR text extraction and analysis. The backend identifies content type (text, chart, table, etc.) and extracts structured data.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `file` | Yes | Screenshot image file (PNG, JPEG) |

**Query Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `change_score` | `float` | No | A score (0–1) indicating how much the screen has changed since the last capture |

**Response `200 OK`**
```json
{
  "id": "665b2c...",
  "meeting_id": "664f1a2b3c...",
  "extracted_text": "Q3 Revenue: $2.4M",
  "content_type": "chart",
  "chart_type": "bar",
  "parsed_values": { "Q3 Revenue": 2400000 },
  "basic_observation": "Bar chart showing Q3 revenue at $2.4M",
  "confidence": 0.92,
  "change_score": 0.85,
  "frame_stored": false
}
```

#### `GET /api/meetings/{id}/screen-text`

Retrieve all screen text entries extracted during the meeting.

**Response `200 OK`** — Returns an array of screen text objects.

---

### Important Points

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/meetings/{id}/important-points` | Mark a moment as important |
| `GET` | `/api/meetings/{id}/important-points` | List all important points |

#### `POST /api/meetings/{id}/important-points`

Mark a moment during the meeting as important. The user can attach a label, a personal note, and contextual data from the transcript or screen at that point in time.

**Request Body**
```json
{
  "label": "Key Decision",
  "user_note": "Team agreed to postpone feature X to Q4",
  "transcript_context": "We'll push feature X to next quarter...",
  "screen_context": "Slide: Q3 Roadmap Adjustments"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | `string` | Yes | Short label for the important point |
| `user_note` | `string` | No | Optional note from the user |
| `transcript_context` | `string` | No | Snapshot of the transcript at the time of marking |
| `screen_context` | `string` | No | Snapshot of the screen content at the time of marking |

**Response `201 Created`** — Returns the created important point object.

#### `GET /api/meetings/{id}/important-points`

Retrieve all important points marked during the meeting.

**Response `200 OK`** — Returns an array of important point objects.

---

### Reports

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/meetings/{id}/reports/generate` | Generate an AI-powered meeting report |
| `GET` | `/api/meetings/{id}/report` | Retrieve the generated report |
| `PUT` | `/api/meetings/{id}/report` | Update/edit the report |

#### `POST /api/meetings/{id}/reports/generate`

Trigger AI report generation for a meeting. The backend collects all transcripts, screen text, and important points, then sends them to the configured AI provider (Gemini, OpenAI, OpenRouter, or Demo) for structured report generation.

**Request Body** — None required. The backend uses the meeting's `selected_mode` and server-configured AI provider.

**Response `200 OK`**
```json
{
  "id": "665c3d...",
  "meeting_id": "664f1a2b3c...",
  "mode": "detailed",
  "provider": "gemini",
  "notes": "Comprehensive meeting notes...",
  "summary": "The team discussed Q3 priorities...",
  "insights": ["Revenue is tracking 15% above target"],
  "decisions": ["Postpone feature X to Q4"],
  "tasks": ["Update roadmap by Friday"],
  "deadlines": ["2026-07-25: Roadmap update"],
  "graph_insights": ["Bar chart shows steady growth"],
  "recommendations": ["Allocate more resources to feature Y"],
  "uncertain_information": ["Exact budget figure was unclear"]
}
```

#### `GET /api/meetings/{id}/report`

Retrieve the generated report for a meeting.

**Response `200 OK`** — Returns the full report object (same schema as above).

#### `PUT /api/meetings/{id}/report`

Update or edit a previously generated report. Users can modify any report field after generation.

**Request Body** — Partial or full report object with the fields to update.

```json
{
  "summary": "Updated summary text...",
  "tasks": ["Updated task list"]
}
```

**Response `200 OK`** — Returns the updated report object.

---

### Export

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/meetings/{id}/export/docx` | Download the meeting report as a Word document |

#### `GET /api/meetings/{id}/export/docx`

Export the meeting report as a downloadable `.docx` Word document.

**Response `200 OK`**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- **Content-Disposition:** `attachment; filename="meeting_report.docx"`
- **Body:** Binary `.docx` file

---

## Error Response Format

All error responses follow a consistent JSON structure:

```json
{
  "detail": "Description of what went wrong"
}
```

### Common HTTP Status Codes

| Status Code | Meaning | When It Occurs |
|---|---|---|
| `400 Bad Request` | Invalid request body or parameters | Malformed JSON, missing required fields, invalid field values |
| `404 Not Found` | Resource does not exist | Invalid meeting ID, no report generated yet |
| `422 Unprocessable Entity` | Validation error | Request body fails FastAPI/Pydantic validation |
| `500 Internal Server Error` | Server-side failure | Database errors, AI provider failures, unexpected exceptions |

### Validation Error Response (422)

FastAPI returns detailed validation errors with field-level information:

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## CORS Configuration

The API is configured with **permissive CORS** settings to allow the Chrome Extension to communicate with the backend during development:

| Setting | Value |
|---|---|
| **Allowed Origins** | `*` (all origins) |
| **Allowed Methods** | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS` |
| **Allowed Headers** | `*` (all headers) |
| **Allow Credentials** | `false` |

> [!WARNING]
> The current CORS configuration allows requests from **any origin**. Before deploying to production, restrict `allowed_origins` to your specific Chrome Extension ID and any trusted domains:
> ```python
> origins = [
>     "chrome-extension://your-extension-id",
>     "https://your-production-domain.com"
> ]
> ```

---

## Rate Limiting

No rate limiting is currently enforced. For production deployments, consider adding rate limiting middleware to protect against abuse, especially on the report generation and screen analysis endpoints which involve external API calls and image processing.

---

## Notes for Extension Developers

1. **Meeting lifecycle:** Always create a meeting (`POST /api/meetings`) before sending transcripts or screen captures.
2. **Batch transcripts:** Prefer the batch endpoint (`POST .../transcripts/batch`) over individual transcript posts to reduce network overhead during active meetings.
3. **Screen analysis:** Only send screenshots when the screen content has meaningfully changed. Use the `change_score` parameter to help the backend decide whether to process the frame.
4. **Report generation:** Reports can only be generated once a meeting has sufficient data. Ensure transcripts and/or screen text have been captured before triggering generation.
5. **Export:** The export endpoint requires a report to exist for the meeting. Generate the report first, then export.
