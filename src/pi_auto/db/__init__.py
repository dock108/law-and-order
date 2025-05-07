"""Database package for the PI Automation application."""

from pi_auto.db.crud import (
    create,
    delete_record,
    get,
    get_all,
    get_client_full_case,
    get_client_with_incidents,
    update,
)
from pi_auto.db.engine import (
    close_connection_pool,
    execute_query,
    execute_transaction,
    get_connection_pool,
)
from pi_auto.db.models import Base, Client, Doc, Incident, Insurance, Provider, Task

__all__ = [
    # Engine functions
    "get_connection_pool",
    "close_connection_pool",
    "execute_query",
    "execute_transaction",
    # CRUD operations
    "create",
    "get",
    "get_all",
    "update",
    "delete_record",
    "get_client_with_incidents",
    "get_client_full_case",
    # Models
    "Base",
    "Client",
    "Incident",
    "Insurance",
    "Provider",
    "Doc",
    "Task",
]
