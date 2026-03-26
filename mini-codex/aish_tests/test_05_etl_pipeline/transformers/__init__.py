"""ETL Transformer base classes."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class Transformer(ABC):
    """Base class for data transformers."""

    def __init__(self, name: str):
        """Initialize transformer."""
        self.name = name
        self.processed = 0
        self.errors = 0

    @abstractmethod
    def transform(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a data row."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get transformer statistics."""
        return {
            "name": self.name,
            "processed": self.processed,
            "errors": self.errors,
        }


class DataCleaner(Transformer):
    """Clean and normalize data."""

    def __init__(self, null_value: str = ""):
        """Initialize cleaner."""
        super().__init__("DataCleaner")
        self.null_value = null_value

    def transform(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean row data."""
        try:
            cleaned = {}
            for key, value in row.items():
                if value is None or value == "" or value == self.null_value:
                    cleaned[key] = None
                else:
                    cleaned[key] = str(value).strip()
            self.processed += 1
            return cleaned
        except Exception as e:
            self.errors += 1
            return None


class DataAggregator(Transformer):
    """Aggregate data by key."""

    def __init__(self, group_by: str):
        """Initialize aggregator."""
        super().__init__("DataAggregator")
        self.group_by = group_by
        self.groups: Dict[str, List[Dict]] = {}

    def transform(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Aggregate row into group."""
        try:
            key = row.get(self.group_by)
            if key not in self.groups:
                self.groups[key] = []
            self.groups[key].append(row)
            self.processed += 1
            return row
        except Exception as e:
            self.errors += 1
            return None

    def get_aggregates(self) -> Dict[str, List[Dict]]:
        """Get aggregated data."""
        return self.groups
