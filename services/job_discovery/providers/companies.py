"""
Company Registry.
"""

from core.config import settings
from services.job_discovery.providers.contracts import ProviderConfig

COMPANIES: list[ProviderConfig] = [
    {
        "id": "adzuna",
        "name": "Adzuna",
        "platform": "adzuna",
        "enabled": bool(settings.adzuna_app_id and settings.adzuna_app_key),
        "priority": 5,
        "country": "in",
    },
    {
        "id": "arbeitnow",
        "name": "Arbeitnow",
        "platform": "arbeitnow",
        "enabled": True,
        "priority": 10,
    },
    {
        "id": "nvidia",
        "name": "NVIDIA",
        "platform": "workday",
        "enabled": True,
        "priority": 100,
        "careers_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        "api_url": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
    },
    {
        "id": "jsearch",
        "name": "JSearch",
        "platform": "jsearch",
        "enabled": True,
        "priority": 1,
        "country": "in",
    },
]
