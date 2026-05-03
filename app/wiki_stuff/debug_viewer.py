from PySide6.QtWidgets import QWidget, QHBoxLayout, QTextBrowser, QVBoxLayout, QLabel, QGroupBox, QScrollArea, QCheckBox
from PySide6.QtCore import Qt, QUrl
from pathlib import Path
from typing import cast
import frontmatter

from app.wiki_stuff.wiki_engine import EldenWikiEngine

class WikiDebugViewer(QWidget):
    def __init__(self, workspace_path):
        super().__init__()
        self.workspace_path = workspace_path
        self.setWindowTitle("Elden Wiki - Debug Viewer")
        self.resize(1000, 600)

        # State Variables
        self.current_markdown = ""
        self.hidden_markdown = ""
        self.current_state = {"events": {}, "items": {}}

        self.setup_ui()

        self.viewer.anchorClicked.connect(self.on_link_clicked)

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # ================= LEFT: HTML VIEWER =================
        self.viewer = QTextBrowser()
        self.viewer.setOpenLinks(False) # We will intercept link clicks later
        self.viewer.setStyleSheet("background-color: #000000; font-size: 14px; padding: 10px;")
        
        main_layout.addWidget(self.viewer, stretch=3) # Takes up 75% of screen

        # ================= RIGHT: FLAG CONTROLS =================
        right_panel = QWidget()
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title for the panel
        self.panel_title = QLabel("<b>Page Context Flags</b>")
        self.right_layout.addWidget(self.panel_title)

        # A GroupBox to hold the dynamically generated checkboxes
        self.flags_group = QGroupBox("Detected Requirements")
        self.flags_layout = QVBoxLayout(self.flags_group)
        self.right_layout.addWidget(self.flags_group)

        # Wrap the right panel in a Scroll Area (in case there are many flags)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(right_panel)
        scroll_area.setMinimumWidth(250)

        main_layout.addWidget(scroll_area, stretch=1) # Takes up 25% of screen

    def on_link_clicked(self, url: QUrl):
        """Intercepts wiki:// links and searches the hard drive."""
        href = url.toString()
        
        if href.startswith("wiki:"):
            # Extract the filename (e.g., "Radahn" from "wiki://Radahn")
            target_name = href.replace("wiki:", "")
            
            # Since this is Debug Mode: Search the OS for the file
            # Obsidian files are named target_name.md
            matches = list(self.workspace_path.rglob(f"{target_name}.md"))
            
            if matches:
                # Load the first match found
                self.load_page(matches[0])
            else:
                # Optional: Show a 404 in the viewer if file missing
                print(f"Debug: {target_name}.md not found in {self.workspace_path}")
        
        elif href.startswith("http"):
            # Open web links in actual browser
            import webbrowser
            webbrowser.open(href)

    def load_page(self, filepath: Path):
        """Called when a user double-clicks a file in the Tree."""
        if not filepath.exists():
            self.viewer.setHtml(f"<h1>Error 404</h1><p>File not found: {filepath}</p>")
            return

        # 1. Read file and strip YAML
        post = frontmatter.load(str(filepath))
        self.current_markdown = post.content
        self.hidden_markdown = post.metadata.get("hidden")
        self.unlock_ids = cast(list[str], post.metadata.get("unlock_ids"))
        

        # 2. Extract IDs from the raw markdown
        discovered_ids = EldenWikiEngine.extract_all_ids(self.current_markdown, self.unlock_ids)

        # 3. Initialize the State Dict (Set everything to True)
        self.current_state = {"events": {}, "items": {}}
        for category, ids in discovered_ids.items():
            for obj_id in ids:
                self.current_state[category][obj_id] = True

        # 4. Rebuild the Checkbox UI
        self.rebuild_checkbox_menu()

        # 5. Render the HTML
        self.render_preview()

    def rebuild_checkbox_menu(self):
        """Clears old checkboxes and generates new ones based on current_state."""
        # 1. Safely clear the existing layout
        while self.flags_layout.count():
            child = self.flags_layout.takeAt(0)
            if child.widget(): # pyright: ignore[reportOptionalMemberAccess]
                child.widget().deleteLater() # pyright: ignore[reportOptionalMemberAccess]

        # 2. If no flags found, show a message
        if not self.current_state["events"] and not self.current_state["items"]:
            self.flags_layout.addWidget(QLabel("<i>No flags detected in this file.</i>"))
            return

        # 3. Generate Checkboxes
        for category in ["events", "items"]:
            if not self.current_state[category]:
                continue
                
            # Add a small header for the category (e.g., "Events:")
            lbl = QLabel(f"<b>{category.capitalize()}</b>")
            lbl.setStyleSheet("margin-top: 10px;")
            self.flags_layout.addWidget(lbl)

            # Create the checkboxes
            # Sort them so they always appear in the same order
            for obj_id in sorted(self.current_state[category].keys()):
                cb = QCheckBox(f"{category[:-1].capitalize()} {obj_id}")
                cb.setChecked(True) # We initialized state to True

                # IMPORTANT: We use default arguments in the lambda (c=category, i=obj_id)
                # to prevent the "late binding loop" bug in Python!
                cb.toggled.connect(lambda checked, c=category, i=obj_id: self.on_flag_toggled(c, i, checked))
                
                self.flags_layout.addWidget(cb)

    def on_flag_toggled(self, category: str, obj_id: str, is_checked: bool):
        """Updates the state dict and instantly rerenders the HTML."""
        self.current_state[category][obj_id] = is_checked
        self.render_preview()

    def render_preview(self):
        """Processes the markdown with the Engine and sets it to the Viewer."""
        if not self.current_markdown:
            self.viewer.clear()
            return

        # 1. Run your custom logic parser
        html = EldenWikiEngine.process(self.current_markdown, self.current_state, self.hidden_markdown, self.unlock_ids)

        # 3. Display
        self.viewer.setHtml(html)