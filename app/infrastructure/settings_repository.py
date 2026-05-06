from pathlib import Path
from typing import List, Tuple, Optional, cast
from PySide6.QtCore import QSettings, QStandardPaths

from app.infrastructure.settings_dialog import WikiSettingsDialog
from app.data.consts import APP, CREATOR
from app.data.containers import WikiSettingsContainer

class SettingsRepository:
    def __init__(self, org_name: str = CREATOR, app_name: str = APP):
        self.settings = QSettings(org_name, app_name)

    def get_default_save_path(self) -> Optional[str]:
        """The logic you wrote is great—kept it exactly the same."""
        # Standard Roaming/EldenRing path
        roaming_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)).parent
        elden_ring_dir = roaming_dir / 'EldenRing'
        
        if not elden_ring_dir.exists():
            return None
            
        steam_id_folders = [f for f in elden_ring_dir.iterdir() if f.is_dir()]
        most_recent_mtime = 0
        found_path = None
        
        for folder in steam_id_folders:
            # Check for both standard and seamless coop extensions
            for ext in ['.sl2', '.co2']:
                save_file = elden_ring_dir / folder / f'ER0000{ext}'
                if save_file.exists():
                    mtime = save_file.stat().st_mtime
                    if mtime > most_recent_mtime:
                        most_recent_mtime = mtime
                        found_path = str(save_file)
                        
        return found_path
    
    def set_event_logging(self, val: bool):
        self.settings.setValue("event_logging", val)

    def get_event_logging(self) -> bool:
        return self.settings.value("event_logging", defaultValue=False, type=bool) # pyright: ignore[reportReturnType]
    
    def set_item_logging(self, val: bool):
        self.settings.setValue("item_logging", val)

    def get_item_logging(self) -> bool:
        return self.settings.value("item_logging", defaultValue=False, type=bool) # pyright: ignore[reportReturnType]

    def save_session(self, path: str, slot: int):
        """Saves the current file and slot to registry."""
        self.settings.setValue("most_recent_path", path)
        self.settings.setValue("most_recent_slot", slot)
        self._add_to_recent_list(path, slot)

    def get_last_path(self) -> Optional[str]:
        path = self.settings.value("most_recent_path")
        return path if path else self.get_default_save_path()

    def get_last_slot(self) -> int:
        val = self.settings.value("most_recent_slot", 0)
        return int(cast(int, val))

    def get_recent_list(self) -> List[Tuple[str, int]]:
        return cast(List[Tuple[str, int]], self.settings.value("recent_list", []))

    def _add_to_recent_list(self, path: str, slot: int):
        recent = self.get_recent_list()
        # Remove if exists to move to top
        recent = [entry for entry in recent if entry[0] != path]
        recent.insert(0, (path, slot))
        # Keep top 5
        self.settings.setValue("recent_list", recent[:5])

    def get_or_prompt_wiki_settings(self):
        r_path = cast(str, self.settings.value("root_path", ""))
        p_path = cast(str, self.settings.value("parse_path", ""))
        d_path = cast(str, self.settings.value("db_path", ""))
        if r_path and p_path and d_path:
            return WikiSettingsContainer(r_path, p_path, d_path)
        return self.prompt_wiki_settings()

    def prompt_wiki_settings(self):
        r_path = cast(str, self.settings.value("root_path", ""))
        p_path = cast(str, self.settings.value("parse_path", ""))
        d_path = cast(str, self.settings.value("db_path", ""))
        root_path = Path(r_path) if r_path else None
        parse_path = Path(root_path if root_path else "", p_path) if p_path else None
        db_path = Path(d_path) if d_path else None
        dialog = WikiSettingsDialog(None, root_path, parse_path, db_path)
        if dialog.exec():
            container = dialog.get_settings()
            self.settings.setValue("root_path", container.root_path)
            self.settings.setValue("parse_path", container.parse_path)
            self.settings.setValue("db_path", container.db_path)
            return container
        return None

