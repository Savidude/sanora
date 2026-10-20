from ..state import TutorState, load_story_states


def initialise(state: TutorState) -> dict:
    """Assign story states once at the start of a session."""
    return {
        "story_states": load_story_states(),
        "current_story_state": state.get("current_story_state", 1),
        "scenario": "Savidu is riding his bike to work when all of a sudden a random stranger jumps in front of him and hands him a note, and runs away.",
        "fallback_context": None,
        "fallback_attempts": 0,
    }


def route_from_start(state: TutorState) -> str:
    """Run initialise only when story_states has not been assigned yet."""
    if not state.get("story_states"):
        return "initialise"
    return direct_message(state)


def direct_message(state: TutorState) -> str:
    """Direct message to the proper node"""
    if len(state.get("messages", [])) == 0:
        return "facilitator"
    else:
        return "state_evaluator"
