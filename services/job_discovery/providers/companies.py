"""
Company Registry.
"""

from services.job_discovery.providers.contracts import ProviderConfig

COMPANIES: list[ProviderConfig] = [
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
