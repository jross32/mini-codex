"""ETL Extractor base classes."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional


class Extractor(ABC):
    """Base class for data extractors."""

    def __init__(self, source: str):
        """Initialize extractor."""
        self.source = source
        self.row_count = 0
        self.error_count = 0

    @abstractmethod
    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """Extract data from source."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return {
            "source": self.source,
            "rows": self.row_count,
            "errors": self.error_count,
        }


class CSVExtractor(Extractor):
    """Extract data from CSV files."""

    def __init__(self, source: str, delimiter: str = ","):
        """Initialize CSV extractor."""
        super().__init__(source)
        self.delimiter = delimiter

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """Extract CSV data."""
        try:
            import csv
            with open(self.source, 'r') as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                for row in reader:
                    self.row_count += 1
                    yield row
        except Exception as e:
            self.error_count += 1
            print(f"Error extracting from CSV: {e}")


class JSONExtractor(Extractor):
    """Extract data from JSON files."""

    def extract(self) -> Generator[Dict[str, Any], None, None]:
        """Extract JSON data."""
        try:
            import json
            with open(self.source, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        self.row_count += 1
                        yield item
                elif isinstance(data, dict):
                    yield data
                    self.row_count = 1
        except Exception as e:
            self.error_count += 1
            print(f"Error extracting from JSON: {e}")
