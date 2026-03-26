"""Narrative helpers for lightweight scene rendering."""
def scene_line(theme, turn):
    """Build a short scene line for the current turn."""
    beats = [
        'wind carries static through broken pylons',
        'a distant bell answers your footsteps',
        'dust glows like embers under moonlight',
    ]
    beat = beats[turn % len(beats)]
    return f"Turn {turn + 1}: In the {theme['archetype']}, {beat}."

