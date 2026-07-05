import json
from playwright.sync_api import sync_playwright


def handle_response(response):
    if response.url.endswith("/jobs") and response.status == 200:
        print("\nFOUND JOB API")
        print(response.url)

        try:
            data = response.json()

            print("\n========== TOP LEVEL KEYS ==========\n")
            print(data.keys())

            print("\n========== SAMPLE RESPONSE ==========\n")
            print(json.dumps(data, indent=2)[:5000])

        except Exception as e:
            print(e)


with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.on("response", handle_response)

    page.goto(
        "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        wait_until="networkidle",
    )

    input("Search for 'Data Scientist' and press ENTER...")

    browser.close()