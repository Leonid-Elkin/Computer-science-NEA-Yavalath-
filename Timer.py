from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtGui import QGuiApplication

class PlayerTimer(QWidget):
    timeExpired = pyqtSignal()

    def __init__(self, duration=60, borderColor=QColor("#00C8FF"),
                 borderWidth=0, fillColor=QColor("#000000"),
                 textColor=QColor("white"), parent=None):
        super().__init__(parent)
        self.originalDuration = duration  # Always store what was passed
        self.duration = duration if duration != 500 else -1  # -1 means infinite
        self.remaining = self.duration if self.duration != -1 else 0

        self.borderColor = borderColor
        self.borderWidth = borderWidth
        self.fillColor = fillColor
        self.textColor = textColor
        self.setMinimumSize(self.standardised(300), self.standardised(100))

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    def start(self):
        if self.duration != -1:
            self.timer.start()
        self.update()

    def stop(self):
        self.timer.stop()
        self.update()

    def reset(self, duration=None):
        if duration is not None:
            self.originalDuration = duration
            self.duration = duration if duration != 500 else -1

        self.remaining = self.duration if self.duration != -1 else 0
        self.timer.stop()
        self.update()

    def _tick(self):
        if self.duration == -1:
            return

        if self.remaining > 0:
            self.remaining -= 1
            self.update()
        else:
            self.timer.stop()
            self.timeExpired.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(self.borderWidth, self.borderWidth,
                                    -self.borderWidth, -self.borderWidth)

        painter.setBrush(QBrush(self.fillColor))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)

        pen = QPen(self.borderColor, self.borderWidth)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 15, 15)

        painter.setPen(self.textColor)
        font = QFont("Arial", self.standardised(40), QFont.Bold)
        painter.setFont(font)
        text = self._formatTime()
        painter.drawText(rect, Qt.AlignCenter, text)

    def _formatTime(self):
        if self.duration == -1:
            return "----"
        minutes = self.remaining // 60
        secs = self.remaining % 60
        return f"{minutes:02}:{secs:02}"
    
    def standardised(self, value):
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.screenWidth = geometry.width()
        self.screenHeight = geometry.height()
        return int(value * self.screenHeight / 1600)
