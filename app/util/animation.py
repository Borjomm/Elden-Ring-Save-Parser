from PySide6.QtCore import QVariantAnimation, QEasingCurve, QPersistentModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

def flash_widget(widget: QWidget, start_color=QColor(0, 100, 0, 150), duration: int = 2000, curve: QEasingCurve.Type = QEasingCurve.Type.Linear):
    anim = QVariantAnimation(widget)
    anim.setDuration(duration)
    anim.setStartValue(start_color)
    anim.setEndValue(QColor(0, 0, 0, 0))
    anim.setEasingCurve(curve)

    def update_style(color):
        # We use rgba() to support transparency
        rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
        widget.setStyleSheet(f"background-color: {rgba}; border-radius: 4px;")

    anim.valueChanged.connect(update_style)

    anim.finished.connect(lambda: widget.setStyleSheet(""))

    anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)

def flash_item(model, index, start_color=QColor(0, 100, 0, 150), duration=2000, curve: QEasingCurve.Type = QEasingCurve.Type.Linear):
    """
    Flashes the background of a specific item in a QStandardItemModel.
    """
    # We use a Persistent Index so the animation doesn't "get lost" if the 
    # user types in the search box while the boss is flashing.
    persistent_index = QPersistentModelIndex(index)
    
    anim = QVariantAnimation(model)
    anim.setDuration(duration)
    anim.setStartValue(start_color)
    anim.setEndValue(QColor(0, 0, 0, 0)) # Fades to transparent
    anim.setEasingCurve(curve)

    def update_item_background(color):
        if persistent_index.isValid():
            # Instead of setStyleSheet, we update the BackgroundRole data
            model.setData(persistent_index, color, Qt.ItemDataRole.BackgroundRole)

    anim.valueChanged.connect(update_item_background)
    
    # When finished, clear the background data so it returns to the theme default
    anim.finished.connect(lambda: model.setData(persistent_index, None, Qt.ItemDataRole.BackgroundRole) if persistent_index.isValid() else None)
    
    anim.start(QVariantAnimation.DeletionPolicy.DeleteWhenStopped)