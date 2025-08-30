# Streamlit User App Deployment Guide

This directory contains the **Streamlit** front-end for TheraCompass end users.
The app communicates with the FastAPI backend to manage accounts, patients and
session analytics. The instructions below explain how to deploy *only* this
user-facing app.

## Required Files

To run the app outside of this repository, copy the following pieces into your
new project:

- `app.py` and all other modules in this folder (`account_page.py`,
  `api_client.py`, `home_page.py`, `login.py`, `markdown_loader.py`,
  `patient_page.py`, `session_page.py`, `styles.py`).
- The `markdown/` directory with the markdown templates.
- `emanuense/firebase_handler.py` and `emanuense/logging_utils.py` (for
  authentication and logging).

## Dependencies

Install the runtime packages used by the app:

```bash
pip install streamlit streamlit-extras requests python-dotenv firebase-admin altair
```

## Environment Variables

The app expects a number of settings provided through environment variables or
Streamlit secrets:

| Variable | Purpose |
|----------|---------|
| `DEPLOYED_URL` | Base URL of the backend API (default `http://localhost:8000`). |
| `FIREBASE_API_KEY` | Firebase API key for authentication. |
| `FIREBASE_CREDENTIALS` | Path or JSON for a Firebase service account. |
| `FIREBASE_PROJECT_ID` / `GOOGLE_CLOUD_PROJECT` | Firebase project identifier. |
| `MODE` | Set to `demo` to enable the built‑in sample audio selector. |
| `TEST_AUDIO_DIR` | Directory holding audio files when `MODE=demo`. |
| `LOG_DIR` | (Optional) directory for log files used by `dashboard.py`. |
| `DEPLOYED` | Set to `TRUE` to log only to stdout. |

## Running Locally

1. Ensure the backend API is reachable at `DEPLOYED_URL`.
2. Export the environment variables above or define them as Streamlit secrets.
3. Install the dependencies.
4. Start the app:

   ```bash
   streamlit run src/emanuense/streamlit_user/app.py
   ```

## Deploying on Streamlit Community Cloud

1. Create a new repository containing the files listed in **Required Files** and
   a `requirements.txt` with the dependencies from above.
2. In the Streamlit Cloud project settings, configure the environment variables
   under **Secrets**.
3. Set the app entry point to `src/emanuense/streamlit_user/app.py`.

## Deploying with Docker

A minimal `Dockerfile` can be used to package the app:

```Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["streamlit", "run", "src/emanuense/streamlit_user/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run the container:

```bash
docker build -t theracompass-streamlit .
docker run -p 8501:8501 --env-file .env theracompass-streamlit
```

The app will be available at `http://localhost:8501`.
