"""TC-06 / TC-07: alert triage and the incident lifecycle state machine."""
import pytest

CRITICAL_EVENT = {
    "source_ip": "203.0.113.90",
    "destination_ip": "10.0.1.20",
    "destination_port": 22,
    "protocol": "SSH",
    "event_type": "authentication",
    "request_count": 420,
    "failed_login_attempts": 380,
    "packet_count": 1900,
    "bytes_transferred": 260000,
    "connection_duration": 180,
}


@pytest.fixture()
def alert(client, auth_headers):
    """An alert produced by the real detection pipeline."""
    response = client.post("/api/events/analyze", headers=auth_headers, json=CRITICAL_EVENT)
    created = response.get_json()["data"]["alert"]
    assert created is not None
    return created


# ---------------------------------------------------------------------- alerts


def test_alerts_are_listed_with_filter_metadata(client, auth_headers):
    body = client.get("/api/alerts", headers=auth_headers).get_json()

    assert body["success"] is True
    assert "pagination" in body
    assert "severities" in body["filters"]
    assert "statuses" in body["filters"]


def test_alerts_can_be_filtered_by_severity(client, auth_headers, alert):
    body = client.get("/api/alerts?severity=CRITICAL", headers=auth_headers).get_json()

    assert all(row["severity"] == "CRITICAL" for row in body["data"])


def test_alerts_can_be_searched_by_source_ip(client, auth_headers, alert):
    body = client.get(
        f"/api/alerts?search={alert['source_ip']}", headers=auth_headers
    ).get_json()

    assert body["pagination"]["total"] >= 1
    assert all(alert["source_ip"] in row["source_ip"] for row in body["data"])


def test_alerts_can_be_sorted_by_risk(client, auth_headers, alert):
    rows = client.get("/api/alerts?sort=risk", headers=auth_headers).get_json()["data"]
    scores = [row["risk_score"] for row in rows]

    assert scores == sorted(scores, reverse=True)


def test_single_alert_includes_its_event(client, auth_headers, alert):
    body = client.get(f"/api/alerts/{alert['id']}", headers=auth_headers).get_json()

    assert body["data"]["alert_code"] == alert["alert_code"]
    assert body["data"]["event"] is not None
    assert body["data"]["reasons"]


def test_alert_can_be_moved_to_investigating(client, auth_headers, alert):
    response = client.put(
        f"/api/alerts/{alert['id']}",
        headers=auth_headers,
        json={"action": "investigate", "note": "Checking the source."},
    )
    data = response.get_json()["data"]

    assert response.status_code == 200
    assert data["status"] == "INVESTIGATING"
    assert "Checking the source." in data["notes"]


def test_alert_can_be_resolved(client, auth_headers, alert):
    response = client.put(
        f"/api/alerts/{alert['id']}", headers=auth_headers, json={"action": "resolve"}
    )
    data = response.get_json()["data"]

    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None


def test_alert_can_be_marked_false_positive(client, auth_headers, alert):
    response = client.put(
        f"/api/alerts/{alert['id']}", headers=auth_headers, json={"action": "false_positive"}
    )

    assert response.get_json()["data"]["status"] == "FALSE_POSITIVE"


def test_invalid_alert_status_is_rejected(client, auth_headers, alert):
    response = client.put(
        f"/api/alerts/{alert['id']}", headers=auth_headers, json={"status": "BANANA"}
    )

    assert response.status_code == 422


def test_alert_status_change_is_audited(client, auth_headers, alert):
    client.put(f"/api/alerts/{alert['id']}", headers=auth_headers, json={"action": "resolve"})
    logs = client.get("/api/audit-logs", headers=auth_headers).get_json()["data"]

    assert any(entry["action"] == "ALERT_STATUS_CHANGED" for entry in logs)


def test_alert_can_be_escalated_to_an_incident(client, auth_headers, alert):
    response = client.post(f"/api/alerts/{alert['id']}/escalate", headers=auth_headers, json={})
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["incident"]["incident_code"].startswith("INC-")
    assert data["alert"]["incident_id"] == data["incident"]["id"]


def test_unknown_alert_returns_404(client, auth_headers):
    response = client.get("/api/alerts/999999", headers=auth_headers)
    assert response.status_code == 404


# ------------------------------------------------------------------- incidents


def test_incident_can_be_created_manually(client, auth_headers):
    response = client.post(
        "/api/incidents",
        headers=auth_headers,
        json={
            "title": "Suspicious VPN sessions from a new region",
            "description": "Several sign-ins outside the expected geography.",
            "threat_type": "Suspicious Login Activity",
            "severity": "HIGH",
            "source_ip": "203.0.113.201",
        },
    )
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["incident_code"].startswith("INC-")
    assert data["status"] == "NEW"
    assert data["severity"] == "HIGH"
    assert data["priority"] == "P2"
    assert len(data["history"]) == 1


def test_incident_creation_requires_a_title(client, auth_headers):
    response = client.post("/api/incidents", headers=auth_headers, json={"severity": "HIGH"})

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "title"


def test_incident_creation_rejects_an_unknown_severity(client, auth_headers):
    response = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "Test case", "severity": "URGENT"}
    )

    assert response.status_code == 422


def test_incident_exposes_only_legal_transitions(client, auth_headers):
    incident = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "Lifecycle test case"}
    ).get_json()["data"]

    detail = client.get(f"/api/incidents/{incident['id']}", headers=auth_headers).get_json()["data"]

    assert detail["state_machine"]["current"] == "NEW"
    assert set(detail["state_machine"]["allowed"]) == {"OPEN", "INVESTIGATING", "FALSE_POSITIVE"}
    assert "RESOLVED" not in detail["state_machine"]["allowed"]


def test_illegal_transition_is_refused(client, auth_headers):
    incident = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "Illegal transition test"}
    ).get_json()["data"]

    response = client.put(
        f"/api/incidents/{incident['id']}", headers=auth_headers, json={"status": "RESOLVED"}
    )
    body = response.get_json()

    assert response.status_code == 409
    assert body["error"] == "CONFLICT"
    assert body["details"]["current"] == "NEW"
    assert body["details"]["requested"] == "RESOLVED"


def test_full_lifecycle_new_to_resolved(client, auth_headers):
    incident = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "Full lifecycle walk-through"}
    ).get_json()["data"]
    incident_id = incident["id"]

    for action, expected in (
        ("investigate", "INVESTIGATING"),
        ("contain", "CONTAINED"),
        ("resolve", "RESOLVED"),
    ):
        response = client.put(
            f"/api/incidents/{incident_id}",
            headers=auth_headers,
            json={"action": action, "note": f"Moving to {expected}"},
        )
        assert response.status_code == 200, response.get_json()
        assert response.get_json()["data"]["status"] == expected

    final = client.get(f"/api/incidents/{incident_id}", headers=auth_headers).get_json()["data"]
    assert final["resolved_at"] is not None
    assert final["contained_at"] is not None
    assert len(final["history"]) == 4  # creation + three transitions


def test_incident_can_be_closed_as_false_positive(client, auth_headers):
    incident = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "False positive case"}
    ).get_json()["data"]

    response = client.put(
        f"/api/incidents/{incident['id']}",
        headers=auth_headers,
        json={"action": "false_positive", "resolution_summary": "Authorised internal scan."},
    )
    data = response.get_json()["data"]

    assert data["status"] == "FALSE_POSITIVE"
    assert data["resolution_summary"] == "Authorised internal scan."


def test_escalating_an_already_linked_alert_returns_the_same_incident(client, auth_headers, alert):
    """A CRITICAL alert already owns an auto-created incident; escalating must not duplicate it."""
    assert alert["incident_id"] is not None

    escalated = client.post(
        f"/api/alerts/{alert['id']}/escalate", headers=auth_headers, json={}
    ).get_json()["data"]["incident"]

    assert escalated["id"] == alert["incident_id"]


def test_resolving_an_incident_closes_its_alerts(client, auth_headers, alert):
    incident = client.post(
        f"/api/alerts/{alert['id']}/escalate", headers=auth_headers, json={}
    ).get_json()["data"]["incident"]

    # The incident opened automatically in NEW, so it must be investigated first:
    # NEW -> CONTAINED is not a legal transition.
    client.put(
        f"/api/incidents/{incident['id']}",
        headers=auth_headers,
        json={"action": "investigate", "note": "Triage started."},
    )
    client.put(
        f"/api/incidents/{incident['id']}",
        headers=auth_headers,
        json={"action": "contain", "note": "Blocked."},
    )
    client.put(
        f"/api/incidents/{incident['id']}",
        headers=auth_headers,
        json={"action": "resolve", "resolution_summary": "Verified."},
    )

    closed_alert = client.get(f"/api/alerts/{alert['id']}", headers=auth_headers).get_json()["data"]
    assert closed_alert["status"] == "RESOLVED"


def test_incident_can_be_reassigned(client, auth_headers):
    incident = client.post(
        "/api/incidents", headers=auth_headers, json={"title": "Reassignment test"}
    ).get_json()["data"]

    analysts = client.get("/api/incidents", headers=auth_headers).get_json()["filters"]["analysts"]
    target = next(user for user in analysts if user["role"] == "ANALYST")

    response = client.put(
        f"/api/incidents/{incident['id']}", headers=auth_headers, json={"assigned_to": target["id"]}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["assigned_to"] == target["id"]


def test_incidents_can_be_filtered_by_status(client, auth_headers):
    client.post("/api/incidents", headers=auth_headers, json={"title": "Filter test case"})
    body = client.get("/api/incidents?status=NEW", headers=auth_headers).get_json()

    assert all(row["status"] == "NEW" for row in body["data"])


def test_unknown_incident_returns_404(client, auth_headers):
    response = client.get("/api/incidents/999999", headers=auth_headers)
    assert response.status_code == 404


def test_incident_endpoints_require_authentication(client):
    assert client.get("/api/incidents").status_code == 401
    assert client.post("/api/incidents", json={"title": "x"}).status_code == 401
