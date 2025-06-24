from .strict import StrictSearch
from .loose import LooseSearch


def get_strategy(name: str):
    if name and name.lower() == "loose":
        return LooseSearch()
    return StrictSearch()
