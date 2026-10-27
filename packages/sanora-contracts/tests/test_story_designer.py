from sanora_contracts import StoryDesignerResponse


def test_story_designer_response_accepts_agentcore_json() -> None:
    response = StoryDesignerResponse.model_validate(
        {
            "scenario": "A forest path",
            "story_states": {
                "0": {
                    "event": "A door opens",
                    "protagonist_decision": "Enter",
                }
            },
            "grammar_progress": [
                {
                    "grammar_concept_code": "present_tense",
                    "identified": True,
                    "total_findings": 2,
                }
            ],
        }
    )

    assert response.story_states[0].event == "A door opens"
    assert response.grammar_progress[0].total_findings == 2
