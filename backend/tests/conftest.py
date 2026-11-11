import pytest

from app.main import reset_database


@pytest.fixture(autouse=True)
def clean_database():
    reset_database()