"""TC-03 / TC-04 / TC-09 / TC-10: event submission, analysis, upload and validation."""
import io

BRUTE_FORCE_PAYLOAD = {
    "source_ip": "203.0.113.66",
    "destination_ip": "10.0.1.20",
    "source_port": 44122,
    "destination_port": 22,
    "protocol": "SSH",
    "event_type": "authentication",
    "request_count": 68,
    "failed_login_attempts": 62,
    "packet_count": 340,
    "bytes_transferred": 41000,
    "connection_duration": 95,
}

NORMAL_PAYLOAD = {
    "source_ip": "10.0.1.42",
    "destination_ip": "10.0.3.10",
    "destination_port": 443,
    "protocol": "HTTPS",
    "event_type": "web_request",
    "request_count": 11,
    "packet_count": 160,
    "bytes_transferred": 190000,
    "connection_duration": 38,
}


def test_list_events_is_paginated(client, auth_headers):
    response = client.get("/api/events?per_page=2", headers=auth_headers)
    body = response.get_json()

    assert response.status_code == 200
    assert len(body["data"]) <= 2
    assert body["pagination"]["per_page"] == 2
    assert body["pagination"]["total"] >= 3


def test_create_event_stores_and_analyses_it(client, auth_headers):
    response = client.post("/api/events", headers=auth_headers, json=NORMAL_PAYLOAD)
    body = response.get_json()

    assert response.status_code == 201
    assert body["data"]["event_id"]
    assert body["data"]["classification"] == "Normal Activity"
    assert body["data"]["event"]["processed"] is True


def test_analyze_returns_a_full_explainable_verdict(client, auth_headers):
    response = client.post("/api/events/analyze", headers=auth_headers, json=BRUTE_FORCE_PAYLOAD)
    data = response.get_json()["data"]

    assert response.status_code == 200
    assert data["classification"] == "Brute Force Attempt"
    assert data["severity"] in ("HIGH", "CRITICAL")
    assert 0 <= data["risk_score"] <= 100
    assert data["reasons"]
    assert data["recommended_action"]
    assert data["persisted"] is True


def test_analyze_raises_an_alert_for_a_threat(client, auth_headers):
    before = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]
    response = client.post("/api/events/analyze", headers=auth_headers, json=BRUTE_FORCE_PAYLOAD)
    after = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]

    assert response.get_json()["data"]["alert"] is not None
    assert after == before + 1


def test_analyze_does_not_raise_an_alert_for_normal_traffic(client, auth_headers):
    before = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]
    response = client.post("/api/events/analyze", headers=auth_headers, json=NORMAL_PAYLOAD)
    after = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]

    assert response.get_json()["data"]["alert"] is None
    assert after == before


def test_critical_detection_opens_an_incident(client, auth_headers):
    response = client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={**BRUTE_FORCE_PAYLOAD, "failed_login_attempts": 400, "request_count": 420},
    )
    data = response.get_json()["data"]

    assert data["severity"] == "CRITICAL"
    assert data["incident"] is not None
    assert data["incident"]["status"] == "NEW"


def test_dry_run_analysis_stores_nothing(client, auth_headers):
    before = client.get("/api/events", headers=auth_headers).get_json()["pagination"]["total"]
    response = client.post(
        "/api/events/analyze?persist=false", headers=auth_headers, json=BRUTE_FORCE_PAYLOAD
    )
    after = client.get("/api/events", headers=auth_headers).get_json()["pagination"]["total"]

    assert response.get_json()["data"]["persisted"] is False
    assert after == before


def test_event_is_linked_to_a_monitored_asset(client, auth_headers):
    response = client.post("/api/events", headers=auth_headers, json=NORMAL_PAYLOAD)
    event = response.get_json()["data"]["event"]

    assert event["asset_id"] is not None
    assert event["asset_name"] == "Test Web Server"


def test_invalid_source_ip_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/analyze", headers=auth_headers, json={"source_ip": "999.999.1.1"}
    )

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "source_ip"


def test_missing_source_ip_is_rejected(client, auth_headers):
    response = client.post("/api/events/analyze", headers=auth_headers, json={"protocol": "TCP"})

    assert response.status_code == 422
    assert "source_ip" in response.get_json()["message"]


def test_out_of_range_port_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={"source_ip": "10.0.1.1", "destination_port": 70000},
    )

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "destination_port"


def test_unknown_protocol_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={"source_ip": "10.0.1.1", "protocol": "TELEPATHY"},
    )

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "protocol"


def test_negative_numeric_value_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={"source_ip": "10.0.1.1", "failed_login_attempts": -5},
    )

    assert response.status_code == 422


def test_non_numeric_value_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={"source_ip": "10.0.1.1", "bytes_transferred": "not-a-number"},
    )

    assert response.status_code == 422


def test_analysis_requires_authentication(client):
    response = client.post("/api/events/analyze", json=BRUTE_FORCE_PAYLOAD)
    assert response.status_code == 401


def test_sample_payloads_are_available(client, auth_headers):
    response = client.get("/api/events/sample", headers=auth_headers)
    samples = response.get_json()["data"]

    assert response.status_code == 200
    assert len(samples) >= 5
    assert all("payload" in sample and "expected" in sample for sample in samples)


# ------------------------------------------------------------------ CSV upload


def _upload(client, headers, content, filename="logs.csv"):
    return client.post(
        "/api/events/upload",
        headers=headers,
        data={"file": (io.BytesIO(content.encode("utf-8")), filename)},
        content_type="multipart/form-data",
    )


def test_csv_upload_analyses_every_row(client, auth_headers, sample_csv):
    response = _upload(client, auth_headers, sample_csv)
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["total_records"] == 4
    assert data["normal_events"] + data["suspicious_events"] == 4
    assert data["suspicious_events"] >= 1
    assert len(data["records"]) == 4
    assert data["rejected_rows"] == 0


def test_csv_upload_creates_alerts(client, auth_headers, sample_csv):
    before = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]
    data = _upload(client, auth_headers, sample_csv).get_json()["data"]
    after = client.get("/api/alerts", headers=auth_headers).get_json()["pagination"]["total"]

    assert data["alerts_created"] >= 1
    assert after == before + data["alerts_created"]


def test_csv_upload_reports_invalid_rows_without_failing(client, auth_headers, invalid_csv):
    response = _upload(client, auth_headers, invalid_csv)
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["total_records"] == 1
    assert data["rejected_rows"] == 2
    assert any("valid IPv4" in row["error"] for row in data["row_errors"])


def test_empty_file_upload_is_rejected(client, auth_headers):
    response = _upload(client, auth_headers, "")

    assert response.status_code == 422
    assert "empty" in response.get_json()["message"].lower()


def test_header_only_csv_is_rejected(client, auth_headers):
    response = _upload(client, auth_headers, "timestamp,source_ip,protocol\n")

    assert response.status_code == 422
    assert "no data rows" in response.get_json()["message"].lower()


def test_csv_without_source_ip_column_is_rejected(client, auth_headers):
    response = _upload(client, auth_headers, "timestamp,protocol\n2026-01-01,TCP\n")

    assert response.status_code == 422
    assert "source_ip" in response.get_json()["message"]


def test_wrong_file_extension_is_rejected(client, auth_headers):
    response = _upload(client, auth_headers, "anything", filename="payload.exe")

    assert response.status_code == 422
    assert ".csv" in response.get_json()["message"]


def test_upload_without_a_file_part_is_rejected(client, auth_headers):
    response = client.post(
        "/api/events/upload", headers=auth_headers, data={}, content_type="multipart/form-data"
    )

    assert response.status_code == 422


def test_upload_requires_authentication(client, sample_csv):
    response = _upload(client, {}, sample_csv)
    assert response.status_code == 401


def test_event_can_be_deleted(client, auth_headers):
    event_id = client.post("/api/events", headers=auth_headers, json=NORMAL_PAYLOAD).get_json()[
        "data"
    ]["event_id"]

    deleted = client.delete(f"/api/events/{event_id}", headers=auth_headers)
    missing = client.get(f"/api/events/{event_id}", headers=auth_headers)

    assert deleted.status_code == 200
    assert missing.status_code == 404


def test_unknown_event_returns_404(client, auth_headers):
    response = client.get("/api/events/999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.get_json()["error"] == "NOT_FOUND"
