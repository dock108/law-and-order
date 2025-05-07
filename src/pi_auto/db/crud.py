"""CRUD operations for the database models."""

from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import delete
from sqlalchemy.sql import update as sql_update

from pi_auto.db.models import Client, Doc, Incident, Insurance, Provider, Staff, Task

# Type variable for generic model operations
T = TypeVar("T", Client, Incident, Insurance, Provider, Doc, Task, Staff)


async def create(
    session: AsyncSession, model_class: Type[T], data: Dict[str, Any]
) -> T:
    """Create a new record.

    Args:
        session: The database session
        model_class: The model class to create
        data: Dictionary of data for the new record

    Returns:
        The newly created model instance
    """
    obj = model_class(**data)
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def get(session: AsyncSession, model_class: Type[T], id: int) -> Optional[T]:
    """Get a record by ID.

    Args:
        session: The database session
        model_class: The model class to query
        id: The record ID

    Returns:
        The model instance or None if not found
    """
    result = await session.execute(select(model_class).where(model_class.id == id))
    return result.scalars().first()


async def get_all(session: AsyncSession, model_class: Type[T]) -> List[T]:
    """Get all records of a model.

    Args:
        session: The database session
        model_class: The model class to query

    Returns:
        List of model instances
    """
    result = await session.execute(select(model_class))
    return result.scalars().all()


async def update(
    session: AsyncSession, model_class: Type[T], id: int, data: Dict[str, Any]
) -> Optional[T]:
    """Update a record.

    Args:
        session: The database session
        model_class: The model class to update
        id: The record ID
        data: Dictionary of data to update

    Returns:
        The updated model instance or None if not found
    """
    # Update the record
    query = sql_update(model_class).where(model_class.id == id).values(**data)
    await session.execute(query)

    # Get the updated record
    result = await session.execute(select(model_class).where(model_class.id == id))
    obj = result.scalars().first()

    if obj:
        await session.commit()

    return obj


async def delete_record(session: AsyncSession, model_class: Type[T], id: int) -> bool:
    """Delete a record.

    Args:
        session: The database session
        model_class: The model class to delete from
        id: The record ID

    Returns:
        True if deleted, False if not found
    """
    query = delete(model_class).where(model_class.id == id)
    result = await session.execute(query)
    await session.commit()

    # Return True if a row was deleted
    return result.rowcount > 0


# Client-specific operations


async def get_client_with_incidents(
    session: AsyncSession, client_id: int
) -> Optional[Client]:
    """Get a client with all related incidents.

    Args:
        session: The database session
        client_id: The client ID

    Returns:
        Client with incidents loaded or None if not found
    """
    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.incidents))
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_client_full_case(
    session: AsyncSession, client_id: int
) -> Optional[Client]:
    """Get a client with complete case information.

    This loads all related incidents, insurance, providers, docs, and tasks.

    Args:
        session: The database session
        client_id: The client ID

    Returns:
        Fully loaded client or None if not found
    """
    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.incidents).selectinload(Incident.insurances),
            selectinload(Client.incidents).selectinload(Incident.providers),
            selectinload(Client.incidents).selectinload(Incident.docs),
            selectinload(Client.incidents).selectinload(Incident.tasks),
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()


# Staff-specific operations
async def get_staff_by_email(session: AsyncSession, email: str) -> Optional[Staff]:
    """Get a staff member by email.

    Args:
        session: The database session
        email: The staff member's email

    Returns:
        The Staff instance or None if not found
    """
    result = await session.execute(select(Staff).where(Staff.email == email))
    return result.scalars().first()
