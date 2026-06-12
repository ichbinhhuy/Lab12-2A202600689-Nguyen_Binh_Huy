from __future__ import annotations


def test_recommend_returns_ranked_results(client):
    test_client, _ = client
    response = test_client.post(
        "/api/recommend",
        json={
            "selected_seed_cafe_ids": ["cafe_001"],
            "excluded_result_cafe_ids": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"]
    assert len(payload["results"]) == 3
    assert payload["results"][0]["similarity_score"] >= payload["results"][1]["similarity_score"]


def test_recommend_handles_exhausted_results(client):
    test_client, _ = client
    response = test_client.post(
        "/api/recommend",
        json={
            "selected_seed_cafe_ids": ["cafe_001"],
            "excluded_result_cafe_ids": [
                "cafe_001",
                "cafe_002",
                "cafe_003",
                "cafe_004",
                "cafe_005",
                "cafe_006",
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["results"] == []
    assert payload["fallback_message"] is not None


def test_recommend_excludes_selected_seed_cafes_from_results(client):
    test_client, _ = client
    response = test_client.post(
        "/api/recommend",
        json={
            "selected_seed_cafe_ids": ["cafe_001", "cafe_002"],
            "excluded_result_cafe_ids": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    result_ids = {item["id"] for item in payload["results"]}

    assert "cafe_001" not in result_ids
    assert "cafe_002" not in result_ids
