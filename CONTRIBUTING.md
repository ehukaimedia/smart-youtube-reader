# Contributing to Smart YouTube Reader

Thank you for your interest in contributing to Smart YouTube Reader! We welcome contributions from the community to help make this local-first video reading tool even better.

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### Reporting Bugs
If you find a bug, please check the existing issues to see if it has already been reported. If not, open a new issue using our Bug Report template. Please include:
* A clear description of the issue.
* Steps to reproduce the bug.
* Expected and actual behavior.
* Environment details (OS, Python version, Node.js version, hardware specifications).

### Requesting Features
We welcome ideas for new features or improvements. Please check existing issues/discussions, then open a new issue using our Feature Request template. Describe the goal and use case of the feature.

### Submitting Pull Requests
1. **Fork the repository** and create your branch from `main`.
2. **Setup your environment** (see [Development Setup](#development-setup) below).
3. **Write tests** for backend changes and ensure frontend modifications pass lint and build checks.
4. **Follow code style** and project structure guidelines.
5. **Open a Pull Request (PR)** against the `main` branch. Use our PR template to explain your changes, what tests you ran, and the impact of the changes.

---

## Development Setup

Smart YouTube Reader consists of a FastAPI backend and a Next.js frontend.

### Prerequisites
* **macOS** (Apple Silicon recommended for `mlx-vlm` local model execution).
* **FFmpeg** (installed via `brew install ffmpeg`).
* **Python 3.10+** and **Node.js 18+**.

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies (including development/testing tools):
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
4. Run tests to verify the setup:
   ```bash
   python3 -m pytest
   ```
5. Run the dev server:
   ```bash
   uvicorn app.main:app --reload --port 8001
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run lint checks and build:
   ```bash
   npm run lint
   ```
4. Build the application to verify:
   ```bash
   npm run build
   ```
5. Start the dev server:
   ```bash
   npm run dev -- --port 3001
   ```

---

## Code Style & Standards

* **Python (Backend)**: Follow PEP 8 guidelines. Write clean, descriptive code and document your functions/modules. Keep tests updated in `backend/tests/`.
* **TypeScript / React (Frontend)**: Write clean, component-driven React. Ensure components are reusable and modular.
* **Local-First Architecture**: Smart YouTube Reader is designed to run locally. Avoid introducing cloud databases or SaaS dependencies. Local files are the source of truth.
