"""Tests de autenticación y scoping por equipo."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@brickwise.dev"


def test_register_y_login():
    email = _unique_email()
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "secreto-123",
            "name": "Edwin",
            "team_name": f"Equipo-{uuid.uuid4().hex[:8]}",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == email

    login = client.post(
        "/auth/login", json={"email": email, "password": "secreto-123"}
    )
    assert login.status_code == 200
    assert login.json()["access_token"]

    bad = client.post("/auth/login", json={"email": email, "password": "incorrecta"})
    assert bad.status_code == 401


def test_register_email_duplicado():
    email = _unique_email()
    payload = {
        "email": email,
        "password": "secreto-123",
        "name": "Edwin",
        "team_name": "DupTeam",
    }
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409


def test_graphql_exige_autenticacion():
    response = client.post("/graphql", json={"query": "{ projects { id } }"})
    assert response.status_code == 200
    body = response.json()
    assert body["errors"], "debe rechazar la consulta sin token"
    assert "No autenticado" in body["errors"][0]["message"]


def test_proyectos_limitados_al_equipo():
    team_a, team_b = f"TeamA-{uuid.uuid4().hex[:6]}", f"TeamB-{uuid.uuid4().hex[:6]}"
    email_a, email_b = _unique_email(), _unique_email()

    token_a = client.post(
        "/auth/register",
        json={"email": email_a, "password": "secreto-123", "name": "A", "team_name": team_a},
    ).json()["access_token"]
    token_b = client.post(
        "/auth/register",
        json={"email": email_b, "password": "secreto-123", "name": "B", "team_name": team_b},
    ).json()["access_token"]

    created = client.post(
        "/graphql",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "query": """
                mutation {
                    createProject(
                        input: {
                            name: "Lote Chapinero"
                            location: "Bogotá"
                            typology: VIVIENDA
                            areaM2: 1200
                            budgetCop: 4000000000
                        }
                    ) { id name }
                }
            """
        },
    )
    assert created.status_code == 200, created.text
    assert not created.json().get("errors")

    mine = client.post(
        "/graphql",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"query": "{ projects { name } }"},
    ).json()
    theirs = client.post(
        "/graphql",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"query": "{ projects { name } }"},
    ).json()

    assert [p["name"] for p in mine["data"]["projects"]] == ["Lote Chapinero"]
    assert theirs["data"]["projects"] == []
