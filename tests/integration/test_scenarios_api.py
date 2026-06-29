def _register_and_login(client, email: str = "user@example.com") -> None:
    client.post(
        "/auth/register",
        data={"email": email, "password": "password123"},
        follow_redirects=False,
    )


def test_list_scenarios_requires_auth(client) -> None:
    response = client.get("/api/scenarios")
    assert response.status_code == 401


def test_scenario_crud_and_clone(client) -> None:
    _register_and_login(client)

    listed = client.get("/api/scenarios")
    assert listed.status_code == 200
    initial_count = len(listed.json())
    assert initial_count >= 6

    created = client.post(
        "/api/scenarios",
        json={
            "name": "Custom Interview",
            "purpose": "interview",
            "document_type": "email",
            "system_prompt": "# Custom prompt\nBe concise.",
        },
    )
    assert created.status_code == 201
    scenario_id = created.json()["id"]

    updated = client.patch(
        f"/api/scenarios/{scenario_id}",
        json={"name": "Updated Interview", "system_prompt": "# Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Interview"

    cloned = client.post(f"/api/scenarios/{scenario_id}/clone")
    assert cloned.status_code == 201
    assert cloned.json()["name"].endswith("(copy)")

    deleted = client.delete(f"/api/scenarios/{scenario_id}")
    assert deleted.status_code == 204

    filtered = client.get("/api/scenarios?purpose=interview&document_type=email")
    assert filtered.status_code == 200
    assert all(
        item["purpose"] == "interview" and item["document_type"] == "email"
        for item in filtered.json()
    )
