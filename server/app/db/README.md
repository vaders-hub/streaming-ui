# Database Layer

## Architecture

This application uses a **hybrid approach** combining SQLAlchemy ORM with Raw SQL:

- **ORM** for simple CRUD operations (type safety, clean code)
- **Raw SQL** for complex queries (performance, Oracle-specific features)

## Files

### `models.py`
SQLAlchemy ORM models for database tables.

**Current Models:**
- `Order`: Represents orders table with full type safety

**Usage Example:**
```python
# Query using ORM
stmt = select(Order).where(Order.customer_id == 123)
orders = db.scalars(stmt).all()

# Create using ORM
new_order = Order(order_id=1, customer_id=123, status="PENDING")
db.add(new_order)
```

### `connection.py`
Database connection manager with SQLAlchemy engine and session factory.

**Important:**
- Application does NOT create/modify database schema
- `Base.metadata.create_all()` is intentionally NOT called
- Schema is managed by DBA
- ORM models map to existing tables

### `dependencies.py`
FastAPI dependency injection for database sessions.

### `streaming_helpers.py`
Session factory helpers for SSE streaming contexts.

## When to Use ORM vs Raw SQL

### Use ORM When:
✅ Simple CRUD operations (INSERT, UPDATE, DELETE by ID)
✅ Type safety is important
✅ Need Python object mapping
✅ Query is simple and doesn't need optimization

**Examples:**
- Creating a new order
- Updating order status by ID
- Querying orders by customer_id
- Simple joins

### Use Raw SQL When:
✅ Complex Oracle-specific queries (ROWNUM, CONNECT BY, etc.)
✅ Performance-critical queries
✅ Advanced window functions
✅ Bulk operations
✅ Legacy SQL that's already optimized

**Examples:**
- Streaming queries with ROWNUM limits
- Complex aggregations with multiple subqueries
- Oracle-specific functions (NVL, TO_CHAR with custom formats)
- Queries that are already tested and optimized

## Database Schema

Schema is managed externally by DBA. ORM models are for mapping only.

### Tables

#### ORDERS
```sql
CREATE TABLE orders (
    order_id NUMBER PRIMARY KEY,
    customer_id NUMBER NOT NULL,
    status VARCHAR2(20) NOT NULL,
    salesman_id NUMBER,
    order_date DATE NOT NULL
);
```

**Application Access:**
- Read: Streaming, queries
- Write: Test data creation only

**Managed By:** DBA

## Adding New Models

When adding new ORM models:

1. **Define Model** in `models.py`:
```python
class YourModel(Base):
    __tablename__ = "your_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
```

2. **DO NOT** run migrations or create_all()
3. **Ensure** table exists in database first
4. **Document** the table in this README

## Best Practices

1. **Type Safety**: Use ORM models when possible for better type checking
2. **Performance**: Use Raw SQL for complex queries
3. **Consistency**: Follow existing patterns in codebase
4. **Documentation**: Document why Raw SQL is used in complex cases
5. **Testing**: Test both ORM and Raw SQL queries thoroughly

## Examples from Codebase

### ORM Usage (oracle.py)
```python
# Create order with ORM
new_order = Order(
    order_id=next_id,
    customer_id=req.customer_id,
    status=req.status,
)
db.add(new_order)

# Query with ORM
stmt = select(Order).where(Order.order_id == order_id)
order = db.scalar(stmt)
```

### Raw SQL Usage (streaming.py)
```python
# Complex query with ROWNUM - too complex for ORM
result = session.execute(
    text("""
        SELECT order_id, customer_id, status
        FROM (
            SELECT order_id, customer_id, status
            FROM orders
            ORDER BY order_id DESC
        )
        WHERE ROWNUM <= :n
    """),
    {"n": limit}
)
```

## Migration Strategy

**Current:** No migrations (schema managed by DBA)

**Future:** If application needs to manage schema:
1. Install Alembic: `uv add alembic`
2. Initialize: `alembic init alembic`
3. Configure `alembic.ini` with connection string
4. Generate migrations: `alembic revision --autogenerate`
5. Apply: `alembic upgrade head`

**When to consider migrations:**
- Application manages schema across environments
- Frequent schema changes
- Multiple developers need schema sync
- CI/CD pipeline needs schema automation
