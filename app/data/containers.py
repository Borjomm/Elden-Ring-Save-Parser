from dataclasses import dataclass

@dataclass(frozen=True)
class Delta:
    event_id: int
    offset: int
    val: bool