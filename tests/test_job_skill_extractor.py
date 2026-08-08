from services.llm.job_skill_extractor import JobSkillExtractor


class StubGroqClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.prompts: list[str] = []

    def chat(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        return self.response


def test_job_skill_extractor_uses_injected_client_and_normalizes_strings():
    client = StubGroqClient({"skills": [" Python ", "", 42, "Docker"]})
    extractor = JobSkillExtractor(client=client)

    assert extractor.extract("Build data services") == ["Python", "Docker"]
    assert "Build data services" in client.prompts[0]


def test_job_skill_extractor_skips_llm_for_empty_descriptions():
    client = StubGroqClient({"skills": ["Python"]})
    extractor = JobSkillExtractor(client=client)

    assert extractor.extract("   ") == []
    assert client.prompts == []


def test_job_skill_extractor_is_not_limited_to_technical_roles():
    client = StubGroqClient({"skills": ["Patient assessment", "CPR certification"]})
    extractor = JobSkillExtractor(client=client)

    assert extractor.extract("Registered nurse in an acute care unit") == [
        "Patient assessment",
        "CPR certification",
    ]
    assert "technical skills only" not in client.prompts[0].casefold()
    assert "non-technical occupations" in client.prompts[0]
