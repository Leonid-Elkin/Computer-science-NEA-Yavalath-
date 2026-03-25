# GameScreen.py

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,QSpacerItem
)
from PyQt5.QtGui import QFont, QColor, QGuiApplication
import math

from Yavalath.YavalathBoard import Board as YavalathBoard
from UI.Buttons import TextButton
from UI.Timer import PlayerTimer
from Pentalath.PentalathBoard import Board as PentalathBoard
from PyQt5.QtWidgets import QApplication
from Susan.SusanBoard import Board as SusanBoard

from UI.StarLogoWidget import StarLogoWidget
from UI.MessageLog import MessageLog

class GameScreen(QWidget):
    quitRequested = pyqtSignal()
    restartRequested = pyqtSignal()
    gameResult = pyqtSignal(str)
    
    # GameScreen.py
    DIFFICULTY_SETTINGS = {
        "Easy":    {"depth": 2, "beam_width": 6},
        "Medium":  {"depth": 3, "beam_width": 8},
        "Hard":    {"depth": 4, "beam_width": 12},
        "Extreme": {"depth": 5, "beam_width": 14},
    }

    def __init__(self, gameSettings=None, parent=None):
        super().__init__(parent)
        
        # Get screen dimensions FIRST
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.SCREEN_WIDTH = geometry.width()
        self.SCREEN_HEIGHT = geometry.height()
        
        #Global stules
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #ffffff;
                font-family: Times New Roman;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }
            TextButton {
                color: #ffffff;
                background: transparent;
                border: none;
            }
        """)

        #Board constant setup
        self.selectedSide = 5
        self.selectedRadius = self.standardised(60)
        self.selectedColors = {
            "player1": QColor("white"),
            "player2": QColor("#FF4080"),
            "empty": QColor("#1E283C"),
            "border": QColor("#00C8FF"),
        }
        #Placeholder vars
        self.selectedAiMoveDelay = 500
        self.numComputers = 0
        self.mode = "Yavalath"
        self.difficulty = "Easy"

        #Load bot from settingsScreen
        self.selectedSide = gameSettings.get("side", self.selectedSide)
        self.selectedRadius = gameSettings.get("radius", self.selectedRadius)
        self.selectedColors = gameSettings.get("colors", self.selectedColors)
        self.selectedAiMoveDelay = gameSettings.get("ai_move_delay", self.selectedAiMoveDelay)
        computersSetting = gameSettings.get("computers", "0 Computers")
        self.computersSetting = gameSettings.get("computers", "0 Computers")
        self.numComputers = {"0 Computers":0, "1 Computer":1, "2 Computers":2}.get(computersSetting, 0)
        self.mode = gameSettings.get("mode", self.mode)
        self.difficulty = gameSettings.get("difficulty", self.difficulty)

        #Minimax config
        self.minimaxConfig = self.DIFFICULTY_SETTINGS.get(self.difficulty, self.DIFFICULTY_SETTINGS["Easy"])
        if self.selectedAiMoveDelay is None:
            self.selectedAiMoveDelay = 100

        self.moveTimerDuration = self.selectedAiMoveDelay // 1000
        self.player1Score = 0
        self.player2Score = 0

        #Background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)

        #True background not the one used in SettingScreen
        self.backgroundFrame = QFrame(self)
        self.backgroundFrame.setStyleSheet("background-color: black;")
        self.backgroundFrame.setGeometry(self.rect())
        self.backgroundFrame.lower()

        #small function to resize background with the screen.
        def resizeEventWithBg(event):
            self.backgroundFrame.setGeometry(self.rect())
            #doesn't break resizing for some reason (Only thing i could to to help)
            super(GameScreen, self).resizeEvent(event)

        self.resizeEvent = resizeEventWithBg

        #Main vertical layout
        mainVerticalLayout = QVBoxLayout(self)
        mainVerticalLayout.setContentsMargins(
            self.standardised(30), self.standardised(30),
            self.standardised(30), self.standardised(30)
        )
        mainVerticalLayout.setSpacing(self.standardised(15))

        #Title
        self.titleContainer = QFrame(self)
        borderRadius = self.standardised(20)
        border = 2
        self.titleContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: {border}px solid #444444;"
        )
        self.titleContainer.setFixedHeight(self.standardised(100))

        titleLayout = QVBoxLayout(self.titleContainer)
        titleLayout.setContentsMargins(0,0,0,0)

        #Adaptive gamemode label
        if self.mode == "Yavalath":
            self.titleLabel = QLabel("Yavalath", self.titleContainer)
        elif self.mode == "Pentalath":
            self.titleLabel = QLabel("Pentalath", self.titleContainer)
        elif self.mode == "Susan":
            self.titleLabel = QLabel("Susan", self.titleContainer)

        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont("Arial", self.standardised(40), QFont.Bold))
        self.titleLabel.setStyleSheet("background: transparent; color: white; border: none;")
        titleLayout.addWidget(self.titleLabel)

        mainVerticalLayout.addWidget(self.titleContainer)

        #Main HBox layout
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(
            self.standardised(30), self.standardised(30),
            self.standardised(30), self.standardised(30)
        )
        mainLayout.setSpacing(self.standardised(40))

        #setup timer
        self.freezeTimer = QTimer(self)
        self.freezeTimer.setInterval(500)
        self.freezeTimer.timeout.connect(self._freezeTimerTick)

        #Left container
        self.leftContainer = QFrame()
        self.leftContainer.setObjectName("LeftContainer")
        self.leftContainer.setFixedWidth(self.standardised(440))
        self.leftContainer.setStyleSheet(f"""
            background-color: #1E1E1E;
            border-radius: {self.standardised(20)}px;
            border: 2px solid #444444;
        """)
        mainLayout.addWidget(self.leftContainer)

        self.leftLayout = QVBoxLayout(self.leftContainer)
        self.leftLayout.setContentsMargins(
            self.standardised(30), self.standardised(30),
            self.standardised(30), self.standardised(30)
        )
        self.leftLayout.setSpacing(self.standardised(25))

        #Star logo
        self.starLogoWidgetSize = self.standardised(350)
        self.starLogo = StarLogoWidget(self.leftContainer)
        self.starLogo.setFixedSize(self.starLogoWidgetSize, self.starLogoWidgetSize)
        self.leftLayout.addWidget(self.starLogo, alignment=Qt.AlignCenter)

        #Only difference between the two timers is that they are assigned to different variables
        #Timer creation
        self.player1Timer = PlayerTimer(
            duration=self.moveTimerDuration,
            borderColor=QColor("#222222"),
            fillColor=QColor("#111822"),
            textColor=self.selectedColors["player1"]
        )
        self.player1Timer.setStyleSheet(f"border: none")
        self.leftLayout.addWidget(self.player1Timer, alignment=Qt.AlignCenter)
        
        #Timer 2 creation
        self.player2Timer = PlayerTimer(
            duration=self.moveTimerDuration,
            borderColor=QColor("#222222"),
            fillColor=QColor("#111822"),
            textColor=self.selectedColors["player2"]
        )
        self.player2Timer.setStyleSheet("border: none")
        self.leftLayout.addWidget(self.player2Timer, alignment=Qt.AlignCenter)

        #Player 1 label
        self.player1Label = QLabel()
        self.player1Label.setAlignment(Qt.AlignCenter)
        self.player1Label.setFont(QFont("Arial", self.standardised(16), QFont.Bold))
        self.player1Label.setStyleSheet("border: none;")
        self.leftLayout.addWidget(self.player1Label)

        #Player 2 label
        self.player2Label = QLabel()
        self.player2Label.setAlignment(Qt.AlignCenter)
        self.player2Label.setFont(QFont("Arial", self.standardised(16), QFont.Bold))
        self.player2Label.setStyleSheet("border: none;")
        self.leftLayout.addWidget(self.player2Label)

        self.leftLayout.addSpacing(self.standardised(30))

        #Message container box setup and creation
        self.messageLogContainer = QFrame(self.leftContainer)
        self.messageLogContainer.setStyleSheet(f"""
            background-color: #1E1E1E;
            border: 1px solid #00FFFF;
            border-radius: {self.standardised(15)}px;
        """)
        self.messageLogContainer.setFixedHeight(self.standardised(300))
        self.leftLayout.addWidget(self.messageLogContainer)

        #Layout inside container
        logLayout = QVBoxLayout(self.messageLogContainer)
        logLayout.setContentsMargins(self.standardised(10), self.standardised(10),
                                    self.standardised(10), self.standardised(10))
        logLayout.setSpacing(self.standardised(5))

        # The actual message log widget
        self.messageLog = MessageLog(self.messageLogContainer)
        self.messageLog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        logLayout.addWidget(self.messageLog)

        # Buttons
        buttonsContainer = QVBoxLayout()
        buttonsContainer.setSpacing(self.standardised(40))
        buttonsContainer.setContentsMargins(0,0,0,0)

        #PLAY AGAIN
        self.playAgainButton = TextButton("Play Again", checkable=False)
        self.playAgainButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.playAgainButton.clicked.connect(self.onPlayAgainClicked)
        self.playAgainButton.setClickable(False)
        self.playAgainButton.setOpacity(0.5)
        self.playAgainButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.playAgainButton, alignment=Qt.AlignCenter)

        #QUIT TO MENU
        self.quitButton = TextButton("Return to Menu", checkable=False)
        self.quitButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.quitButton.clicked.connect(self.onQuitClicked)
        self.quitButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.quitButton, alignment=Qt.AlignCenter)

        #QUIT PROGRAM
        self.quitAppButton = TextButton("Quit", checkable=False)
        self.quitAppButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.quitAppButton.clicked.connect(self.onQuitAppClicked)
        self.quitButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.quitAppButton, alignment=Qt.AlignCenter)

        self.leftLayout.addLayout(buttonsContainer)
        self.leftLayout.addStretch(1)

        #Right container
        self.rightContainer = QFrame()
        self.rightContainer.setStyleSheet(f"""
            background-color: #1E1E1E;
            border-radius: {self.standardised(20)}px;
            border: 2px solid #444444;
        """)
        mainLayout.addWidget(self.rightContainer)

        rightLayout = QVBoxLayout(self.rightContainer)
        rightLayout.setContentsMargins(
            self.standardised(40), self.standardised(40),
            self.standardised(40), self.standardised(40)
        )
        rightLayout.setSpacing(self.standardised(20))
        rightLayout.setAlignment(Qt.AlignCenter)

        print(f"DEBUG: MODE IS {self.mode}!")
        print(f"DEBUG: numcomputers: {self.numComputers}")

        
        #Board
        if self.mode == "Yavalath":
            self.boardObject = YavalathBoard
        elif self.mode == "Pentalath":
            self.boardObject = PentalathBoard
        elif self.mode == "Susan":
            self.boardObject = SusanBoard
            print("board init for susan")
        else:
            print("Unknown game state")

        # determine game mode that is sent from settings screen
        #Actually redundant but works
        mode_val = "human" if gameSettings.get("game_type", "human") == "human" else "ai"
        side, radius, colors, ai_move_delay, human_player, wait_for_message = (
            self.selectedSide, self.selectedRadius, self.selectedColors, 0, 1, True
        )

        #Result Label
        self.resultLabel = QLabel("")
        self.resultLabel.setAlignment(Qt.AlignCenter)
        self.resultLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        self.resultLabel.setStyleSheet("color: red; background: transparent; border: none;")

        # BOARD CREATION
        #Board parameter generation
        print(f"DEBUG: human player: {human_player}")
        boardParams = dict(
            side=side, radius=radius, colors=colors,
            ai_move_delay=ai_move_delay, mode=mode_val,
            human_player=human_player, wait_for_message=wait_for_message,
            message_handler=self.messageLog
        )
        #Add extra parameters if mode is ai
        if mode_val == "ai":
            boardParams["depth"] = self.minimaxConfig["depth"]
            boardParams["beamwidth"] = self.minimaxConfig["beam_width"]

        self.boardWidget = self.boardObject(**boardParams)
        self.boardWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use EXACT same calculation as SettingsScreen to keep board at the same position
        boardWidth = int(self.selectedRadius * 2 * (self.selectedSide + 0.5)) * 2
        boardHeight = int(math.sqrt(3) * self.selectedRadius * (self.selectedSide + 1)) * 2
        self.boardWidget.setMinimumSize(boardWidth, boardHeight)
        self.boardWidget.setMaximumSize(boardWidth, boardHeight)  # ADD THIS

        # Board alignment and result label
        #All labels placed inside boardLayout
        boardLayout = QVBoxLayout()
        boardLayout.setSpacing(self.standardised(20))
        boardLayout.setAlignment(Qt.AlignCenter)  # Changed from AlignTop
        boardLayout.addWidget(self.resultLabel)
        boardLayout.addWidget(self.boardWidget, alignment=Qt.AlignCenter)
        rightLayout.addLayout(boardLayout)

        mainVerticalLayout.addLayout(mainLayout)

        #Initialize game state
        self.currentPlayer = 1
        self.timerEnabled = self.selectedAiMoveDelay != 500
        self.updateScoreLabels()
        #Connect timer expiration signals to handler functions
        self.player1Timer.timeExpired.connect(lambda: self.handleTimeExpired(1)) 
        self.player2Timer.timeExpired.connect(lambda: self.handleTimeExpired(2))

        #Start player timer if timer is enabled. In the current version of the game they will always be.
        if self.timerEnabled:
            self.player1Timer.start()

        #BOARD SIGNAL CONNECTIONS - each action that the board can do is connected to a corresponding handler function
        if hasattr(self.boardWidget, 'moveMade'):
            self.boardWidget.moveMade.connect(self.onMoveMade)
            self.boardWidget.moveMade.connect(self.clearIllegalMoveMessage)

        if hasattr(self.boardWidget, 'gameOver'):
            self.boardWidget.gameOver.connect(self.onGameOver)
        if hasattr(self.boardWidget, 'player1Win'):
            self.boardWidget.player1Win.connect(lambda: self.handleWinner(1))
        if hasattr(self.boardWidget, 'player2Win'):
            self.boardWidget.player2Win.connect(lambda: self.handleWinner(2))
        if hasattr(self.boardWidget, 'drawGame'):
            self.boardWidget.drawGame.connect(lambda: self.handleWinner(0))
        if hasattr(self.boardWidget, 'illegalMove'):
            self.boardWidget.illegalMove.connect(self.showIllegalMoveMessage)

    def standardised(self, value):
        #Standardises the size of the widget based on the screen height, so it scales properly on different resolutions
        return int(value * self.SCREEN_HEIGHT / 1600)

    def updateScoreLabels(self):
        """
        updates the score labels for both players based on the current gamestate
        """
        def formatScore(score):
            #Just in case there is a draw limit score to 3 sig figs
            if score % 1 == 0:
                return str(int(score))
            else:
                return str(f"{score:.3}")

        #Function to display an appropriate message for draws/wins
        self.player1Label.setText(f"Player 1 (White): {formatScore(self.player1Score)} wins")
        if self.computersSetting == "0 Computers":
            self.player2Label.setText(f"Player 2 (Magenta): {formatScore(self.player2Score)} wins")
        else:
            self.player2Label.setText(f"Computer Player (Magenta): {formatScore(self.player2Score)} wins")

    def onQuitClicked(self):
        #Quit button handler method, emits a signal thatis caught by Main.py to return to the menu screen
        self.quitRequested.emit()

    def handleTimeExpired(self, player):
        #Handles the event of a player's timer running out
        if player == 1:
            opponent = 2
        else:
            opponent = 1

        #Debug log and set result label
        reason = f"DEBUG: Player {opponent} won because Player {player} ran out of time."
        print(reason)
        self.resultLabel.setText(reason)

        if opponent == 1:
            self.player1Score += 1
        else:
            self.player2Score += 1

        #Updates score labels
        self.updateScoreLabels()
        self.player1Timer.stop()
        self.player2Timer.stop()
        self.boardWidget.setEnabled(False)

        self.playAgainButton.setClickable(True)
        self.playAgainButton.setOpacity(1.0)

        #Fake a game over signal from the board so that the same endgame logic is used as if a player won normally. I am so sorry for this.
        if hasattr(self.boardWidget, 'gameOver'):
            self.boardWidget.gameOver.emit()
            self.onGameOver()

    def onMoveMade(self):
        #Method runs every time a move is made

        #This never gets used
        if not self.timerEnabled:
            return

        resetToSeconds = self.moveTimerDuration

        #Resets and starts the relevant player's timer and stops the other player's timer
        if self.currentPlayer == 1:
            self.player1Timer.stop()
            self.player1Timer.reset(duration=resetToSeconds)
            self.player2Timer.reset(duration=resetToSeconds)
            self.player2Timer.start()
            self.currentPlayer = 2
        else:
            self.player2Timer.stop()
            self.player2Timer.reset(duration=resetToSeconds)
            self.player1Timer.reset(duration=resetToSeconds)
            self.player1Timer.start()
            self.currentPlayer = 1

    def onPlayAgainClicked(self):
        #Play again button handler method, resets the game state to allow the players to play another game without returning to the menu
        self.playAgainButton.setClickable(False)
        self.playAgainButton.setOpacity(0.5)
        self.freezeTimer.stop()
        self.restartGame()

    def onQuitAppClicked(self):
        #Quit app button handler method, quits the entire application
        QApplication.quit()

    def restartGame(self):
        #Resets the game state to allow the players to play another game without returning to the menu
        #Score persists between games
        self.boardWidget.continue_game()
        self.resultLabel.setText("")
        self.player1Timer.reset(duration=self.moveTimerDuration)
        self.player2Timer.reset(duration=self.moveTimerDuration)
        self.player1Timer.start()
        self.player2Timer.stop()
        self.currentPlayer = 1
        self.boardWidget.setEnabled(True)

    def _freezeTimerTick(self):
        #Method called every time a frozen timer ticks, so instead of not moving it just resets the timers every time to create a frozen effect.
        self.player1Timer.reset(duration=self.moveTimerDuration)
        self.player2Timer.reset(duration=self.moveTimerDuration)

    def onGameOver(self):
        #Game over state handler
        self.playAgainButton.setClickable(True)
        self.playAgainButton.setOpacity(1.0)
        self.boardWidget.setEnabled(False)
        self.player1Timer.stop()
        self.player2Timer.stop()
        self.freezeTimer.start()

    def handleWinner(self, winner):
        #Gives appropriate amount of points to each player after a game ends - win - 1 loss - 1 draw 0.5 each
        if winner == 1:
            self.player1Score += 1
        elif winner == 2:
            self.player2Score += 1
        elif winner == 0:
            self.player1Score += 0.5    
            self.player2Score += 0.5

        #Function to display an appropriate message for draws/wins
        if winner == 1:
            self.resultLabel.setStyleSheet("color: white; background: transparent; border: none;")
            message = "Player 1 won by making winning moves."
        elif winner == 2:
            self.resultLabel.setStyleSheet("color: #FF4080; background: transparent; border: none;")
            message = "Player 2 won by making winning moves."
        elif winner == 0:
            self.resultLabel.setStyleSheet("color: green; background: transparent; border: none;")
            message = "Game ended in a draw."
        self.resultLabel.setText(message)

        self.updateScoreLabels()
        self.player1Timer.stop()
        self.boardWidget.setEnabled(False)
        self.playAgainButton.setClickable(True)
        self.playAgainButton.setOpacity(1.0)

    def showIllegalMoveMessage(self):
        #Handler method to show illegal move message into log
        self.messageLog.send_message("Illegal move! Please try again.")

    def clearIllegalMoveMessage(self):
        #Handler message to clear illegal move message 
        self.messageLog.send_message("")