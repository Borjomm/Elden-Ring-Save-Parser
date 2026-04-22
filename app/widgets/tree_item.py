from PySide6.QtGui import QStandardItem, QColor
from PySide6.QtCore import Qt

from app.core.app_state import EventBus
from app.util.animation import flash_item
from app.data.consts import QT_GREEN, QT_RED, QT_YELLOW

class ExpandableItem(QStandardItem):
    def __init__(self, ui_callback, name: str = ""):
        super().__init__(name)
        self.ui_callback = ui_callback

    def flash(self, color: QColor, duration: int = 2000):
        flash_item(self.model(), self.index(), color, duration) #TODO: Maybe add entire flash_item logic here?

    def request_expand(self):
        parent = self.parent()
        if isinstance(parent, ExpandableItem):
            parent.request_expand()
        self.ui_callback(self)

class EventDisplayItem(ExpandableItem):
    def __init__(self, ui_callback, dispatcher: EventBus, name: str, event_id: int):
        super().__init__(ui_callback, name)
        self.dispatcher = dispatcher
        self.setEditable(False)
        self.setCheckable(False)
        self.setCheckState(Qt.CheckState.Unchecked)
        self.event_id = event_id
    
        self.dispatcher.subscribe(self.event_id, self.on_offset_changed)

    def on_offset_changed(self, new_val: bool):
        new_state = Qt.CheckState.Checked if new_val else Qt.CheckState.Unchecked
        if new_state == self.checkState():
            return
        self.setCheckState(new_state)
        parent = self.parent()
        if isinstance(parent, ExpandableItem):
            parent.request_expand()
        if isinstance(parent, RegionItem):
            parent.child_changed(new_val)
        
        color = QT_GREEN if new_val else QT_RED
        self.flash(color)




class RegionItem(ExpandableItem):
    def __init__(self, ui_callback, dispatcher: EventBus, region_name: str):
        super().__init__(ui_callback)
        self.dispatcher = dispatcher
        self.setEditable(False)
        self._added = False
        self._removed = False
        self.region_name = region_name
        self.dispatcher.cycle_finished.connect(self.clean)

    def child_changed(self, val: bool):
        if val:
            self._added = True
        else:
            self._removed = True

    def update_count(self):
        total = self.rowCount()
        checked = sum(1 for i in range(total) if self.child(i).checkState() == Qt.CheckState.Checked)
        self.setText(f"{self.region_name} ({checked}/{total})")

    def clean(self):
        if not self._added and not self._removed:
            return
        self.update_count()


class BossItem(EventDisplayItem):
    def __init__(self, ui_callback, dispatcher: EventBus, boss_name: str, event_id: int, remembrance: bool, dlc: bool, wiki_link: str):
        super().__init__(ui_callback, dispatcher, boss_name, event_id)
        self.remembrance = remembrance
        self.dlc = dlc
        self.link = wiki_link

class GraceItem(EventDisplayItem):
    def __init__(self, ui_callback, dispatcher: EventBus, grace_name: str, event_id: int, dlc: bool):
        super().__init__(ui_callback, dispatcher, grace_name, event_id)
        self.dlc = dlc

        
        

    
