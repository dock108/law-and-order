# CRUD Operations Reference

This document provides a reference for using the CRUD (Create, Read, Update, Delete) operations in the Personal Injury Automation system.

## Basic Operations

### Setting Up

```python
import asyncio
from pi_auto.db import (
    create, get, get_all, update, delete_record,
    get_connection_pool, close_connection_pool,
    Client, Incident, Insurance, Provider, Doc, Task
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

async def main():
    # Get the connection pool
    pool = await get_connection_pool()

    # Create a session factory
    async_session_factory = sessionmaker(
        expire_on_commit=False,
        class_=AsyncSession
    )

    # Create a session
    async with async_session_factory(bind=pool) as session:
        # Perform operations here

        # Don't forget to commit
        await session.commit()

    # Clean up
    await close_connection_pool()

# Run the async function
asyncio.run(main())
```

### Creating Records

```python
# Create a client
client_data = {
    "full_name": "John Doe",
    "dob": datetime.date(1980, 1, 1),
    "phone": "555-123-4567",
    "email": "john.doe@example.com",
    "address": "123 Main St, Anytown, USA"
}
client = await create(session, Client, client_data)

# Create an incident for this client
incident_data = {
    "client_id": client.id,
    "date": datetime.date(2023, 5, 10),
    "location": "Main St and Broadway intersection",
    "injuries": {"type": "whiplash", "severity": "moderate"}
}
incident = await create(session, Incident, incident_data)

# Create insurance information
insurance_data = {
    "incident_id": incident.id,
    "carrier_name": "ABC Insurance",
    "policy_number": "POL-12345",
    "claim_number": "CLM-67890",
    "is_client_side": True
}
insurance = await create(session, Insurance, insurance_data)
```

### Reading Records

```python
# Get a client by ID
client = await get(session, Client, 1)

# Get all clients
all_clients = await get_all(session, Client)

# Get a client with all incidents
client_with_incidents = await get_client_with_incidents(session, 1)

# Get a client with full case information
full_case = await get_client_full_case(session, 1)
```

### Updating Records

```python
# Update a client record
updated_data = {
    "phone": "555-999-8888",
    "email": "john.new.email@example.com"
}
updated_client = await update(session, Client, 1, updated_data)
```

### Deleting Records

```python
# Delete a record (returns True if successful, False if not found)
success = await delete_record(session, Client, 1)
```

## Transactions

For operations that need to be performed as a unit:

```python
queries = [
    ("INSERT INTO client (full_name, email) VALUES ($1, $2)", ["Jane Smith", "jane@example.com"]),
    ("UPDATE client SET address = $1 WHERE email = $2", ["456 Oak St", "john.doe@example.com"])
]
await execute_transaction(queries)
```

## Raw SQL Queries

For more complex operations:

```python
# Execute a custom query
results = await execute_query(
    "SELECT c.full_name, i.date, i.location FROM client c JOIN incident i ON c.id = i.client_id WHERE c.id = $1",
    1
)
```

## Best Practices

1. Always use the `async with` context manager for sessions to ensure proper cleanup.
2. Commit the session after making changes.
3. Use the CRUD operations instead of raw SQL when possible.
4. Close the connection pool when your application exits.
5. Use parametrized queries to prevent SQL injection.
6. Handle exceptions appropriately, especially for database operations.
7. For bulk operations, use transactions to ensure atomicity.
