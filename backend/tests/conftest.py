import pytest
from sqlalchemy import text

from app import create_app
from app.config import TestConfig
from app.extensions import db
from tests.factories import PASSWORD, make_user


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app

        db.session.rollback()
        table_names = ", ".join(table.name for table in db.metadata.sorted_tables)
        db.session.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
        db.session.commit()
        db.session.remove()


@pytest.fixture
def demo_users(app):
    users = {
        "customer": make_user(email="customer@demo.com", role="CUSTOMER", full_name="Ravi Kumar"),
        "officer": make_user(email="officer@demo.com", role="OFFICER", full_name="Anita Rao"),
        "admin": make_user(email="admin@demo.com", role="ADMIN", full_name="Admin User"),
    }
    db.session.commit()
    return users


@pytest.fixture
def client(app, demo_users):
    return app.test_client()


def login_as(client, email, password=PASSWORD):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_headers(client):
    return login_as(client, "customer@demo.com")


@pytest.fixture
def officer_headers(client):
    return login_as(client, "officer@demo.com")


@pytest.fixture
def admin_headers(client):
    return login_as(client, "admin@demo.com")
