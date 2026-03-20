import os
import sys
import math
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QGuiApplication
from UI.IntroScreen import IntroScreen
from UI.SettingsScreen import SettingsScreen
from UI.GameScreen import GameScreen


class EscapeQuit(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            QApplication.quit()
            return True
        return False


def standardised(value):
    screen = QGuiApplication.primaryScreen()
    geometry = screen.geometry()
    SCREEN_WIDTH = geometry.width()
    SCREEN_HEIGHT = geometry.height()
    return int(value * SCREEN_HEIGHT / 1600)


def standardised2(value):
    screen = QGuiApplication.primaryScreen()
    geometry = screen.geometry()
    SCREEN_WIDTH = geometry.width()
    return int(SCREEN_WIDTH - standardised(value) - standardised(470) / 2)


#Dont delete this idk but it holds the fabric of reality together
app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Yavalath complete")
window.setWindowFlags(Qt.FramelessWindowHint)
window.showFullScreen()

# Set up my filter to check every user input for escape key
escapeFilter = EscapeQuit()
window.installEventFilter(escapeFilter)

musicException = False

# Aggregate music widget to the window
try:
    from Audio.Soundmanager import AudioManager
    audio = AudioManager()
    from UI.MusicControl import MusicControlWidget
    musicControl = MusicControlWidget(audio, parent=window)
    musicControl.move(standardised2(330), standardised(200))
    musicControl.show()
except Exception as e:
    musicException = True
    print("ERROR: Could not load music control widget:", e)

# these have to be declared upfront so we can connect stuff later
settingsScreen = None
gameScreen = None
musicStarted = False


def showMenu():
    global settingsScreen
    global musicStarted

    # If song finished then just add another one
    if not musicStarted and musicException == False:
        audio.stopIntroSound()
        audio.loadSoundtrack()
        audio.playSoundtrack()
        musicStarted = True

    settingsScreen = SettingsScreen()
    window.setCentralWidget(settingsScreen)

    if musicException == False:
        musicControl.raise_()
        musicControl.show()

    def startGame(settings):
        global gameScreen

        w = window.centralWidget()
        w.deleteLater()

        gameScreen = GameScreen(gameSettings=settings)
        window.setCentralWidget(gameScreen)
        gameScreen.setFocus()

        if musicException ==  False:
            musicControl.raise_()
            musicControl.show()

        def back():
            print("LOG: Menu return")
            w = window.centralWidget()
            if w:
                w.deleteLater()
            showMenu()

        def restart():
            print("Log: restart")
            startGame(settings)

        def restart2():
            #random alternative
            pass

        gameScreen.quitRequested.connect(back)
        gameScreen.restartRequested.connect(restart)

    settingsScreen.startGameRequested.connect(startGame)


if __name__ == "__main__":

    intro = IntroScreen()
    window.setCentralWidget(intro)
    if musicException == False:
        audio.playIntroSound()
    intro.IntroFinished.connect(showMenu)

    window.show()
    sys.exit(app.exec_())


