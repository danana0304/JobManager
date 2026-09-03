import os
import sys
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api import Application, Posting, User, UserType, app, db


class ApiCrudTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with app.app_context():
            db.drop_all()
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def setUp(self):
        self.client = app.test_client()

    def register(self, email, password="password123"):
        return self.client.post(
            "/register",
            json={"email": email, "password": password},
        )

    def login(self, email, password="password123"):
        return self.client.post(
            "/login",
            json={"email": email, "password": password},
        )

    def test_user_registration_and_login(self):
        response = self.register("user@example.com")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["usertype"], "User")

        response = self.login("user@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["email"], "user@example.com")
        self.assertEqual(response.json["usertype"], "User")

        response = self.client.get("/me")
        self.assertTrue(response.json["logged_in"])

    def test_registration_validation_and_duplicate_user(self):
        self.assertEqual(self.register("", "password123").status_code, 400)
        self.assertEqual(self.register("duplicate@example.com").status_code, 201)
        self.assertEqual(self.register("duplicate@example.com").status_code, 409)
        self.assertEqual(
            self.login("duplicate@example.com", "wrong-password").status_code,
            401,
        )

    def test_posting_create_and_read(self):
        user_response = self.register("poster@example.com")
        user_id = user_response.json["userid"]

        response = self.client.post(
            "/postings",
            json={
                "company": "Example Corp",
                "position": "Engineer",
                "description": "Build useful software",
                "postedby": user_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        posting_id = response.json["postingid"]

        response = self.client.get("/postings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["postingid"], posting_id)

        response = self.client.get(f"/users/{user_id}/postings")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["description"], "Build useful software")

    def test_application_create_read_and_update_status(self):
        poster_id = self.register("poster2@example.com").json["userid"]
        applicant_id = self.register("applicant@example.com").json["userid"]
        posting_id = self.client.post(
            "/postings",
            json={"company": "Example Corp", "position": "Developer", "postedby": poster_id},
        ).json["postingid"]

        response = self.client.post(
            "/applications",
            json={"postingid": posting_id, "userid": applicant_id},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["status"], "Applied")
        self.assertEqual(
            self.client.post(
                "/applications",
                json={"postingid": posting_id, "userid": applicant_id},
            ).status_code,
            409,
        )

        response = self.client.get(f"/applications/users/{applicant_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["postingid"], posting_id)

        response = self.client.get(f"/postings/{posting_id}/applicants")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["user"]["email"], "applicant@example.com")

        response = self.client.put(
            f"/applications/postings/{posting_id}/users/{applicant_id}",
            json={"status": "Accepted"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "Accepted")

    def test_application_and_posting_validation(self):
        self.assertEqual(
            self.client.post("/applications", json={"postingid": 999, "userid": 1}).status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                "/applications/postings/999/users/1",
                json={"status": "Unknown"},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/postings", json={"company": "Only Company"}).status_code,
            400,
        )

    def test_user_role_update_and_audit_log(self):
        user_id = self.register("role@example.com").json["userid"]
        response = self.client.put(
            f"/users/{user_id}/role",
            json={"usertype": "Admin"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["usertype"], "Admin")

        response = self.client.post(
            "/audit-logs",
            json={
                "action": "UPDATE",
                "entitytype": "User",
                "actoruserid": user_id,
                "entityid": user_id,
                "newvalues": {"usertype": "Admin"},
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get("/audit-logs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["entitytype"], "User")

    def test_logout_and_protected_routes(self):
        self.register("logout@example.com")
        self.login("logout@example.com")
        self.assertEqual(self.client.post("/logout").status_code, 200)
        self.assertFalse(self.client.get("/me").json["logged_in"])
        self.assertEqual(self.client.get("/admin").status_code, 401)


if __name__ == "__main__":
    unittest.main()
