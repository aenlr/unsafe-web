
def abbrev_filter(value: str, maxlen=40):
    """Return the first line of a string abbreviated to ``maxlen`` characters.

    The result will have an ellipsis appended if truncated by leaving out lines
    or truncating the first line.
    """
    if not value:
        return value
    try:
        i = value.index('\n')
        clipped = i + 1 < len(value)
        value = value[:i]
    except ValueError:
        clipped = False

    if value.endswith(':'):
        value = value[:-1]
        clipped = True

    if len(value) > maxlen:
        value = value[0:maxlen]
        clipped = True

    return value + '\u2026' if clipped else value
