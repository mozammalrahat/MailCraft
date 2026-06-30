def test_dashboard_requires_auth(client) -> None:
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_register_and_login_flow(client) -> None:
    register = client.post(
        "/auth/register",
        data={"email": "user@example.com", "password": "password123"},
        follow_redirects=False,
    )
    assert register.status_code == 303

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code == 200

    logout = client.post("/auth/logout", follow_redirects=False)
    assert logout.status_code == 303

    blocked = client.get("/dashboard", follow_redirects=False)
    assert blocked.status_code == 303


def test_dashboard_search_accepts_empty_select_filters(client) -> None:
    client.post(
        "/auth/register",
        data={"email": "search@example.com", "password": "password123"},
        follow_redirects=False,
    )

    response = client.get(
        "/dashboard",
        params={
            "purpose": "",
            "document_type": "",
            "scenario_id": "",
            "q": "Acme",
        },
    )

    assert response.status_code == 200
    assert "Acme" in response.text
