from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple


class SearchStrategy(ABC):

    @abstractmethod
    def find(self, user_query: str) -> List[Tuple[str, str, str, str]]:
        raise NotImplementedError
