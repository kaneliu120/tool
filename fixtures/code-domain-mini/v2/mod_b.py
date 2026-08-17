def handoff(project: str) -> dict:
    """Build a handoff payload for project."""
    return {"project": project, "kind": "handoff"}
