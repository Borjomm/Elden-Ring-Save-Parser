from urllib.parse import unquote

from PySide6.QtWidgets import QWidget, QTextBrowser, QVBoxLayout
from PySide6.QtCore import QUrl

class WikiViewer(QWidget):
    def __init__(self, wiki_callback):
        super().__init__()
        self.wiki_callback = wiki_callback
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # ================= LEFT: HTML VIEWER =================
        self.viewer = QTextBrowser()
        self.viewer.setOpenLinks(False) # We will intercept link clicks later
        self.viewer.setStyleSheet("background-color: #000000; font-size: 14px; padding: 10px;")
        self.viewer.anchorClicked.connect(self.on_link_clicked)
        
        main_layout.addWidget(self.viewer)

    def on_link_clicked(self, url: QUrl):
        """Intercepts wiki:// links and searches the hard drive."""
        href = url.toString()
        
        if href.startswith("wiki:"):
            # Extract the filename (e.g., "Radahn" from "wiki://Radahn")
            encoded_target = href.replace("wiki:", "")
            target_name = unquote(encoded_target)
            self.wiki_callback(target_name)
            
            # Ask wiki tree to load the page
        
        elif href.startswith("http"):
            # Open web links in actual browser
            import webbrowser
            webbrowser.open(href)

    def load_page(self, html):
        self.viewer.setHtml(html)