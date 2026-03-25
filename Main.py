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
    # Defined as an object so that PyQT can install it as an event filter
    # global event filter that checks if the escape key is pressed and if so quits the application
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            QApplication.quit()
            return True
        return False


def standardised(value):
    # Simple resolution handler that scales a value based on the screen height, assuming a base resolution of 1600x900
    screen = QGuiApplication.primaryScreen()
    geometry = screen.geometry()
    SCREEN_WIDTH = geometry.width()
    SCREEN_HEIGHT = geometry.height()
    return int(value * SCREEN_HEIGHT / 1600)


def standardised2(value):
    # An alternative standardised function that scales based on screen width rather than screen height
    screen = QGuiApplication.primaryScreen()
    geometry = screen.geometry()
    SCREEN_WIDTH = geometry.width()
    return int(SCREEN_WIDTH - standardised(value) - standardised(470) / 2)


#App starter
app = QApplication(sys.argv)

#Window setup
window = QMainWindow()
window.setWindowTitle("Yavalath complete")
window.setWindowFlags(Qt.FramelessWindowHint)
window.showFullScreen()

# Set up my filter to check every user input for escape key
escapeFilter = EscapeQuit()
window.installEventFilter(escapeFilter)

musicException = False

# Aggregate music widget to the window
# Try to setup the VPC music control, if it fails just skip it and print an error message for debug
# The game will still be fully playable just without music control
try:
    from Audio.Soundmanager import AudioManager
    audio = AudioManager()
    from UI.MusicControl import MusicControlWidget
    musicControl = MusicControlWidget(audio, parent=window)
    musicControl.move(standardised2(330), standardised(200))
    musicControl.show()
except Exception as e:
    musicException = True
    print("LOG: ERROR: Could not load music control widget:", e)


# Premature declaration of variables that will then be used to store window objects
settingsScreen = None
gameScreen = None
musicStarted = False


def showMenu():
    global settingsScreen
    global musicStarted

    # If song finished then just add another one only if music player was loaded in successfully.
    if not musicStarted and musicException == False:
        audio.stopIntroSound()
        audio.loadSoundtrack()
        audio.playSoundtrack()
        musicStarted = True

    #Defines a new settingscreen object and sets it as central widget
    settingsScreen = SettingsScreen()
    window.setCentralWidget(settingsScreen)

    # Stack musicControl to the top and show
    if musicException == False:
        musicControl.raise_()
        musicControl.show()

    def startGame(settings):
        global gameScreen

        #Sets up widget deletion to prevent recursion depth issues
        w = window.centralWidget()
        w.deleteLater()


        gameScreen = GameScreen(settings)
        window.setCentralWidget(gameScreen)
        gameScreen.setFocus()

        if musicException ==  False:
            musicControl.raise_()
            musicControl.show()

        def back():
            # Goes back to the showmenu function while removing the current widget to prevent recursion depth issues.
            print("LOG: Menu return")
            w = window.centralWidget()
            if w:
                w.deleteLater()
            showMenu()

        # restarts game
        def restart():
            print("LOG :restart")
            startGame(settings)

        #Signal connection to the widgets so that the back and restart buttons work
        gameScreen.quitRequested.connect(back)
        gameScreen.restartRequested.connect(restart)

    settingsScreen.startGameRequested.connect(startGame)

#Main execution 
if __name__ == "__main__":

    #Create intro widget
    intro = IntroScreen()
    #Centralise intro widget and show
    window.setCentralWidget(intro)
    #Play intro music if music player loaded successfully
    if musicException == False:
        audio.playIntroSound()
    #Connect a signal from the introscreen to the showMenu function so that when the intro finishes it will start
    intro.IntroFinished.connect(showMenu)

    window.show()
    sys.exit(app.exec_())


