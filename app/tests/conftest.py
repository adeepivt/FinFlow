import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.utils.security import hash_password

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Automatically set up and tear down database for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Provide database session for tests that need direct DB access."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("testpassword123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    login_data = {
        "username": test_user.email,
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_account(db, test_user):
    account = Account(
        user_id=test_user.id,
        name="Test Checking",
        account_type="checking",
        balance=1000.00,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def test_savings_account(db, test_user):
    account = Account(
        user_id=test_user.id,
        name="Test Savings",
        account_type="savings",
        balance=500.00,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account