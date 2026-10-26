"""TC-02 / TC-08 / TC-12: dashboard, analytics, assets, intelligence, reports, health."""


# ------------------------------------------------------------------ dashboard


def test_dashboard_stats_returns_every_section(client, auth_headers):
    response = client.get("/api/dashboard/stats", headers=auth_headers)
    data = response.get_json()["data"]

    assert response.status_code == 200
    for section in ("totals", "threat_level", "detection_quality", "system_health",
                    "charts", "recent_alerts", "activity_feed"):
        assert section in data, f"missing dashboard section: {section}"


def test_dashboard_totals_are_computed_from_the_database(client, auth_headers):
    totals = client.get("/api/dashboard/stats", headers=auth_headers).get_json()["data"]["totals"]
    events = client.get("/api/events", headers=auth_headers).get_json()["pagination"]["total"]
    assets = client.get("/api/assets", headers=auth_headers).get_json()["pagination"]["total"]

    assert totals["total_events"] == events
    assert totals["monitored_assets"] == assets


def test_dashboard_charts_have_the_expected_series(client, auth_headers):
    charts = client.get("/api/dashboard/stats", headers=auth_headers).get_json()["data"]["charts"]

    for key in ("threats_over_time", "severity_distribution", "category_distribution",
                "events_by_source", "detection_trend", "protocol_distribution"):
        assert key in charts
        assert isinstance(charts[key], list)

    assert {row["severity"] for row in charts["severity_distribution"]} == {
        "LOW", "MEDIUM", "HIGH", "CRITICAL"
    }


def test_threat_level_is_one_of_the_four_bands(client, auth_headers):
    data = client.get("/api/dashboard/threat-level", headers=auth_headers).get_json()["data"]

    assert data["level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert 0 <= data["score"] <= 100
    assert data["basis"]


def test_detection_quality_states_where_the_number_came_from(client, auth_headers):
    quality = client.get("/api/dashboard/stats", headers=auth_headers).get_json()["data"][
        "detection_quality"
    ]

    assert quality["source"] in ("analyst_triage", "model_holdout", "engine_confidence")
    assert quality["label"]
    assert quality["note"], "the figure must always be qualified, never presented bare"


def test_activity_feed_is_newest_first(client, auth_headers):
    feed = client.get("/api/dashboard/activity?limit=10", headers=auth_headers).get_json()["data"]
    timestamps = [item["timestamp"] for item in feed]

    assert timestamps == sorted(timestamps, reverse=True)


def test_analytics_endpoint_returns_aggregates(client, auth_headers):
    data = client.get("/api/analytics?days=30", headers=auth_headers).get_json()["data"]

    assert "averages" in data
    assert "severity_distribution" in data
    assert "hourly_distribution" in data
    assert len(data["hourly_distribution"]) == 24
    assert data["averages"]["analysis_time_ms"] >= 0


def test_dashboard_requires_authentication(client):
    assert client.get("/api/dashboard/stats").status_code == 401


# --------------------------------------------------------------------- assets


def test_assets_are_listed_with_event_counts(client, auth_headers):
    body = client.get("/api/assets", headers=auth_headers).get_json()

    assert body["pagination"]["total"] == 2
    assert all("event_count" in asset for asset in body["data"])


def test_asset_can_be_created(client, auth_headers):
    response = client.post(
        "/api/assets",
        headers=auth_headers,
        json={
            "name": "New Mail Server",
            "ip_address": "10.0.3.40",
            "asset_type": "Mail Server",
            "operating_system": "Ubuntu 22.04",
            "criticality": "HIGH",
        },
    )
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["name"] == "New Mail Server"
    assert data["risk_level"] == "LOW"


def test_duplicate_asset_ip_is_rejected(client, auth_headers):
    response = client.post(
        "/api/assets", headers=auth_headers, json={"name": "Clash", "ip_address": "10.0.3.10"}
    )

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "ip_address"


def test_asset_requires_a_valid_ip(client, auth_headers):
    response = client.post(
        "/api/assets", headers=auth_headers, json={"name": "Bad", "ip_address": "10.0.0"}
    )

    assert response.status_code == 422


def test_asset_requires_a_name(client, auth_headers):
    response = client.post("/api/assets", headers=auth_headers, json={"ip_address": "10.9.9.9"})

    assert response.status_code == 422
    assert response.get_json()["details"]["field"] == "name"


def test_asset_can_be_updated(client, auth_headers):
    asset_id = client.get("/api/assets", headers=auth_headers).get_json()["data"][0]["id"]
    response = client.put(
        f"/api/assets/{asset_id}", headers=auth_headers, json={"status": "QUARANTINED"}
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "QUARANTINED"


def test_asset_risk_rises_after_a_critical_detection(client, auth_headers):
    before = next(
        asset
        for asset in client.get("/api/assets", headers=auth_headers).get_json()["data"]
        if asset["ip_address"] == "10.0.1.20"
    )

    client.post(
        "/api/events/analyze",
        headers=auth_headers,
        json={
            "source_ip": "203.0.113.77",
            "destination_ip": "10.0.1.20",
            "destination_port": 22,
            "protocol": "SSH",
            "event_type": "authentication",
            "failed_login_attempts": 400,
            "request_count": 420,
            "packet_count": 2000,
            "bytes_transferred": 300000,
            "connection_duration": 200,
        },
    )

    after = next(
        asset
        for asset in client.get("/api/assets", headers=auth_headers).get_json()["data"]
        if asset["ip_address"] == "10.0.1.20"
    )

    assert after["risk_score"] > before["risk_score"]
    assert after["risk_level"] == "CRITICAL"


def test_asset_can_be_deleted_and_events_survive(client, auth_headers):
    asset_id = client.post(
        "/api/assets", headers=auth_headers, json={"name": "Temp", "ip_address": "10.7.7.7"}
    ).get_json()["data"]["id"]
    events_before = client.get("/api/events", headers=auth_headers).get_json()["pagination"]["total"]

    response = client.delete(f"/api/assets/{asset_id}", headers=auth_headers)
    events_after = client.get("/api/events", headers=auth_headers).get_json()["pagination"]["total"]

    assert response.status_code == 200
    assert events_after == events_before


def test_asset_endpoints_require_authentication(client):
    assert client.get("/api/assets").status_code == 401
    assert client.post("/api/assets", json={"name": "x", "ip_address": "1.1.1.1"}).status_code == 401


# --------------------------------------------------------- threat intelligence


def test_threat_intelligence_is_marked_simulated(client, auth_headers):
    body = client.get("/api/threat-intelligence", headers=auth_headers).get_json()

    assert body["pagination"]["total"] >= 1
    assert "simulated" in body["notice"].lower()
    assert all(indicator["is_simulated"] for indicator in body["data"])


def test_indicator_status_can_be_changed(client, auth_headers):
    indicator = client.get("/api/threat-intelligence", headers=auth_headers).get_json()["data"][0]
    response = client.put(
        f"/api/threat-intelligence/{indicator['id']}", headers=auth_headers,
        json={"status": "MONITORING"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "MONITORING"


# --------------------------------------------------------------------- threats


def test_threats_are_listed(client, auth_headers):
    body = client.get("/api/threats", headers=auth_headers).get_json()

    assert body["success"] is True
    assert "categories" in body["filters"]


def test_single_threat_includes_its_event(client, auth_headers):
    threats = client.get("/api/threats", headers=auth_headers).get_json()["data"]
    if not threats:
        return
    body = client.get(f"/api/threats/{threats[0]['id']}", headers=auth_headers).get_json()

    assert body["data"]["event"] is not None


# --------------------------------------------------------------------- reports


def test_report_can_be_generated(client, auth_headers):
    response = client.post(
        "/api/reports/generate", headers=auth_headers, json={"days": 30, "report_type": "SUMMARY"}
    )
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["report_code"].startswith("RPT-")
    assert "summary" in data["content"]
    assert data["content"]["recommendations"]


def test_report_rejects_an_invalid_period(client, auth_headers):
    response = client.post("/api/reports/generate", headers=auth_headers, json={"days": 9999})

    assert response.status_code == 422


def test_report_rejects_an_unknown_type(client, auth_headers):
    response = client.post(
        "/api/reports/generate", headers=auth_headers, json={"report_type": "MAGIC"}
    )

    assert response.status_code == 422


def test_report_downloads_in_every_format(client, auth_headers):
    report_id = client.post(
        "/api/reports/generate", headers=auth_headers, json={"days": 7}
    ).get_json()["data"]["id"]

    json_export = client.get(f"/api/reports/{report_id}/download?format=json", headers=auth_headers)
    csv_export = client.get(f"/api/reports/{report_id}/download?format=csv", headers=auth_headers)
    pdf_export = client.get(f"/api/reports/{report_id}/download?format=pdf", headers=auth_headers)

    assert json_export.status_code == 200
    assert csv_export.status_code == 200
    assert "CyberGuard AI Security Report" in csv_export.get_data(as_text=True)
    # 200 with a PDF body, or 501 with a clear message if ReportLab is absent.
    assert pdf_export.status_code in (200, 501)
    if pdf_export.status_code == 200:
        assert pdf_export.data.startswith(b"%PDF")


def test_report_preview_does_not_store_anything(client, auth_headers):
    before = client.get("/api/reports", headers=auth_headers).get_json()["pagination"]["total"]
    response = client.get("/api/reports/preview?days=14", headers=auth_headers)
    after = client.get("/api/reports", headers=auth_headers).get_json()["pagination"]["total"]

    assert response.status_code == 200
    assert after == before


# ---------------------------------------------------------------------- system


def test_health_check_is_public(client):
    response = client.get("/api/health")
    data = response.get_json()["data"]

    assert response.status_code == 200
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["detection_engine"]["mode"] in ("hybrid-ml", "hybrid-rules")


def test_system_status_reports_table_counts(client, auth_headers):
    data = client.get("/api/system/status", headers=auth_headers).get_json()["data"]

    assert data["database"]["tables"]["users"] == 3
    assert data["thresholds"]["alert_risk_threshold"] == 26
    assert data["thresholds"]["incident_risk_threshold"] == 76


def test_api_index_lists_endpoints(client):
    data = client.get("/api").get_json()["data"]

    assert data["endpoint_count"] > 20
    paths = {route["path"] for route in data["endpoints"]}
    for expected in ("/api/health", "/api/auth/login", "/api/dashboard/stats",
                     "/api/events/analyze", "/api/alerts", "/api/incidents"):
        assert expected in paths


def test_unknown_route_returns_a_json_404(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"] == "NOT_FOUND"


def test_wrong_method_returns_405(client):
    response = client.delete("/api/health")

    assert response.status_code == 405
    assert response.get_json()["error"] == "METHOD_NOT_ALLOWED"


def test_audit_log_records_every_state_change(client, auth_headers):
    client.post(
        "/api/assets", headers=auth_headers, json={"name": "Audited", "ip_address": "10.8.8.8"}
    )
    logs = client.get("/api/audit-logs", headers=auth_headers).get_json()["data"]
    actions = {entry["action"] for entry in logs}

    assert "ASSET_CREATED" in actions
    assert "LOGIN_SUCCESS" in actions
