from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class PrinterStatus:
    state: str = "unknown"
    progress: int = 0
    remaining_minutes: Optional[int] = None
    job_name: str = ""
    detail: str = ""

    def to_dict(self):
        return asdict(self)

class PrinterConnector:
    def read_status(self) -> PrinterStatus:
        raise NotImplementedError
