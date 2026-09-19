import requests
from django.conf import settings

BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": settings.API_SPORTS_KEY
}


def test_fixture(fixture_id):
    url = f"{BASE_URL}/fixtures"

    params = {
        "id": fixture_id
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    print("\n==============================")
    print("FIXTURE")
    print("==============================")

    print(data)

    return data