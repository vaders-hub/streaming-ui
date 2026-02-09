# SSE Streaming Server

FastAPI server with Server-Sent Events (SSE), Oracle Database, and Redis support.

## Features

- FastAPI web framework
- Server-Sent Events (SSE) streaming
- Oracle Database integration
- Redis pub/sub support
- Poetry dependency management

## Prerequisites

- Python 3.10+
- Poetry
- Oracle Database
- Redis

## Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
cd server
poetry install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run the server:
```bash
poetry run python run.py
```

Or activate the virtual environment:
```bash
poetry shell
python run.py
```

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `GET /stream/{stream_type}` - SSE stream endpoint (counter, timestamp, custom)
- `GET /stream/database` - Stream data from Oracle database
- `GET /stream/redis/{channel}` - Stream data from Redis pub/sub
- `POST /publish/{channel}` - Publish message to Redis channel

## Development

Run with auto-reload:
```bash
poetry run python run.py
```

Format code:
```bash
poetry run black .
poetry run ruff check .
```

Run tests:
```bash
poetry run pytest
```

## Oracle schema snapshot (Method A)

To dump Oracle schema/table metadata using the server virtualenv (`oracledb`) and `server/.env`:

```bash
cd server
poetry run python tools/schema_dump.py
```

This will generate `server/schema_snapshot.md`.

## Environment Variables

See `.env.example` for all available configuration options.
