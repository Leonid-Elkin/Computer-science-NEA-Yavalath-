from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSlider, QLabel, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
import math

from UI.Buttons import PlayButton, PauseButton, SkipButton


class MusicControlWidget(QWidget):
    def __init__(self, audioManager, parent=None):
        super().__init__(parent)
        self.audioManager = audioManager
        self.player = self.audioManager.musicPlayer
        self.playlist = self.audioManager.musicPlaylist

        self.setFixedSize(self.standardised(470), self.standardised(140))

        # --- Container frame ---
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.standardised(470), self.standardised(140))

        border = self.standardised(2)
        borderRadius = self.standardised(15)

        self.container.setStyleSheet(f"""
            QFrame {{
                border: {border}px solid #444444;
                border-radius: {borderRadius}px;
                background-color: #222222;
            }}
        """)

        # --- Buttons ---
        self.btnPrevious = SkipButton("previous")
        self.btnNext = SkipButton("next")
        self.btnPlayPause = PlayButton()

        button_size = self.standardised(50)
        self.btnPrevious.setFixedSize(button_size, button_size)
        self.btnNext.setFixedSize(button_size, button_size)
        self.btnPlayPause.setFixedSize(button_size, button_size)

        self.btnPrevious.clicked.connect(self.prevTrack)
        self.btnNext.clicked.connect(self.nextTrack)
        self.btnPlayPause.clicked.connect(self.playPause)

        # --- Position slider and labels ---
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        sliderHeight = self.standardised(8)
        borderRadius = self.standardised(4)
        width = self.standardised(10)
        height = self.standardised(20)
        margin = self.standardised(-6)

        self.positionSlider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {sliderHeight}px;
                background: #444444;
                border-radius: {borderRadius}px;
            }}
            QSlider::handle:horizontal {{
                background: rgb(0, 150, 255);
                border: 1px solid #333;
                width: {width}px;
                height: {height}px;
                margin: {margin}px 0;
                border-radius: 0px;
                transition: background 0.3s;
            }}
            QSlider::handle:horizontal:hover {{
                background: rgb(0, 200, 255);
            }}
        """)

        self.labelElapsed = QLabel("00:00")
        self.labelRemaining = QLabel("-00:00")
        for label in (self.labelElapsed, self.labelRemaining):
            label.setFixedWidth(self.standardised(50))
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: white;")

        # --- Volume slider and label ---
        self.volumeLabel = QLabel("Volume")
        self.volumeLabel.setStyleSheet("color: white;")
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, self.standardised(100))
        self.volumeSlider.setValue(40)  # VLC default
        self.volumeSlider.setFixedWidth(self.standardised(100))
        self.volumeSlider.valueChanged.connect(self.changeVolume)

        self.volumeSlider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: {sliderHeight}px;
                background: #444444;
                border-radius: {borderRadius}px;
            }}
            QSlider::handle:horizontal {{
                background: rgb(0, 150, 255);
                border: 1px solid #333;
                width: {width}px;
                height: {height}px;
                margin: {margin}px 0;
                border-radius: 0px;
                transition: background 0.3s;
            }}
            QSlider::handle:horizontal:hover {{
                background: rgb(0, 200, 255);
            }}
        """)

        # --- Layout ---
        containerLayout = QVBoxLayout(self.container)
        containerLayout.setContentsMargins(self.standardised(15), self.standardised(15), self.standardised(15), self.standardised(15))
        containerLayout.setSpacing(10)

        controlsLayout = QHBoxLayout()
        controlsLayout.setSpacing(self.standardised(15))
        controlsLayout.addStretch()
        controlsLayout.addWidget(self.btnPrevious)
        controlsLayout.addWidget(self.btnPlayPause)
        controlsLayout.addWidget(self.btnNext)
        controlsLayout.addStretch()

        progressLayout = QHBoxLayout()
        progressLayout.setContentsMargins(self.standardised(5), 0, self.standardised(5), 0)
        progressLayout.addWidget(self.labelElapsed)
        progressLayout.addWidget(self.positionSlider)
        progressLayout.addWidget(self.labelRemaining)

        volumeLayout = QHBoxLayout()
        volumeLayout.addWidget(self.volumeLabel)
        volumeLayout.addWidget(self.volumeSlider)
        volumeLayout.addStretch()

        containerLayout.addLayout(controlsLayout)
        containerLayout.addLayout(progressLayout)
        containerLayout.addLayout(volumeLayout)

        fontSize = self.standardised(15)
        self.volumeLabel.setStyleSheet(f"color: white; font-size: {fontSize}px; border: none;")
        self.labelElapsed.setStyleSheet(f"color: white; font-size: {fontSize}px; border: none;")
        self.labelRemaining.setStyleSheet(f"color: white; font-size: {fontSize}px; border: none;")

        # --- Seek tracking ---
        self.isSeeking = False
        self.positionSlider.sliderPressed.connect(self.startSeek)
        self.positionSlider.sliderReleased.connect(self.endSeek)

        # --- Connect to AudioManager (VLC signals) ---
        self.audioManager.positionChanged.connect(self.updatePosition)
        self.audioManager.durationChanged.connect(self.updateDuration)
        self.audioManager.stateChanged.connect(self.updatePlayPauseIcon)

    def prevTrack(self):
        self.playlist.previous()
        self.audioManager.playSoundtrack()

    def nextTrack(self):
        self.playlist.next()
        self.audioManager.playSoundtrack()

    def playPause(self):
        self.audioManager.togglePlayPause()

    def updatePlayPauseIcon(self, playing):
        if playing:
            if not isinstance(self.btnPlayPause, PauseButton):
                self._replacePlayPauseButton(PauseButton())
        else:
            if not isinstance(self.btnPlayPause, PlayButton):
                self._replacePlayPauseButton(PlayButton())

    def _replacePlayPauseButton(self, new_button):
        new_button.setFixedSize(self.standardised(50), self.standardised(50))
        new_button.clicked.connect(self.playPause)

        controlsLayout = self.container.layout().itemAt(0)
        for i in range(controlsLayout.count()):
            widget = controlsLayout.itemAt(i).widget()
            if widget == self.btnPlayPause:
                controlsLayout.removeWidget(widget)
                widget.deleteLater()
                controlsLayout.insertWidget(i, new_button)
                break

        self.btnPlayPause = new_button

    def changeVolume(self, value):
        self.audioManager.setVolume(value)

    def updatePosition(self, seconds):
        if not self.isSeeking:
            self.positionSlider.setValue(seconds)
            self.labelElapsed.setText(self.sToHMS(seconds))
            duration = self.positionSlider.maximum()
            remaining = max(duration - seconds, 0)
            self.labelRemaining.setText(f"-{self.sToHMS(remaining)}")

    def updateDuration(self, seconds):
        self.positionSlider.setRange(0, seconds)
        remaining = max(seconds - self.positionSlider.value(), 0)
        self.labelRemaining.setText(f"-{self.sToHMS(remaining)}")

    def setPosition(self, seconds):
        self.audioManager.seek(seconds)

    def startSeek(self):
        self.isSeeking = True

    def endSeek(self):
        self.isSeeking = False
        self.audioManager.seek(self.positionSlider.value())

    def sToHMS(self, s):
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

    def standardised(self, value):
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        SCREEN_HEIGHT = geometry.height()
        return math.ceil(value * SCREEN_HEIGHT / 1600)
