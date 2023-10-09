"""Restore previous successful deployed configuration."""

from nua.orchestrator.state_journal import StateJournal, restore_from_state_journal


def restore_active_state() -> None:
    """Restore to the most recent deployment configuration that did succeed."""
    state = StateJournal()
    state.read_current_state()
    restore_from_state_journal(state)
