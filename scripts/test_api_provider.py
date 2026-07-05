import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://jsearch.p.rapidapi.com/search-v2"

headers = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}

params = {
    "query": "Machine Learning Engineer jobs in India",
    "page": "1",
    "num_pages": "1",
    "country": "in",
    "date_posted": "all",
}

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=30,
)

print("Status Code:", response.status_code)

try:
    payload = response.json()

    print(
        json.dumps(
            payload,
            indent=2,
        )[:6000]
    )

except Exception:

    print(response.text)