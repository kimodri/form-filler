# CFG – Context-Free Generator  
**Automated Form and Document Generation from User Input Using Context-Free Grammar (CFG)**

---

## Overview

CFG (Context-Free Generator) is a Python-based web application that automates the generation and filling of forms and documents from user input using context-free grammar (CFG) techniques.

The project integrates OCR (Tesseract), PDF rendering (Poppler), and computer vision tools to extract, analyze, and populate document structures. It is designed to run consistently across operating systems by encapsulating all system-level dependencies inside Docker.

---

## Prerequisites

### Required
- Docker (Docker Desktop on Windows/macOS, Docker Engine on Linux)

### Optional (for local, non-Docker execution)
- Python 3.13+
- Tesseract OCR
- Poppler
- OpenCV system dependencies

> Docker is **strongly recommended** to avoid OS-specific setup issues.

---

## Project Structure (Simplified)

```

.
├── server/
│   └── app.py
├── templates/
│   └── index.html
├── static/
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Running with Docker (Recommended)

### 1. Build the image

```bash
docker build -t form-filler .
```

### 2. Run the container

```bash
docker run -p 5000:5000 form-filler
```

### 3. Open in browser

```
http://127.0.0.1:5000
```

The Flask app runs inside the container with all native dependencies preinstalled.

---

## Notes on Cross-Platform Compatibility

* **Windows, macOS, Linux** users can all run the application using Docker without modifying paths or environment variables.
* Tesseract and Poppler binaries are installed **inside the container**, so no `.env` path configuration is required.
* The application resolves template and static paths relative to the source file, not the working directory, ensuring consistent behavior inside and outside Docker.

---

## Development Notes

* Flask runs in **debug mode** by default inside the container.
* The container exposes port `5000`.
* `.env`, `.venv`, and local system binaries should be excluded via `.dockerignore`.

Example `.dockerignore`:

```
.venv/
.env
__pycache__/
poppler/
```

---

## Local (Non-Docker) Execution (Optional)

If running without Docker, ensure the following are installed and available in your system PATH:

1. Python 3.13+
2. Tesseract OCR
3. Poppler
4. OpenCV dependencies

Then:

```bash
pip install -r requirements.txt
python server/app.py
```

---

## `.env` Configuration Note (Local Development Only)

When running the application **without Docker** on Windows, certain OCR and PDF utilities require explicit binary paths. These are configured using a `.env` file.

Example `.env` (Windows only):

```env
POPPLER_PATH=C:\Users\you\your_repo\poppler\poppler-25.12.0\Library\bin
PYTESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
````

### Important Notes

* These variables are **not required when running via Docker**.
* Inside Docker, Poppler and Tesseract are installed system-wide and resolved automatically.
* The `.env` file should **not be committed** and must be included in `.dockerignore`.

```
.env
```

* macOS and Linux users typically do **not** need these variables if the binaries are installed via package managers and available in `PATH`.

---


---

## Disclaimer

This project uses Flask’s built-in development server.
Do **not** use it as-is in production without a proper WSGI server.

---

## License

Specify license here (MIT, Apache 2.0, etc.).

