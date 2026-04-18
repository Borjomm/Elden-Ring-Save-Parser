from dataclasses import dataclass, replace
import os

@dataclass(frozen=True)
class EventFlag:
    event_id: int
    description: str
    category: str
    tags: str
    screenshot_id: int = -1
    display_val: int = -1

    def __str__(self):
        if self.display_val == 1:
            switch = " (OFF -> ON)"
        elif self.display_val == 0:
            switch = " (ON -> OFF)"
        else:
            switch = ""
        return f"ID {self.event_id} [{self.category} flag] - {self.description}{switch}"
    
    def add_temp_info(self, screenshot_id: int, display_val: int):
        return replace(self, screenshot_id=screenshot_id, display_val=display_val)

@dataclass(frozen=True)
class DisplayedDeltaChange:
    timestamp: int
    screenshot_path: str
    flags: list[EventFlag]

    def __iter__(self):
        for flag in self.flags:
            yield flag

    def __str__(self):
        s = f"{self.timestamp}: Delta Change with {len(self.flags)} flag toggles\nScreenshot: {os.path.abspath(self.screenshot_path)}\n"
        s += '\n'.join(f"\t{str(flag)}" for flag in self.flags)
        return s
    
    def __len__(self):
        return len(self.flags)

@dataclass(frozen=True)
class Delta:
    event_id: int
    offset: int
    val: bool