import requests

url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"

response = requests.post(
    url,
    json={
        "limit": 20,
        "offset": 0,
        "searchText": "Data Scientist"
    }
)

print(response.status_code)
print(response.text[:1000])