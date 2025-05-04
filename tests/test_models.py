"""Integration tests for database models."""

import datetime

import pytest
from pi_auto.db.models import Base, Client, Doc, Incident, Insurance, Provider, Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Create a SQLite in-memory engine for testing."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """Create a new session for the test database."""
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    yield session
    session.close()


def test_client_model(session):
    """Test creating and querying a client."""
    # Create a client
    client = Client(
        full_name="John Doe",
        dob=datetime.date(1980, 1, 1),
        phone="555-123-4567",
        email="john.doe@example.com",
        address="123 Main St, Anytown, USA",
    )

    session.add(client)
    session.commit()

    # Query the client
    queried_client = session.query(Client).filter_by(full_name="John Doe").first()

    assert queried_client is not None
    assert queried_client.full_name == "John Doe"
    assert queried_client.email == "john.doe@example.com"
    assert queried_client.id is not None


def test_incident_relationship(session):
    """Test relationship between client and incident."""
    # Create a client with an incident
    client = Client(full_name="Jane Smith", email="jane.smith@example.com")

    incident = Incident(
        client=client,
        date=datetime.date(2023, 6, 15),
        location="Intersection of Main St and Broadway",
        police_report_url="https://example.com/report123",
        injuries={"type": "whiplash", "severity": "moderate"},
        vehicle_damage_text="Front bumper damage",
    )

    session.add(client)
    session.commit()

    # Query the incident through the client
    queried_client = session.query(Client).filter_by(full_name="Jane Smith").first()

    assert queried_client is not None
    assert len(queried_client.incidents) == 1

    incident = queried_client.incidents[0]
    assert incident.location == "Intersection of Main St and Broadway"
    assert incident.injuries["type"] == "whiplash"


def test_full_relationship_chain(session):
    """Test the full relationship chain from client to task."""
    # Create a complete client case
    client = Client(full_name="Robert Johnson", email="robert@example.com")

    incident = Incident(
        client=client, date=datetime.date(2023, 5, 10), location="Highway 101"
    )

    # Create related objects - these will be automatically added to the session
    # when the client is added due to the relationship cascade
    Insurance(
        incident=incident,
        carrier_name="ABC Insurance",
        policy_number="POL-12345",
        claim_number="CLM-67890",
        is_client_side=True,
    )

    Provider(
        incident=incident,
        name="City General Hospital",
        phone="555-999-8888",
        fax="555-999-7777",
    )

    Doc(
        incident=incident,
        type="medical_records",
        url="https://example.com/records/123",
        status="received",
    )

    Task(
        incident=incident,
        type="request_records",
        due_date=datetime.date(2023, 6, 1),
        status="completed",
        assignee_email="paralegal@example.com",
    )

    session.add(client)
    session.commit()

    # Query and check everything
    queried_client = session.query(Client).filter_by(full_name="Robert Johnson").first()

    assert queried_client is not None
    assert len(queried_client.incidents) == 1

    queried_incident = queried_client.incidents[0]
    assert len(queried_incident.insurances) == 1
    assert len(queried_incident.providers) == 1
    assert len(queried_incident.docs) == 1
    assert len(queried_incident.tasks) == 1

    queried_insurance = queried_incident.insurances[0]
    assert queried_insurance.carrier_name == "ABC Insurance"

    queried_provider = queried_incident.providers[0]
    assert queried_provider.name == "City General Hospital"

    queried_doc = queried_incident.docs[0]
    assert queried_doc.type == "medical_records"

    queried_task = queried_incident.tasks[0]
    assert queried_task.type == "request_records"
    assert queried_task.status == "completed"
