from abc import ABC, abstractmethod
from typing import List, Dict

class ListingsService(ABC):
    @abstractmethod
    def get_all_properties(self) -> List[Dict]:
        pass

    @abstractmethod
    def get_filtered_listings(self, filters: Dict) -> List[Dict]:
        pass