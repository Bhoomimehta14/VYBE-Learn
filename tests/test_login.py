"""The demo login: accounts live in data/demo_users.json and the backend checks them."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "educator"))
os.environ.setdefault("ADK_BASE_URL", "http://127.0.0.1:1")

from fastapi.testclient import TestClient

from web import api
from web.api import app

client = TestClient(app)


def test_the_first_demo_account_is_demo_demo123():
    accounts = client.get("/api/demo-accounts").json()["accounts"]
    assert accounts[0] == {"username": "demo", "password": "demo123", "name": "Demo"}
    assert client.post("/api/login", json={"username": "demo", "password": "demo123"}).status_code == 200


def test_the_demo_accounts_file_is_valid_and_has_a_simple_admin_login():
    data = json.loads((ROOT / "data" / "demo_users.json").read_text(encoding="utf-8"))
    users = {u["username"]: u for u in data["users"]}
    assert users["admin"]["password"] == "admin123"
    for u in users.values():
        assert {"role", "experience", "goal"} <= set(u["profile"])


def test_the_login_page_can_list_the_demo_accounts():
    accounts = client.get("/api/demo-accounts").json()["accounts"]
    assert {"username": "admin", "password": "admin123", "name": "Admin"} in accounts


def test_the_right_username_and_password_log_in_with_that_accounts_profile():
    r = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and body["name"] == "Admin"
    assert body["profile"] == {"role": "admin", "experience": "pretty confident", "goal": "just exploring"}


def test_username_ignores_case_and_surrounding_spaces_but_password_does_not():
    assert client.post("/api/login", json={"username": "  ADMIN ", "password": "admin123"}).status_code == 200
    assert client.post("/api/login", json={"username": "admin", "password": "ADMIN123"}).status_code == 401


def test_wrong_credentials_are_refused_with_a_plain_message():
    for creds in ({"username": "admin", "password": "nope"}, {"username": "nobody", "password": "admin123"}):
        r = client.post("/api/login", json=creds)
        assert r.status_code == 401
        assert "don't match" in r.json()["error"]


def test_a_missing_accounts_file_means_no_logins_and_no_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "DEMO_USERS_PATH", tmp_path / "missing.json")
    assert client.get("/api/demo-accounts").json() == {"accounts": []}
    assert client.post("/api/login", json={"username": "admin", "password": "admin123"}).status_code == 401


def test_a_second_account_added_to_the_file_just_works(monkeypatch, tmp_path):
    path = tmp_path / "users.json"
    path.write_text(
        json.dumps(
            {
                "users": [
                    {
                        "username": "raj",
                        "password": "raj123",
                        "name": "Raj",
                        "profile": {"role": "business owner", "experience": "new to this", "goal": "get better at my job"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "DEMO_USERS_PATH", path)
    body = client.post("/api/login", json={"username": "raj", "password": "raj123"}).json()
    assert body["profile"]["role"] == "business owner"
