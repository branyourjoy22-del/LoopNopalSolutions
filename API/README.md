# API

Starter FastAPI backend for future simulation integrations.

Run locally:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

