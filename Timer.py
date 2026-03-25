from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PyQt5.QtGui import QGuiApplication

class PlayerTimer(QWidget):
    timeExpired = pyqtSignal()
    # Game cyan - #00C8FF

    def __init__(self, duration=60, borderColor=QColor("#00C8FF"),
                 borderWidth=0, fillColor=QColor("#000000"),
                 textColor=QColor("white"), parent=None):
        """
        TIMER WIDGET - USED IN GAME SCREEN TO DISPLAY REMAINING TIME FOR PLAYERS
        timer time resets after each move
        if a timer runs out the respective player loses and the game ends
        """


        super().__init__(parent) #If I want to override this
        self.originalDuration = duration  # Store original duration

        # Duration 500 is special and will be treated as infinity
        # UNUSED
        if duration != 500:
            self.duration = duration
            self.remaining = self.duration
        else:
            self.duration = -1
            self.remaining = 0

        # UI constant setup
        self.borderColor = borderColor
        self.borderWidth = borderWidth
        self.fillColor = fillColor
        self.textColor = textColor
        self.setMinimumSize(self.standardised(300), self.standardised(100))

        # Built in QTimer to handle countdown setup
        self.timer = QTimer(self)
        self.timer.setInterval(1000) # 1 second interval
        self.timer.timeout.connect(self._tick) # Connect timer's timeout signal to the tick method

    def start(self):
        # Starts the timer
        if self.duration != -1:
            self.timer.start()
        self.update()

    def stop(self):
        #Stops timer
        self.timer.stop()
        self.update()

    def reset(self, duration=None):
        """ Resets timer back to original state """

        # Copy pasted section from __init__ to reset timer
        if duration is not None:
            if duration != 500:
                self.duration = duration
                self.remaining = self.duration
            else:
                self.duration = -1
                self.remaining = 0
        
        # In every case the timer will need to be stopped straight after the reset
        self.timer.stop()
        self.update()

    def _tick(self):
        """ Method to update the remaining time in seconds"""
        if self.duration == -1:
            return

        if self.remaining > 0:
            self.remaining -= 1
            self.update()
        else:
            # If timer reaches zero then stop timer and emit a signal
            self.timer.stop()
            self.timeExpired.emit()

    def paintEvent(self, event):
        """PaintEvent - PyQT built in method to handle customisation of widgets - autimatically called every time the widget is updated"""
        painter = QPainter(self)
        #Make things look smoother
        painter.setRenderHint(QPainter.Antialiasing)

        #Main body
        rect = self.rect().adjusted(self.borderWidth, self.borderWidth,
                                    -self.borderWidth, -self.borderWidth)

        painter.setBrush(QBrush(self.fillColor))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 15, 15)

        #Border
        pen = QPen(self.borderColor, self.borderWidth)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 15, 15)

        #Text
        painter.setPen(self.textColor)
        font = QFont("Arial", self.standardised(40), QFont.Bold)
        painter.setFont(font)
        text = self._formatTime()
        painter.drawText(rect, Qt.AlignCenter, text)

    def _formatTime(self):
        """
        Turns an integer number of seconds into a MM:SS format to be displayed on the timer widget.
        """
        if self.duration == -1:
            return "----"
        minutes = self.remaining // 60
        secs = self.remaining % 60
        return f"{minutes:02}:{secs:02}"
    
    def standardised(self, value):
        "Simple resolution handler that scales a value based on the screen height, assuming a base resolution of 1600x900"
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.screenWidth = geometry.width()
        self.screenHeight = geometry.height()
        return int(value * self.screenHeight / 1600)
