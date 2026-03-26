from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Settings
from app.models import Base, User


class UserContextValidationTestCase(unittest.TestCase):
    def setUp(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        
        # Create test data file with sample divisions/teams
        import os
        data_dir = tmpdir.name
        test_data = {
            "meta": {"league_name": "Test League"},
            "league": {},
            "divisions": {
                "test_div_1": {"id": "test_div_1", "name": "Test Division 1"},
                "test_div_2": {"id": "test_div_2", "name": "Test Division 2"},
            },
            "teams": {
                "test_team_1": {"id": "test_team_1", "name": "Test Team 1", "division_id": "test_div_1"},
                "test_team_2": {"id": "test_team_2", "name": "Test Team 2", "division_id": "test_div_1"},
                "test_team_3": {"id": "test_team_3", "name": "Test Team 3", "division_id": "test_div_2"},
            },
            "players": [],
            "matches": [],
            "locations": [],
        }
        
        data_file = os.path.join(data_dir, "test_data.json")
        with open(data_file, "w") as f:
            json.dump(test_data, f)
        
        self.settings = Settings(
            environment="test",
            secret_key="test-secret",
            database_url="sqlite+pysqlite:///:memory:",
            api_host="127.0.0.1",
            api_port=0,
            data_dir=data_dir,
            cors_allow_origin=None,
        )
        self.app = create_app(self.settings)
        self.client = self.app.test_client()
        with self.app.app_context():
            Base.metadata.create_all(self.app.config["DB_ENGINE"])
        
        # Create test user
        self._create_user("test@example.com", "password123")
    
    def _csrf(self):
        resp = self.client.get("/api/auth/csrf")
        data = resp.get_json()
        return data["csrf_token"]
    
    def _create_user(self, email: str, password: str):
        with self.app.app_context():
            session = self.app.config["DB_SESSION"]
            user = User(
                email=email,
                username=email.split("@")[0],
                password_hash=generate_password_hash(password),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(user)
            session.commit()
    
    def _login(self, email: str, password: str):
        csrf = self._csrf()
        resp = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": email, "password": password}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        return resp
    
    def test_valid_division_id(self):
        """Test updating context with valid division_id."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({"division_id": "test_div_1", "role": "player"}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["context"]["division_id"], "test_div_1")
    
    def test_invalid_division_id(self):
        """Test updating context with invalid division_id."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({"division_id": "nonexistent_div", "role": "player"}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "invalid_division")
        self.assertEqual(data["error"]["field"], "division_id")
    
    def test_valid_team_id_in_division(self):
        """Test updating context with valid team_id that belongs to division."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({
                "division_id": "test_div_1",
                "team_id": "test_team_1",
                "role": "player"
            }),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["context"]["team_id"], "test_team_1")
    
    def test_invalid_team_id(self):
        """Test updating context with invalid team_id."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({
                "division_id": "test_div_1",
                "team_id": "nonexistent_team",
                "role": "player"
            }),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "invalid_team")
        self.assertEqual(data["error"]["field"], "team_id")
    
    def test_team_not_in_division(self):
        """Test updating context with team that doesn't belong to selected division."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({
                "division_id": "test_div_1",
                "team_id": "test_team_3",  # test_team_3 belongs to test_div_2
                "role": "player"
            }),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "team_not_in_division")
        self.assertEqual(data["error"]["field"], "team_id")
    
    def test_valid_role(self):
        """Test updating context with valid role."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        for role in ["captain", "player", "fan"]:
            resp = self.client.put(
                "/api/user/context",
                data=json.dumps({"role": role}),
                content_type="application/json",
                headers={"X-CSRF-Token": csrf},
            )
            
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["context"]["role"], role)
    
    def test_invalid_role(self):
        """Test updating context with invalid role."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.put(
            "/api/user/context",
            data=json.dumps({"role": "invalid_role"}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "invalid_role")
        self.assertEqual(data["error"]["field"], "role")
    
    def test_complete_onboarding_with_valid_context(self):
        """Test completing onboarding with valid division and team."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        # Set context first
        self.client.put(
            "/api/user/context",
            data=json.dumps({
                "division_id": "test_div_1",
                "team_id": "test_team_1",
                "role": "captain"
            }),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        # Complete onboarding
        csrf = self._csrf()
        resp = self.client.post(
            "/api/onboarding/complete",
            data=json.dumps({}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["user"]["onboarding_completed"])
    
    def test_complete_onboarding_without_context(self):
        """Test completing onboarding without setting context first."""
        self._login("test@example.com", "password123")
        csrf = self._csrf()
        
        resp = self.client.post(
            "/api/onboarding/complete",
            data=json.dumps({}),
            content_type="application/json",
            headers={"X-CSRF-Token": csrf},
        )
        
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "incomplete_setup")


if __name__ == "__main__":
    unittest.main()
