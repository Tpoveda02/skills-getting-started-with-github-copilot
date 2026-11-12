from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Chess Club"
SAMPLE_ACTIVITIES = {
    ACTIVITY_NAME: {
        "description": "Play chess",
        "schedule": "Fridays",
        "max_participants": 12,
        "participants": ["student@example.com"],
    }
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(SAMPLE_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == SAMPLE_ACTIVITIES


def test_signup_adds_participant(client):
    email = "new-student@example.com"

    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert email in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown/signup",
        params={"email": "new-student@example.com"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    email = "student@example.com"

    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert email not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown", "student@example.com", "Activity not found"),
        (ACTIVITY_NAME, "not-registered@example.com",
         "not-registered@example.com is not registered for Chess Club"),
    ],
)
def test_unregister_returns_404_for_unknown_activity_or_participant(
    client, activity_name, email, expected_detail
):
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
