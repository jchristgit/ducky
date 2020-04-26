from cassiopeia import Region


def as_region(value: str) -> Region:
    return Region(value.upper())
