from dataclasses import dataclass


@dataclass(frozen=True)
class MatchingSelection:
    names: list
    active_names: list
    inactive_names: list
    next_inactive_index: int


@dataclass(frozen=True)
class ScheduleMode:
    name: str
    inactive_per_frame: int


def get_schedule_mode(
    active_count,
    boost_frames_remaining,
    inactive_per_frame_empty,
    inactive_per_frame_active,
    inactive_per_frame_boost,
):
    if active_count == 0:
        return ScheduleMode("empty_scan", inactive_per_frame_empty)
    if boost_frames_remaining > 0:
        return ScheduleMode("boost_scan", inactive_per_frame_boost)
    return ScheduleMode("steady_scan", inactive_per_frame_active)


def choose_cards_to_match(
    all_card_names,
    debounce_state,
    inactive_index,
    frame_counter,
    locked_refresh_interval,
    inactive_per_frame,
):
    active_names = [
        name
        for name, state in debounce_state.items()
        if state.get("stable_count", 0) > 0
    ]
    active_set = set(active_names)
    inactive_names = [name for name in all_card_names if name not in active_set]

    active_to_check = []
    for name in active_names:
        phase = debounce_state.get(name, {}).get("phase", "DETECTING")
        if phase != "LOCKED" or frame_counter % locked_refresh_interval == 0:
            active_to_check.append(name)

    inactive_to_check = []
    next_inactive_index = inactive_index
    if inactive_names and inactive_per_frame > 0:
        if next_inactive_index >= len(inactive_names):
            next_inactive_index = 0
        for i in range(min(inactive_per_frame, len(inactive_names))):
            idx = (next_inactive_index + i) % len(inactive_names)
            inactive_to_check.append(inactive_names[idx])
        next_inactive_index = (next_inactive_index + len(inactive_to_check)) % len(inactive_names)

    selected = list(dict.fromkeys(active_to_check + inactive_to_check))
    return MatchingSelection(
        names=selected,
        active_names=active_names,
        inactive_names=inactive_names,
        next_inactive_index=next_inactive_index,
    )
