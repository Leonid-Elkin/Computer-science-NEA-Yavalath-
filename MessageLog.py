from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class MessageLog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Outer box style
        self.setStyleSheet("""
            background-color: #1E1E1E;
            border: 2px solid #00FFFF;
            border-radius: 10px;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Scroll area to contain messages
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: transparent; border: none")
        layout.addWidget(self.scrollArea)

        self.container = QWidget()
        self.scrollLayout = QVBoxLayout(self.container)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollArea.setWidget(self.container)

        self.messages = []

    def send_message(self, msg):
        """Add a plain message to the log, skip empty messages."""
        msg = msg.strip()
        if not msg:
            return

        label = QLabel(msg)
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: #CCCCCC; background: transparent; border: none;")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setWordWrap(True)

        self.scrollLayout.addWidget(label)
        self.messages.append(label)

        # Keep only the last 500 messages
        if len(self.messages) > 500:
            old_label = self.messages.pop(0)
            old_label.deleteLater()

        # Scroll to bottom
        self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        )
