VoxVision AI

VoxVision AI is an intelligent meeting-assistance system that helps users capture, understand, and document online meetings. It combines a Chrome extension with a Python/FastAPI backend, MongoDB persistence, OCR processing, and configurable AI providers.

During a supported Google Meet session, VoxVision can collect meeting speech or transcript text, visible screen text, and important discussion points. The backend cleans and organizes this information, detects duplicate content, generates summaries and insights, and exports professional PDF or Word reports.

VoxVision is an assistance and documentation tool. It does not replace human judgment, meeting consent, or organizational privacy policies.

Features

Chrome extension interface for meeting assistance

Google Meet session detection and widget injection

Capture of visible meeting text and screen changes

OCR processing for text visible on the screen

Meeting transcript and screen-text storage

Important-point extraction

Duplicate-content detection and text cleaning

AI-generated meeting summaries and insights

Configurable AI providers:

OpenAI

Google Gemini

OpenRouter

Ollama for local inference

Demo provider for development and offline testing

MongoDB persistence for meetings, transcripts, reports, and extracted information

PDF report export

Word document export

Chart and summary generation

REST API for communication between the extension and backend

Health-check endpoint for local and deployed environments

Automated backend and extension tests

Provider abstraction so AI services can be changed without rewriting the application

How it works

flowchart LR
    A[Google Meet] --> B[Chrome Extension]
    B --> C[FastAPI Backend]
    C --> D[OCR and Text Processing]
    D --> E[AI Provider]
    E --> F[MongoDB]
    F --> G[Summary and Reports]
    G --> B

Main data flow

The Chrome extension detects a supported meeting page.

The extension captures permitted meeting text, screen text, and session events.

Data is sent to the FastAPI backend through REST endpoints.

The backend validates, cleans, normalizes, and deduplicates the content.

OCR is used when text must be read from a visible screen region.

The configured AI provider generates summaries, insights, or structured reports.

MongoDB stores meeting data and report information.

The extension requests the processed results and displays them to the user.

Users can export supported results as PDF or Word documents.

Architecture

VoxVision AI
├── extension/                 Chrome extension and meeting widget
│   ├── background/             Background service worker
│   ├── content/                Content scripts and meeting detection
│   ├── icons/                  Extension icons
│   ├── widget/                 Widget styling
│   └── manifest.json           Chrome Manifest configuration
├── backend/                   FastAPI backend
│   ├── database/               MongoDB connection and persistence helpers
│   ├── models/                 Typed data models
│   ├── routes/                 REST API route modules
│   ├── services/               OCR, AI, reports, charts, exports, and cleaning
│   ├── prompts/                AI prompt templates
│   ├── config.py               Environment-backed configuration
│   └── main.py                 FastAPI application entry point
├── docs/                      Project and API documentation
├── scripts/                   Development and startup scripts
├── tests/
│   ├── backend/                Python backend tests
│   └── extension/              JavaScript extension tests
├── .env.local                 Local-only environment variables (never commit)
├── backend/.env.example       Backend environment template
├── LICENSE                    Project license
└── README.md                  This file

Technology stack

Extension

JavaScript

Chrome Extension Manifest V3

Content scripts

Background service worker

DOM observation and page-event handling

Backend

Python 3.11 or newer recommended

FastAPI

Uvicorn

Pydantic

PyMongo or the repository's configured MongoDB client

Requests and HTTP client utilities

OCR processing libraries configured in backend/requirements.txt

ReportLab or the configured PDF library

Python document-generation library for Word export

Data and AI

MongoDB local instance or MongoDB Atlas

OpenAI, Gemini, OpenRouter, or Ollama

Environment-based provider selection

Mock and demo providers for tests and offline development

Prerequisites

Install the following before running VoxVision:

Git

Python 3.11+

Google Chrome or Chromium

MongoDB Community Server locally, or a MongoDB Atlas connection string

Node.js only if you run JavaScript extension tests or additional frontend tooling

An API key only for the AI provider you intend to use

You do not need every AI provider key. Ollama or the demo provider can be used for local development when supported by the current configuration.

Clone the repository

git clone https://github.com/yashsantoshchougule/voxvision.git
cd voxvision

Backend setup on Windows PowerShell

Create and activate a virtual environment:

py -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

Install dependencies:

python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

Create the local environment file from the example:

Copy-Item backend\.env.example backend\.env

Open backend\.env and set the variables required by the current backend/config.py. Use the exact variable names from that file and from backend/.env.example.

Start the backend:

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

If the repository's scripts/start-backend.ps1 contains the preferred startup command, use that script instead:

.\scripts\start-backend.ps1

The interactive API documentation is normally available at:

http://127.0.0.1:8000/docs

The exact port and route prefix should always be confirmed from backend/main.py and the environment configuration.

MongoDB configuration

VoxVision supports either a local MongoDB instance or MongoDB Atlas.

Example local connection format:

mongodb://localhost:27017

For MongoDB Atlas, use the connection string supplied by Atlas and keep it only in the backend environment file. Do not place the connection string in extension code, browser storage, Git commits, screenshots, or public documentation.

Recommended development checks:

Confirm MongoDB is running.

Confirm the database name configured in backend/config.py.

Start the backend.

Open the health endpoint or /docs.

Trigger one test request before loading the extension.

AI provider configuration

The project contains a provider abstraction and can select an AI implementation through configuration. Configure only the provider you are authorized to use.

Typical provider settings may include:

Setting

Purpose

AI_PROVIDER

Selects the active provider, such as demo, ollama, openai, gemini, or openrouter

OPENAI_API_KEY

OpenAI authentication, if OpenAI is selected

GEMINI_API_KEY

Gemini authentication, if Gemini is selected

OPENROUTER_API_KEY

OpenRouter authentication, if OpenRouter is selected

OLLAMA_BASE_URL

Local Ollama server URL, if Ollama is selected

OLLAMA_MODEL

Local model name, if required by the provider

The authoritative variable names are the ones defined in the repository's environment example and configuration modules. Do not add guessed names if the project already defines a convention.

Local Ollama example

If the project is configured for Ollama:

ollama list
ollama serve

Then set the model name in the backend environment file according to the model installed on your machine.

Protecting API keys

Keep secrets in ignored environment files.

Never commit .env, .env.local, API tokens, MongoDB URIs, cookies, or service-role keys.

Use .env.example files with blank placeholders only.

Rotate a key immediately if it was committed, pasted into a public issue, or exposed in a screenshot.

Check Git history before pushing changes.

Load the Chrome extension

Start the backend and confirm it is healthy.

Open Chrome and navigate to:

chrome://extensions

Enable Developer mode.

Select Load unpacked.

Choose the repository's extension directory.

Open a supported Google Meet page.

Confirm the extension is enabled and inspect the extension service-worker console if the widget does not appear.

If the extension expects a backend URL, configure the URL using the repository's existing configuration convention. Do not hardcode production credentials or private endpoints in extension/.

API areas

The backend route modules currently cover areas such as:

Health checks

Meeting lifecycle and meeting data

Transcript data

Screen-text data

Important points

AI-generated reports

Export operations

For exact paths, request and response bodies, authentication requirements, and status codes, see:

docs/api-documentation.md

backend/routes/

backend/models/

Do not assume an endpoint path from this README if it differs from the current source code.

Testing

Activate the virtual environment first:

& ".\.venv\Scripts\Activate.ps1"

Run backend tests:

python -m pytest

Run a focused backend test module:

python -m pytest tests/backend/test_api.py -q

Run extension tests when the repository's Node test setup is available:

node --test tests/extension/*.test.js

Normal tests should use mocks and fixtures. They should not call paid AI providers, MongoDB production databases, Google Meet, or live external services.

Development guidelines

Keep route handlers thin; place business logic in services.

Validate all external input with Pydantic or the repository's existing validation layer.

Keep AI provider-specific code behind the provider interface.

Return stable API response shapes.

Add tests when changing models, routes, providers, or report generation.

Avoid logging transcripts, API keys, MongoDB credentials, cookies, or personal meeting content unnecessarily.

Use bounded processing for transcript and OCR input.

Handle provider timeouts and rate limits gracefully.

Preserve a demo/offline path so the extension can be developed without paid API calls.

Privacy and responsible use

Meeting content can contain confidential or personal information. Before using VoxVision in a real meeting:

Obtain consent where required.

Follow organizational recording and monitoring policies.

Avoid processing sensitive meetings unless explicitly authorized.

Minimize stored data and define a retention period.

Secure MongoDB credentials and restrict database access.

Use HTTPS and authenticated API access in production.

Do not share generated reports publicly without permission.

Provide a way to delete meeting data when required.

VoxVision should process only the data needed for its stated meeting-assistance features. It should not collect unrelated browsing activity or private account information.

Troubleshooting

Backend does not start

Confirm the virtual environment is activated.

Run python -m pip install -r backend\requirements.txt again.

Check the exact import path in backend/main.py.

Confirm required environment variables exist without printing their values.

Check that the configured port is not already in use.

MongoDB connection fails

Confirm MongoDB is running or Atlas is reachable.

Verify the connection string and database name.

Check Atlas network access rules and database-user permissions.

Do not put the URI in extension code.

AI output is unavailable

Confirm AI_PROVIDER matches an implemented provider.

Confirm the selected provider key or local server is available.

Try the demo provider to separate application errors from provider errors.

Check backend logs for a redacted provider error.

Avoid retrying an invalid key repeatedly.

Extension does not appear

Confirm Developer mode and Load unpacked were used.

Reload the extension after changing files.

Confirm the page matches the manifest's allowed URL patterns.

Inspect the service-worker and content-script consoles.

Confirm the backend URL and CORS settings.

Check whether the current meeting page changed its DOM structure.

Reports are incomplete

Confirm the meeting contains enough captured text.

Check OCR quality and input size limits.

Inspect backend validation warnings.

Confirm the configured AI provider returned a complete response.

Use the stored meeting data and logs to identify whether the problem occurred during capture, processing, AI generation, or export.

Production considerations

Before deploying VoxVision:

Use HTTPS for frontend-extension-to-backend communication.

Add authentication and authorization for every protected API route.

Configure strict CORS origins rather than *.

Store secrets in a managed secret store.

Use a production MongoDB user with least-privilege access.

Add request rate limiting and payload-size limits.

Add structured logs and error monitoring without sensitive meeting content.

Configure backups and a retention/deletion policy.

Run tests and a production build in CI.

Pin and regularly review dependency versions.

Review Chrome Web Store policies and Google Meet usage requirements.

Obtain consent and document how meeting data is processed.

Roadmap

Improve meeting-platform compatibility beyond Google Meet

Add stronger live transcript synchronization

Add configurable retention and user-controlled deletion

Improve OCR for noisy or changing screen content

Add report templates for interviews, lectures, team meetings, and sales calls

Add authenticated multi-user workspaces

Add background processing for long meetings

Add more export formats

Add provider health dashboards and usage monitoring

Improve automated fixture coverage for extension DOM changes

Contributing

Create a feature branch.

Make a focused change.

Add or update tests.

Run the backend and extension test suites.

Check that no secrets or generated logs are staged.

Review the diff before committing.

Open a pull request with a clear description of the change and verification performed.

License

See the repository's LICENSE file for the applicable terms.

Project summary

VoxVision AI demonstrates how a browser extension, backend services, databases, OCR, and configurable AI providers can work together to transform meeting information into useful, structured documentation. The project is designed as an extensible foundation: capture modules, processing services, AI providers, storage models, and export formats can evolve independently as the system grows.
