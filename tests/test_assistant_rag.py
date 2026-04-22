from app.rag import retriever


def test_assistant_recovers_after_transient_generation_failure(monkeypatch):
    query = "Give me a 5-step employee response playbook for suspected phishing."

    def fail_once(_prompt):
        raise RuntimeError("temporary provider failure")

    monkeypatch.setattr(retriever, "_generate_answer", fail_once)

    first_response = retriever.get_rag_response(query)
    assert "AI provider is unavailable right now" in first_response

    monkeypatch.setattr(retriever, "_generate_answer", lambda _prompt: "recovered answer")

    second_response = retriever.get_rag_response(query)
    assert second_response == "recovered answer"