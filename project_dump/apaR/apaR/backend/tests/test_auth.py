from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Settings
from app.models import Base, User


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        
        # Create test data file with sample divisions/teams
        test_data = {
            "meta": {"league_name": "Test League"},
            "league": {},
            "divisions": [
                {"id": "div_1", "name": "Division 1"},
                {"id": "div_2", "name": "Division 2"},
            ],
            "teams": [
                {"id": "team_1", "name": "Team 1", "division_id": "div_1"},
                {"id": "team_2", "name": "Team 2", "division_id": "div_1"},
                {"id": "team_3", "name": "Team 3", "division_id": "div_2"},
            ],
            "players": [],
            "matches": [],
            "locations": [],
        }
        
        data_file = os.path.join(tmpdir.name, "test_data.json")
        with open(data_file, "w") as f:
            json.dump(test_data, f)
        
        self.settings = Settings(
            environment="test",
            secret_key="test-secret",
            database_url="sqlite+pysqlite:///:memory:",
            api_host="127.0.0.1",
            api_port=0,
            data_dir=tmpdir.name,
            cors_allow_origin=None,
        )
        self.app = create_app(self.settings)
        self.client = self.app.test_client()
        with self.app.app_context():
            Base.metadata.create_all(self.app.config["DB_ENGINE"])

    def _csrf(self):
        resp = self.client.get("/api/auth/csrf")
        data = resp.get_json()
        return data["csrf_token"]

    def _create_user(self, email: str, password: str, is_admin: bool = False):
        with self.app.app_context():
            session = self.app.config["DB_SESSION"]
            user = User(
                email=email,
                username=email.split("@")[0],
                password_hash=generate_password_hash(password),
                is_admin=is_admin,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.commit()

    def test_signup_creates_user(self):
        token = self._csrf()
        res = self.client.post(
            "/api/auth/signup",
            data=json.dumps({"email": "new@example.com", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["user"]["email"], "new@example.com")

    def test_signup_rejects_whitespace_email(self):
        token = self._csrf()
        res = self.client.post(
            "/api/auth/signup",
            data=json.dumps({"email": "   ", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "invalid_email")

    def test_login_and_me(self):
        self._create_user("user@example.com", "password123")
        token = self._csrf()
        login = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        self.assertEqual(login.status_code, 200)
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.get_json()["user"]["email"], "user@example.com")

    def test_logout_clears_session(self):
        self._create_user("user@example.com", "password123")
        token = self._csrf()
        self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        logout = self.client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
        self.assertEqual(logout.status_code, 200)
        me = self.client.get("/api/auth/me")
        self.assertIsNone(me.get_json()["user"])

    def test_admin_endpoints_require_admin(self):
        # No session
        res = self.client.get("/api/admin/health")
        self.assertEqual(res.status_code, 401)

        # Logged in but not admin
        self._create_user("user@example.com", "password123", is_admin=False)
        token = self._csrf()
        self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "user@example.com", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        res_non_admin = self.client.get("/api/admin/health")
        self.assertEqual(res_non_admin.status_code, 403)

        # Admin user
        self.client.post("/api/auth/logout", headers={"X-CSRF-Token": token})
        self._create_user("admin@example.com", "password123", is_admin=True)
        token = self._csrf()
        self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "admin@example.com", "password": "password123"}),
            headers={"Content-Type": "application/json", "X-CSRF-Token": token},
        )
        res_admin = self.client.get("/api/admin/health")
        self.assertEqual(res_admin.status_code, 200)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
