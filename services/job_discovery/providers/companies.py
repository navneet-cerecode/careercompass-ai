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
        "id": "the_muse",
        "name": "The Muse",
        "platform": "the_muse",
        "enabled": bool(settings.the_muse_api_key),
        "priority": 7,
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
        "id": "appian",
        "name": "Appian",
        "platform": "greenhouse",
        "enabled": True,
        "priority": 40,
        "board_token": "appian",
    },
    {
        "id": "blenheim-chalcot-india",
        "name": "Blenheim Chalcot India",
        "platform": "greenhouse",
        "enabled": True,
        "priority": 40,
        "board_token": "blenheimchalcotindia",
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
