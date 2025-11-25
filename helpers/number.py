import random


def denumerize(value: str):
    units = {"K": 1_000, "M": 1_000_000,
             "B": 1_000_000_000, "T": 1_000_000_000_000}

    value = value.upper().replace(",", "")
    for unit, factor in units.items():
        if value.endswith(unit):
            return int(float(value[:-1]) * factor)

    return int(float(value))


def random_number(minimum=1, maximum=2):
    return random.randrange(minimum, maximum)
