# SQLAlchemy Database Improvements

This document describes the improvements made to the database connection and session management.

## Summary of Changes

We've refactored the SQLAlchemy implementation from manual session management to **FastAPI Dependency Injection** pattern, improving code quality, reliability, and maintainability.

---

## Before & After Comparison

### ❌ Before: Manual Session Management

```python
@router.post("/orders")
async def create_order(req: CreateOrderRequest):
    session = oracle_db.get_session()
    try:
        # ... database operations ...
        session.commit()
        return {"ok": True, ...}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    finally:
        session.close()  # Easy to forget!
```

**Problems:**
- Repetitive boilerplate code
- Risk of forgetting `session.close()` in finally block
- No separation between DB errors and business logic errors
- Async functions with sync DB operations (blocking)
- Manual error handling in every route

### ✅ After: Dependency Injection Pattern

```python
@router.post("/orders")
def create_order(
    req: CreateOrderRequest,
    db: Session = Depends(get_db),
):
    try:
        # ... database operations ...
        # Auto-commit on success
        # Auto-rollback on error
        # Auto-cleanup always
        return {"ok": True, ...}
    except Exception as e:
        raise handle_db_error(e) from e
```

**Benefits:**
- Clean, concise code
- Automatic session management
- Proper error handling
- No memory leaks
- Testable (can mock `get_db`)

---

## Key Improvements

### 1. Enhanced Connection Pool Settings

**File:** `server/app/db/connection.py`

```python
self.engine = create_engine(
    oracle_url,
    # Connection Pool Settings
    pool_pre_ping=True,       # Verify connections before use
    pool_size=5,              # Base pool size
    max_overflow=10,          # Max additional connections
    pool_recycle=3600,        # ✅ NEW: Recycle after 1 hour
    pool_timeout=30,          # ✅ NEW: Wait max 30s for connection
    echo_pool=False,          # ✅ NEW: Debug option
    # Query Settings
    echo=settings.debug,      # ✅ NEW: Log SQL in debug mode
)
```

**Benefits:**
- Prevents stale connections (`pool_recycle`)
- Avoids indefinite waits (`pool_timeout`)
- Better debugging capabilities

### 2. Context Manager for Session Scope

**File:** `server/app/db/connection.py`

```python
@contextmanager
def session_scope(self) -> Generator[Session, None, None]:
    """
    Provide a transactional scope for a series of operations.

    Usage:
        with oracle_db.session_scope() as session:
            session.execute(...)
            # auto-commit on success, auto-rollback on error
    """
    session = self.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Use Case:** Long-running streaming operations

### 3. FastAPI Dependency Functions

**File:** `server/app/db/dependencies.py` (NEW)

```python
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for SQLAlchemy database sessions.

    Provides:
    - Automatic session creation
    - Automatic commit on success
    - Automatic rollback on error
    - Automatic session cleanup
    """
    db = oracle_db.get_session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_db_readonly() -> Generator[Session, None, None]:
    """
    Read-only sessions for SELECT queries.
    No commit performed.
    """
    db = oracle_db.get_session()
    try:
        yield db
    finally:
        db.close()
```

### 4. Structured Error Handling

**File:** `server/app/core/exceptions.py` (NEW)

```python
class RecordNotFoundError(HTTPException):
    """Record not found - returns 404"""

class DuplicateRecordError(HTTPException):
    """Duplicate record - returns 409"""

class DatabaseError(HTTPException):
    """Generic DB error - returns 500"""

def handle_db_error(error: Exception) -> HTTPException:
    """
    Convert SQLAlchemy exceptions to appropriate HTTP exceptions.

    - IntegrityError → 409 Conflict
    - OperationalError → 500 Database Error
    - DBAPIError → 500 Database Error
    - HTTPException → Pass through
    """
```

**Benefits:**
- Proper HTTP status codes
- Better error messages for clients
- Consistent error format

---

## Usage Examples

### Example 1: Simple CRUD Endpoint

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.core.exceptions import RecordNotFoundError, handle_db_error

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        result = db.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        )
        user = result.fetchone()
        if not user:
            raise RecordNotFoundError("User not found")
        return {"user": user}
    except Exception as e:
        raise handle_db_error(e) from e
```

### Example 2: Read-Only Query

```python
from app.db.dependencies import get_db_readonly

@router.get("/stats")
def get_stats(db: Session = Depends(get_db_readonly)):
    # No commit happens, just cleanup
    count = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
    return {"total_orders": count}
```

### Example 3: Streaming with Context Manager

```python
async def stream_database_data() -> AsyncGenerator[dict[str, str], None]:
    from app.db.connection import oracle_db

    count = 0
    while True:
        try:
            # Each iteration gets a fresh session
            with oracle_db.session_scope() as session:
                result = session.execute(text("SELECT SYSDATE FROM DUAL"))
                row = result.fetchone()

                yield {
                    "event": "message",
                    "data": json.dumps({
                        "db_time": str(row[0]),
                        "count": count,
                    })
                }

            count += 1
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            break
```

---

## Migration Guide

### For New Endpoints

Use the Dependency Injection pattern:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.core.exceptions import handle_db_error

@router.post("/items")
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),  # ← Add this
):
    try:
        # Your database logic here
        db.execute(text("INSERT INTO items ..."))
        return {"ok": True}
    except Exception as e:
        raise handle_db_error(e) from e
```

### For Streaming Functions

Use context manager:

```python
async def my_stream() -> AsyncGenerator:
    from app.db.connection import oracle_db

    while True:
        with oracle_db.session_scope() as session:
            # Your query here
            result = session.execute(...)
            yield {...}
        await asyncio.sleep(1)
```

### For Legacy Code

The old `oracle_db.get_session()` still works but is **DEPRECATED**:

```python
# ⚠️ DEPRECATED - Still works but not recommended
session = oracle_db.get_session()
try:
    session.execute(...)
    session.commit()
finally:
    session.close()
```

---

## Testing

### Unit Testing with DI

Dependency Injection makes testing much easier:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create test database
engine = create_engine("sqlite:///:memory:")
TestSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

# Override dependency
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
response = client.post("/orders", json={...})
assert response.status_code == 200
```

---

## Performance Improvements

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| Connection reuse | Manual | Automatic | Pool management |
| Stale connections | Possible | Prevented | `pool_recycle=3600` |
| Connection leaks | Risk | Prevented | Auto-cleanup |
| Error handling | Inconsistent | Standardized | Proper status codes |
| Code duplication | High | Low | DRY principle |

---

## Best Practices

### ✅ DO

```python
# Use Dependency Injection for endpoints
@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    ...

# Use context manager for streaming
with oracle_db.session_scope() as session:
    ...

# Use structured error handling
try:
    ...
except Exception as e:
    raise handle_db_error(e) from e

# Use read-only dependency for queries
def get_stats(db: Session = Depends(get_db_readonly)):
    ...
```

### ❌ DON'T

```python
# Don't use manual session management
session = oracle_db.get_session()
try:
    ...
finally:
    session.close()

# Don't use async def with sync DB operations
async def endpoint(db: Session = Depends(get_db)):
    db.execute(...)  # Blocks event loop!

# Don't forget error handling
@router.post("/items")
def create(db: Session = Depends(get_db)):
    db.execute(...)  # No try/except!
```

---

## Further Improvements (Future)

For even better performance, consider migrating to async SQLAlchemy:

```python
# Requires: sqlalchemy[asyncio], asyncpg (for PostgreSQL) or aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=True,
)

async def get_async_db():
    async with AsyncSession(engine) as session:
        yield session
        await session.commit()

@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text("SELECT * FROM items"))
    ...
```

**Benefits:**
- True async I/O (non-blocking)
- Better concurrency
- Higher throughput

**Note:** Requires async database driver (not available for all databases).

---

## Summary

The refactored database layer provides:

1. ✅ **Automatic session management** - No manual cleanup needed
2. ✅ **Better error handling** - Proper HTTP status codes
3. ✅ **Cleaner code** - Less boilerplate
4. ✅ **Enhanced reliability** - Connection pool improvements
5. ✅ **Easier testing** - Dependency injection support
6. ✅ **Maintainability** - DRY principle, single responsibility

All existing functionality is preserved while significantly improving code quality.
