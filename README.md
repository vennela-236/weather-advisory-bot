
# Weather Advisory Support Bot

A chatbot that checks weather conditions and provides safety guidance for different outdoor activities. It uses live data from Open-Meteo and follows predefined Standard Operating Procedures (SOPs) to decide what advice to give.

The backend is built with FastAPI, and LangGraph manages the flow from understanding a question to checking the weather and selecting an applicable SOP.

## Features

- Gets weather and location data from Open-Meteo.
- Identifies the activity, location, date, and time mentioned in a question.
- Checks the relevant SOPs against the weather conditions.
- Chooses the highest-severity SOP when more than one applies.
- Remembers relevant details during follow-up questions.
- Returns a no-match response when no SOP condition is met.
- Handles API failures without making up weather information.

## Tech Stack

- Python
- FastAPI
- LangGraph
- Open-Meteo Weather and Geocoding APIs
- HTML, CSS, JavaScript
- Pytest

## Project Structure

```text
Weather advisory bot/
├── backend/
│   ├── app/
│   │   ├── policies/
│   │   │   └── sops.json
│   │   └── ...
│   └── tests/
├── frontend/
├── .gitignore
├── EVALUATION.md
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd "Weather advisory bot"
```

### 2. Create a virtual environment

Run these commands in PowerShell from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the packages from the project's requirements file:

```powershell
pip install -r backend/requirements.txt
```

If the file is in a different folder, use its actual path.

## Run the Application

Start the backend and frontend in separate terminals.

### Backend

From the project root:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend will be available at `http://127.0.0.1:8000`.

### Frontend

Open another terminal in the project root and run:

```powershell
python -m http.server 5173 --directory frontend
```

Then open `http://localhost:5173` in your browser.

## Weather Data

The bot uses Open-Meteo for weather forecasts and geocoding. The endpoints used in this project do not require an API key.

The advice depends on the weather data returned for the requested location and time. If the service is unavailable, the bot reports the issue instead of generating weather details.

## SOPs

The SOPs are stored in `backend/app/policies/sops.json`.

Why JSON? It keeps the procedures structured and easy to add or update without changing the matching code.

Each SOP includes:

- `id`: A unique identifier
- `title`: Name of the procedure
- `category`: Type of procedure
- `severity`: Severity level
- `applies_to`: Activities the procedure covers
- `when`: Weather conditions that trigger it
- `advice`: Guidance to provide
- `reason`: Explanation for the rule

Conditions under `all` must all be met. If an `any` list is provided, at least one of those conditions must be met.

### Adding or Updating an SOP

You can add or edit SOPs directly in `sops.json`. The matching logic does not need to change, as long as the new entry follows the existing format and uses supported condition fields and operators.

## How SOP Matching Works

The bot follows a rule-based process:

1. It identifies the activity mentioned in the question.
2. It finds SOPs that apply to that activity.
3. It checks whether their weather conditions are met.
4. If multiple SOPs match, it selects the one with the highest severity.

The matcher also returns the list of matched SOPs and the strategy used to resolve conflicts (`highest_severity`).

If nothing matches, the bot returns a no-match response rather than making up safety advice.

## Follow-up Questions

LangGraph checkpointing is used to retain relevant session context. For example, if a user first asks about cycling in Bhopal and then asks, "What about this evening?", the bot can use the earlier location and activity.

## Tests and Evaluation

Run the automated tests from the `backend` directory:

```powershell
python -m pytest
```

The latest recorded test run had **13 passing tests**.

More details, including website checks and known limitations, are in [EVALUATION.md](EVALUATION.md).

## Limitations

- Weather information depends on the external service.
- A no-match response only means that no configured SOP was triggered. It does not guarantee that an activity is safe.
- Mocked tests do not confirm how the bot will behave during an actual severe-weather event.