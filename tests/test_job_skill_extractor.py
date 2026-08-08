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
