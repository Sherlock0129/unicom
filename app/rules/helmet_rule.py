from __future__ import annotations

from dataclasses import dataclass

from app.detection.association import HelmetState, PersonObservation


@dataclass
class TrackRuleState:
    violation_started_at: float | None = None
    safe_started_at: float | None = None
    alarm_active: bool = False
    last_seen_at: float = 0.0


@dataclass(frozen=True)
class RuleResult:
    observation: PersonObservation
    alarm_active: bool
    alarm_started_now: bool


class HelmetRuleEngine:
    def __init__(self, alarm_after: float, clear_after: float) -> None:
        self.alarm_after = alarm_after
        self.clear_after = clear_after
        self._states: dict[int, TrackRuleState] = {}

    def evaluate(
        self,
        observation: PersonObservation,
        now: float,
        fallback_id: int,
    ) -> RuleResult:
        track_id = observation.person.track_id
        identity = track_id if track_id is not None else -1_000_000 - fallback_id
        state = self._states.setdefault(identity, TrackRuleState())
        state.last_seen_at = now
        alarm_started_now = False

        is_violation = (
            observation.in_region
            and observation.helmet_state == HelmetState.NO_HELMET
        )

        if is_violation:
            state.safe_started_at = None
            if state.violation_started_at is None:
                state.violation_started_at = now
            if not state.alarm_active and now - state.violation_started_at >= self.alarm_after:
                state.alarm_active = True
                alarm_started_now = True
        else:
            state.violation_started_at = None
            if state.safe_started_at is None:
                state.safe_started_at = now
            if state.alarm_active and now - state.safe_started_at >= self.clear_after:
                state.alarm_active = False

        return RuleResult(observation, state.alarm_active, alarm_started_now)

    def remove_stale_tracks(self, now: float, max_age: float = 5.0) -> None:
        stale = [
            identity
            for identity, state in self._states.items()
            if now - state.last_seen_at > max_age
        ]
        for identity in stale:
            del self._states[identity]

