# Backend - Event Second Brain

This directory contains the backend service and database logic for **Event Second Brain – Agentic Workflow Automation & Context Engineering**.

---

## Getting Started

### 1. Create a Virtual Environment

Navigate to the `backend` folder:
```bash
cd backend
```

Create a virtual environment named `venv`:
- **Windows (PowerShell or Command Prompt):**
  ```powershell
  python -m venv venv
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  ```

---

### 2. Activate the Virtual Environment

- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` first, or use Command Prompt: `.\venv\Scripts\activate.bat`)*

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

When active, your terminal prompt will show `(venv)`.

---

### 3. Install Dependencies

With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

To deactivate the virtual environment when done:
```bash
deactivate
```

---

## Run the Server

1. Open a terminal and navigate to the `backend` folder:
   ```bash
   cd backend
   ```

2. Activate the virtual environment:
   - **Windows:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. Start the Uvicorn development server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Verify the endpoints in your browser or with curl:
   - **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) (returns `{"status": "ok"}`)
   - **Interactive API Docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

