# SSE Streaming Application

A full-stack application demonstrating Server-Sent Events (SSE) for real-time data streaming.

## Project Structure

```
streaming-ui/
├── server/          # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI application
│   │   ├── config.py     # Configuration
│   │   ├── database.py   # Oracle & Redis connections
│   │   └── streaming.py  # SSE streaming logic
│   ├── pyproject.toml    # Poetry dependencies
│   └── .env.example      # Environment variables template
│
└── front/           # Next.js frontend
    ├── src/
    │   ├── app/          # Next.js app router
    │   ├── components/   # React components
    │   └── hooks/        # Custom hooks (useSSE)
    ├── package.json      # pnpm dependencies
    └── .env.example      # Environment variables template
```

## Tech Stack

### Backend (server/)
- Python FastAPI
- SSE (sse-starlette)
- Oracle Database (oracledb)
- Redis
- Poetry (dependency management)

### Frontend (front/)
- Next.js 15
- TypeScript
- shadcn/ui
- Tailwind CSS
- pnpm (package manager)

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Node.js 18+
- Poetry
- pnpm
- Oracle Database (optional)
- Redis (optional)

### 2. Backend Setup

```bash
cd server

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
poetry run python run.py
```

The API will be available at http://localhost:8000

### 3. Frontend Setup

```bash
cd front

# Install pnpm
npm install -g pnpm

# Install dependencies
pnpm install

# Configure environment
cp .env.example .env.local

# Run development server
pnpm dev
```

The UI will be available at http://localhost:3000

## API Endpoints

### Server Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /stream/counter` - Counter stream
- `GET /stream/timestamp` - Timestamp stream
- `GET /stream/database` - Oracle database stream
- `GET /stream/redis/{channel}` - Redis pub/sub stream
- `POST /publish/{channel}` - Publish to Redis channel

## Features

1. **Multiple Stream Types**
   - Counter stream - Simple incrementing counter
   - Timestamp stream - Real-time server time
   - Database stream - Data from Oracle database
   - Redis stream - Pub/sub messaging

2. **Real-time UI**
   - Live connection status indicators
   - Start/Stop streaming controls
   - Message history with clear functionality
   - Responsive card-based layout

3. **Custom SSE Hook**
   - Easy-to-use React hook for SSE connections
   - Automatic connection management
   - Error handling
   - TypeScript support

## Development

### Backend Development

```bash
cd server

# Run with auto-reload
poetry run python run.py

# Format code
poetry run black .
poetry run ruff check .

# Run tests
poetry run pytest
```

### Frontend Development

```bash
cd front

# Development mode
pnpm dev

# Build for production
pnpm build

# Run production build
pnpm start

# Lint
pnpm lint
```

## Configuration

### Backend (.env)

```env
HOST=0.0.0.0
PORT=8000

ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=localhost:1521/XEPDB1

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage Example

1. Start the backend server
2. Start the frontend application
3. Open http://localhost:3000
4. Click "Start" on any streaming card
5. Watch real-time data updates

## Notes

- The Oracle and Redis connections are optional. The server will start even if these services are not available.
- For production use, ensure proper error handling and security measures are in place.
- Update CORS settings in the backend for production deployments.

## License

MIT
