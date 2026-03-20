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
        
        # --- Global Styles ---
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

        # --- Default game settings ---
        self.selectedSide = 5
        self.selectedRadius = self.standardised(60)
        self.selectedColors = {
            "player1": QColor("white"),
            "player2": QColor("#FF4080"),
            "empty": QColor("#1E283C"),
            "border": QColor("#00C8FF"),
        }
        self.selectedAiMoveDelay = 500
        self.numComputers = 0
        self.mode = "Yavalath"
        self.difficulty = "Easy"

        # --- Load from gameSettings ---
        self.selectedSide = gameSettings.get("side", self.selectedSide)
        self.selectedRadius = gameSettings.get("radius", self.selectedRadius)
        self.selectedColors = gameSettings.get("colors", self.selectedColors)
        self.selectedAiMoveDelay = gameSettings.get("ai_move_delay", self.selectedAiMoveDelay)
        computersSetting = gameSettings.get("computers", "0 Computers")
        self.computersSetting = gameSettings.get("computers", "0 Computers")
        self.numComputers = {"0 Computers":0, "1 Computer":1, "2 Computers":2}.get(computersSetting, 0)
        self.mode = gameSettings.get("mode", self.mode)
        self.difficulty = gameSettings.get("difficulty", self.difficulty)

        # --- Minimax config ---
        self.minimaxConfig = self.DIFFICULTY_SETTINGS.get(self.difficulty, self.DIFFICULTY_SETTINGS["Easy"])
        if self.selectedAiMoveDelay is None:
            self.selectedAiMoveDelay = 100

        self.moveTimerDuration = self.selectedAiMoveDelay // 1000
        self.player1Score = 0
        self.player2Score = 0

        # --- Background ---
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(palette)

        self.backgroundFrame = QFrame(self)
        self.backgroundFrame.setStyleSheet("background-color: black;")
        self.backgroundFrame.setGeometry(self.rect())
        self.backgroundFrame.lower()

        def resizeEventWithBg(event):
            self.backgroundFrame.setGeometry(self.rect())
            super(GameScreen, self).resizeEvent(event)
        self.resizeEvent = resizeEventWithBg

        # --- Main Vertical Layout ---
        mainVerticalLayout = QVBoxLayout(self)
        mainVerticalLayout.setContentsMargins(
            self.standardised(30), self.standardised(30),
            self.standardised(30), self.standardised(30)
        )
        mainVerticalLayout.setSpacing(self.standardised(15))

        # --- Title ---
        self.titleContainer = QFrame(self)
        borderRadius = self.standardised(20)
        border = 2
        self.titleContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: {border}px solid #444444;"
        )
        self.titleContainer.setFixedHeight(self.standardised(100))

        titleLayout = QVBoxLayout(self.titleContainer)
        titleLayout.setContentsMargins(0,0,0,0)

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

        # --- Main HBox Layout ---
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(
            self.standardised(30), self.standardised(30),
            self.standardised(30), self.standardised(30)
        )
        mainLayout.setSpacing(self.standardised(40))

        self.freezeTimer = QTimer(self)
        self.freezeTimer.setInterval(500)
        self.freezeTimer.timeout.connect(self._freezeTimerTick)

        # --- Left Container ---
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

        # Star Logo
        self.starLogoWidgetSize = self.standardised(350)
        self.starLogo = StarLogoWidget(self.leftContainer)
        self.starLogo.setFixedSize(self.starLogoWidgetSize, self.starLogoWidgetSize)
        self.leftLayout.addWidget(self.starLogo, alignment=Qt.AlignCenter)

        self.player1Timer = PlayerTimer(
            duration=self.moveTimerDuration,
            borderColor=QColor("#222222"),
            fillColor=QColor("#111822"),
            textColor=self.selectedColors["player1"]
        )
        self.player1Timer.setStyleSheet(f"border: none")
        self.leftLayout.addWidget(self.player1Timer, alignment=Qt.AlignCenter)

        self.player2Timer = PlayerTimer(
            duration=self.moveTimerDuration,
            borderColor=QColor("#222222"),
            fillColor=QColor("#111822"),
            textColor=self.selectedColors["player2"]
        )
        self.player2Timer.setStyleSheet("border: none")
        self.leftLayout.addWidget(self.player2Timer, alignment=Qt.AlignCenter)

        self.player1Label = QLabel()
        self.player1Label.setAlignment(Qt.AlignCenter)
        self.player1Label.setFont(QFont("Arial", self.standardised(16), QFont.Bold))
        self.player1Label.setStyleSheet("border: none;")
        self.leftLayout.addWidget(self.player1Label)

        self.player2Label = QLabel()
        self.player2Label.setAlignment(Qt.AlignCenter)
        self.player2Label.setFont(QFont("Arial", self.standardised(16), QFont.Bold))
        self.player2Label.setStyleSheet("border: none;")
        self.leftLayout.addWidget(self.player2Label)

        self.leftLayout.addSpacing(self.standardised(30))

        # --- Message Log Container Box ---
        self.messageLogContainer = QFrame(self.leftContainer)
        self.messageLogContainer.setStyleSheet(f"""
            background-color: #1E1E1E;
            border: 1px solid #00FFFF;
            border-radius: {self.standardised(15)}px;
        """)
        self.messageLogContainer.setFixedHeight(self.standardised(300))
        self.leftLayout.addWidget(self.messageLogContainer)

        # Layout inside the container
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

        self.playAgainButton = TextButton("Play Again", checkable=False)
        self.playAgainButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.playAgainButton.clicked.connect(self.onPlayAgainClicked)
        self.playAgainButton.setClickable(False)
        self.playAgainButton.setOpacity(0.5)
        self.playAgainButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.playAgainButton, alignment=Qt.AlignCenter)

        self.quitButton = TextButton("Return to Menu", checkable=False)
        self.quitButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.quitButton.clicked.connect(self.onQuitClicked)
        self.quitButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.quitButton, alignment=Qt.AlignCenter)

        self.quitAppButton = TextButton("Quit", checkable=False)
        self.quitAppButton.setFixedSize(self.standardised(160), self.standardised(44))
        self.quitAppButton.clicked.connect(self.onQuitAppClicked)
        self.quitButton.setStyleSheet("color: white; background: transparent; border: none;")
        buttonsContainer.addWidget(self.quitAppButton, alignment=Qt.AlignCenter)

        self.leftLayout.addLayout(buttonsContainer)
        self.leftLayout.addStretch(1)

        # --- Right Container ---
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

        print(f"MODE IS {self.mode}!!!!!!!!!!")

        # --- Board ---
        if self.mode == "Yavalath":
            self.boardObject = YavalathBoard
        elif self.mode == "Pentalath":
            self.boardObject = PentalathBoard
        elif self.mode == "Susan":
            self.boardObject = SusanBoard
            print("board init for susan")
        else:
            print("Unknown game state")

# Find this section in GameScreen.py around line 120-140
# Replace the board initialization code with this:

        # Determine game mode based on number of computers
        if self.numComputers == 0:
            mode_val = "human"
            human_player = 1  # Doesn't matter for human vs human
        elif self.numComputers == 1:
            mode_val = "human_vs_ai"
            human_player = 1  # Human is player 1, AI is player 2
        else:  # numComputers == 2
            mode_val = "ai_vs_ai"
            human_player = None  # No human player

        side, radius, colors, ai_move_delay = (
            self.selectedSide, self.selectedRadius, self.selectedColors, 0
        )
        wait_for_message = True

        self.resultLabel = QLabel("")
        self.resultLabel.setAlignment(Qt.AlignCenter)
        self.resultLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        self.resultLabel.setStyleSheet("color: red; background: transparent; border: none;")

        # Board initialization with correct mode
        boardParams = dict(
            side=side, 
            radius=radius, 
            colors=colors,
            ai_move_delay=self.selectedAiMoveDelay,  # Use actual delay, not 0
            mode=mode_val,
            human_player=human_player, 
            wait_for_message=wait_for_message,
            message_handler=self.messageLog
        )
        
        # Add depth and beam_width for AI modes
        if mode_val in ["ai_vs_ai", "human_vs_ai"]:
            boardParams["depth"] = self.minimaxConfig["depth"]
            boardParams["beamwidth"] = self.minimaxConfig["beam_width"]

        self.boardWidget = self.boardObject(**boardParams)
        self.boardWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Use EXACT same calculation as SettingsScreen
        boardWidth = int(self.selectedRadius * 2 * (self.selectedSide + 0.5)) * 2
        boardHeight = int(math.sqrt(3) * self.selectedRadius * (self.selectedSide + 1)) * 2
        self.boardWidget.setMinimumSize(boardWidth, boardHeight)
        self.boardWidget.setMaximumSize(boardWidth, boardHeight)  # ADD THIS

        # --- Layout for board and result ---
        boardLayout = QVBoxLayout()
        boardLayout.setSpacing(self.standardised(20))
        boardLayout.setAlignment(Qt.AlignCenter)  # Changed from AlignTop
        boardLayout.addWidget(self.resultLabel)
        boardLayout.addWidget(self.boardWidget, alignment=Qt.AlignCenter)
        rightLayout.addLayout(boardLayout)

        mainVerticalLayout.addLayout(mainLayout)

        # --- Initialize state ---
        self.currentPlayer = 1
        self.timerEnabled = self.selectedAiMoveDelay != 500
        self.updateScoreLabels()
        self.player1Timer.timeExpired.connect(lambda: self.handleTimeExpired(1))
        self.player2Timer.timeExpired.connect(lambda: self.handleTimeExpired(2))

        if self.timerEnabled:
            self.player1Timer.start()

        # --- Connect board signals ---
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
        #autism
        return int(value * self.SCREEN_HEIGHT / 1600)

    def updateScoreLabels(self):
        def formatScore(score):

            if score % 1 == 0:
                return str(int(score))
            else:
                return str(f"{score:.3}")
            
        print(self.computersSetting == "human")

        self.player1Label.setText(f"Player 1 (White): {formatScore(self.player1Score)} wins")
        if self.computersSetting == "0 Computers":
            self.player2Label.setText(f"Player 2 (Magenta): {formatScore(self.player2Score)} wins")
        else:
            self.player2Label.setText(f"Computer Player (Magenta): {formatScore(self.player2Score)} wins")

    def onQuitClicked(self):
        self.quitRequested.emit()

    def handleTimeExpired(self, player):
        if player == 1:
            opponent = 2
        else:
            opponent = 1

        reason = f"Player {opponent} won because Player {player} ran out of time."
        print(reason)
        self.resultLabel.setText(reason)

        if opponent == 1:
            self.player1Score += 1
        else:
            self.player2Score += 1

        self.updateScoreLabels()
        self.player1Timer.stop()
        self.player2Timer.stop()
        self.boardWidget.setEnabled(False)

        self.playAgainButton.setClickable(True)
        self.playAgainButton.setOpacity(1.0)

        if hasattr(self.boardWidget, 'gameOver'):
            self.boardWidget.gameOver.emit()
            self.onGameOver()

    def onMoveMade(self):
        if not self.timerEnabled:
            return

        resetToSeconds = self.moveTimerDuration

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
        self.playAgainButton.setClickable(False)
        self.playAgainButton.setOpacity(0.5)
        self.freezeTimer.stop()
        self.restartGame()

    def onQuitAppClicked(self):
        QApplication.quit()

    def restartGame(self):
        self.boardWidget.continue_game()
        self.resultLabel.setText("")
        self.player1Timer.reset(duration=self.moveTimerDuration)
        self.player2Timer.reset(duration=self.moveTimerDuration)
        self.player1Timer.start()
        self.player2Timer.stop()
        self.currentPlayer = 1
        self.boardWidget.setEnabled(True)

    def _freezeTimerTick(self):
        #Idiot solution instead of putting even a sliver of effort into manual updating
        self.player1Timer.reset(duration=self.moveTimerDuration)
        self.player2Timer.reset(duration=self.moveTimerDuration)

    def onGameOver(self):
        self.playAgainButton.setClickable(True)
        self.playAgainButton.setOpacity(1.0)
        self.boardWidget.setEnabled(False)
        self.player1Timer.stop()
        self.player2Timer.stop()
        self.freezeTimer.start()

    def handleWinner(self, winner):
        #Useless bad solution to fake problem I am useless and working with this code is my punishment from god
        if winner == 1:
            self.player1Score += 1
        elif winner == 2:
            self.player2Score += 1
        elif winner == 0:
            self.player1Score += 0.5    
            self.player2Score += 0.5
#if if if elif elif if else if else elif else if else if else elif if if elif else elif elif if elif else (26-28th of September needed to have a different outcome)
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
#Mental illness diagnosis 
    def showIllegalMoveMessage(self):
        self.messageLog.send_message("Illegal move! Please try again.")

    def clearIllegalMoveMessage(self):
        self.messageLog.send_message("")