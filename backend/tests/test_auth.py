"""TC-01 / TC-11: authentication and access control."""
from conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def test_login_with_valid_credentials_returns_token(client):
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    body = response.get_json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["email"] == ADMIN_EMAIL
    assert body["data"]["user"]["role"] == "ADMIN"
    assert "password" not in body["data"]["user"]
    assert "password_hash" not in body["data"]["user"]


def test_login_with_wrong_password_is_rejected(client):
    response = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "definitely-wrong"}
    )
    body = response.get_json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"] == "INVALID_CREDENTIALS"


def test_login_with_unknown_email_gives_the_same_message(client):
    """The error must not reveal whether an account exists."""
    unknown = client.post(
        "/api/auth/login", json={"email": "nobody@test.local", "password": "whatever"}
    ).get_json()
    wrong = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "whatever"}
    ).get_json()

    assert unknown["message"] == wrong["message"]


def test_login_with_malformed_email_is_a_validation_error(client):
    response = client.post("/api/auth/login", json={"email": "not-an-email", "password": "x"})

    assert response.status_code == 422
    assert response.get_json()["error"] == "VALIDATION_ERROR"


def test_login_requires_a_password(client):
    response = client.post("/api/auth/login", json={"email": ADMIN_EMAIL})

    assert response.status_code == 422
    assert "password" in response.get_json()["message"].lower()


def test_disabled_account_cannot_sign_in(client):
    response = client.post(
        "/api/auth/login", json={"email": "disabled@test.local", "password": "disabled123"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "ACCOUNT_DISABLED"


def test_protected_route_rejects_a_missing_token(client):
    response = client.get("/api/alerts")

    assert response.status_code == 401
    assert response.get_json()["error"] == "NO_TOKEN"


def test_protected_route_rejects_a_forged_token(client):
    response = client.get("/api/alerts", headers={"Authorization": "Bearer not.a.real.token"})

    assert response.status_code == 401
    assert response.get_json()["error"] == "TOKEN_INVALID"


def test_me_returns_the_signed_in_profile(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    body = response.get_json()

    assert response.status_code == 200
    assert body["data"]["email"] == ADMIN_EMAIL
    assert "preferences" in body["data"]


def test_profile_can_be_updated(client, auth_headers):
    response = client.put(
        "/api/auth/profile", headers=auth_headers, json={"full_name": "Renamed Admin"}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["full_name"] == "Renamed Admin"


def test_preferences_reject_an_out_of_range_sensitivity(client, auth_headers):
    response = client.put(
        "/api/auth/preferences", headers=auth_headers, json={"detection_sensitivity": 9.0}
    )

    assert response.status_code == 422
    assert response.get_json()["error"] == "VALIDATION_ERROR"


def test_password_change_requires_the_current_password(client, auth_headers):
    response = client.put(
        "/api/auth/password",
        headers=auth_headers,
        json={"current_password": "wrong", "new_password": "newpassword"},
    )

    assert response.status_code == 401


def test_password_change_succeeds_and_the_new_password_works(client, auth_headers):
    changed = client.put(
        "/api/auth/password",
        headers=auth_headers,
        json={"current_password": ADMIN_PASSWORD, "new_password": "brand-new-pass"},
    )
    assert changed.status_code == 200

    relogin = client.post(
        "/api/auth/login", json={"email": ADMIN_EMAIL, "password": "brand-new-pass"}
    )
    assert relogin.status_code == 200


def test_logout_is_recorded(client, auth_headers):
    response = client.post("/api/auth/logout", headers=auth_headers)
    assert response.status_code == 200

    logs = client.get("/api/audit-logs", headers=auth_headers).get_json()["data"]
    assert any(entry["action"] == "LOGOUT" for entry in logs)


def test_failed_login_is_audited(client, auth_headers):
    client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": "nope-wrong"})

    logs = client.get("/api/audit-logs", headers=auth_headers).get_json()["data"]
    failures = [entry for entry in logs if entry["action"] == "LOGIN_FAILED"]

    assert failures
    assert failures[0]["status"] == "FAILURE"
