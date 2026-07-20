# SipSetu — Run Doc

## How to reproduce artifacts

No `.env` or build artifacts are needed beyond what `npm install` provides.

## How to run the dev server

### Frontend (Vite dev server)

```bash
cd frontend
npm install
npx vite --host 0.0.0.0 --port 5173
```

The frontend starts at **http://localhost:5173**.

### Backend (Flask API)

```bash
cd backend
python -m venv venv
# Windows:
.\\venv\\Scripts\\activate
pip install -r requirements.txt

# Ensure PostgreSQL is running and the sipsetu database exists,
# then start the Flask server:
python app.py
```

The backend starts at **http://127.0.0.1:5000**.

**Note:** The frontend works standalone for UI preview, but API calls require the backend with PostgreSQL.
