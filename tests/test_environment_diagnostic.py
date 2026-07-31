from scripts import test_env


def test_environment_diagnostic_never_prints_secret_values(monkeypatch, capsys):
    groq_secret = "super-secret-groq-value"
    rapidapi_secret = "super-secret-rapidapi-value"
    monkeypatch.setenv("GROQ_API_KEY", groq_secret)
    monkeypatch.setenv("RAPIDAPI_KEY", rapidapi_secret)

    test_env.main()

    output = capsys.readouterr().out
    assert "GROQ_API_KEY configured: yes" in output
    assert "RAPIDAPI_KEY configured: yes" in output
    assert groq_secret not in output
    assert rapidapi_secret not in output
