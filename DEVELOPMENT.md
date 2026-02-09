# Development Guide

## Project Structure

```
streaming-ui/
├── front/               # Next.js frontend
│   ├── src/
│   │   ├── app/        # Next.js app router pages
│   │   ├── components/ # React components
│   │   ├── hooks/      # Custom React hooks (useSSE)
│   │   └── store/      # Zustand state management
│   └── package.json
├── server/             # FastAPI backend
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── core/       # Core configuration
│   │   ├── db/         # Database connections
│   │   └── services/   # Business logic
│   ├── .venv/          # Python virtual environment
│   └── pyproject.toml  # Python dependencies
└── .vscode/            # VS Code settings
```

## Python Development Setup

### Prerequisites

- Python 3.10+ (currently using 3.13)
- Poetry (Python package manager)

### Environment Setup

1. **Virtual Environment Location**
   - Path: `server/.venv/`
   - Created automatically by Poetry

2. **Install Dependencies**
   ```bash
   cd server
   poetry install
   ```

3. **Activate Virtual Environment**
   ```bash
   # Windows
   poetry shell

   # Or run commands directly
   poetry run python app/main.py
   poetry run serve  # Using the script defined in pyproject.toml
   ```

### Code Quality Tools

#### Black (Code Formatter)
- Line length: 100
- Formats code automatically on save (VS Code)
- Manual formatting:
  ```bash
  poetry run black app/
  ```

#### Ruff (Linter)
- Modern, fast Python linter
- Auto-fixes many issues
- Manual linting:
  ```bash
  poetry run ruff check app/
  poetry run ruff check app/ --fix  # Auto-fix
  ```

#### Flake8 (Legacy Linter)
- Still configured for compatibility
- Max line length: 100
- Ignores: E203, W503 (Black compatibility)

### VS Code Configuration

The project includes optimized VS Code settings:

**Interpreter**
- Location: `server/.venv/Scripts/python.exe`
- Auto-selected via `.vscode/settings.json`

**Features Enabled**
- Format on save (Black)
- Auto-organize imports
- Type checking (Pylance - basic mode)
- Auto-fix linting issues on save

**Testing**
- Framework: pytest
- Test directory: `server/tests/`
- Run via Testing panel or:
  ```bash
  poetry run pytest
  ```

### Pylance/Pyright Configuration

Configuration file: `pyrightconfig.json` (project root)

**Key Settings**
- Include: `server/app/`
- Virtual env: `server/.venv/`
- Type checking: Basic mode
- Reports: Missing imports, unused variables/imports

### Running the Server

```bash
# Development mode (with auto-reload)
cd server
poetry run serve

# Or with uvicorn directly
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

Create `.env` file in `server/` directory:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# OpenAI (for chat features)
OPENAI_API_KEY=sk-...

# Oracle Database (optional)
ORACLE_DSN=localhost:1521/XEPDB1
ORACLE_USER=your_user
ORACLE_PASSWORD=your_password

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Frontend Development Setup

### Prerequisites

- Node.js 18+ (currently using pnpm)
- pnpm (or npm/yarn)

### Install Dependencies

```bash
cd front
pnpm install
```

### Run Development Server

```bash
pnpm dev
```

### Environment Variables

Create `.env.local` in `front/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Code Style Guidelines

### Python

- **Line Length**: 100 characters
- **Imports**: Organized automatically (ruff/isort)
- **Formatting**: Black with 100 line length
- **Type Hints**: Encouraged for public APIs
- **Async**: Use `async def` for I/O operations

**Example:**
```python
from collections.abc import AsyncGenerator

async def stream_data(
    limit: int = 100,
) -> AsyncGenerator[dict[str, str], None]:
    """Stream data with proper type hints."""
    for i in range(limit):
        yield {"index": i, "data": f"item-{i}"}
```

### TypeScript/React

- **Line Length**: 100 characters
- **Indentation**: 2 spaces
- **Component Style**: Functional components with hooks
- **State Management**: Zustand for global state
- **Formatting**: Prettier (via Next.js defaults)

## Common Tasks

### Add Python Dependency

```bash
cd server
poetry add <package>           # Production dependency
poetry add --group dev <package>  # Development dependency
```

### Add Frontend Dependency

```bash
cd front
pnpm add <package>
pnpm add -D <package>  # Dev dependency
```

### Format All Code

```bash
# Python
cd server
poetry run black app/
poetry run ruff check app/ --fix

# Frontend (if configured)
cd front
pnpm format
```

### Run Tests

```bash
# Python
cd server
poetry run pytest

# Frontend
cd front
pnpm test
```

## Troubleshooting

### Python Import Errors in VS Code

1. Check Python interpreter is set to `server/.venv/Scripts/python.exe`
2. Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
3. Verify Pylance extension is installed
4. Check `pyrightconfig.json` paths are correct

### Linting Errors

1. Run auto-fix: `poetry run ruff check app/ --fix`
2. Run formatter: `poetry run black app/`
3. Check `pyproject.toml` for ruff/black configuration

### Poetry Issues

```bash
# Clear cache and reinstall
poetry cache clear . --all
poetry install

# Recreate virtual environment
poetry env remove python
poetry install
```

## Editor Configuration

The project includes `.editorconfig` for consistent coding styles across editors:
- Python: 4 spaces, 100 line length
- TypeScript/JavaScript: 2 spaces, 100 line length
- JSON/YAML: 2 spaces
- UTF-8 encoding, LF line endings
