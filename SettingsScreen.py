from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QFrame
)
from PyQt5.QtGui import QFont, QColor
from Yavalath.YavalathBoard import Board
from UI.Buttons import TextButton
from UI.StarLogoWidget import StarLogoWidget
import math
from PyQt5.QtGui import QGuiApplication
from UI.Buttons import TickBoxButton

class SettingsScreen(QWidget):
    startGameRequested = pyqtSignal(dict)

    rules = {
        "Yavalath": (
            "Yavalath Rules:\n"
            "- Goal: Create a line of 4 pieces before your opponent.\n"
            "- You lose if you create a line of 3 pieces first.\n"
        ),
        "Pentalath": (
            "Pentalath Rules:\n"
            "- Goal: Create a line of 5 pieces.\n"
            "- Surround a group of enemy pieces to remove them from the board.\n"
        ),
        "Susan": (
            "Susan Rules:\n"
            "- Goal: Capture an opponent piece without losing one of your on.\n"
            "- You can either move or place down a new piece each turn\n"
            "- A piece is captured when it has no free spaces on any side."
        )
    }


    def __init__(self, parent=None):

        """
        Controls the setting screen of the game, where players can select game mode, difficulty, and time limits before starting a new game. It also displays the rules for each game mode
        BUTTONS:
        - Game mode selection: Yavalath, Pentalath, Susan (only one can be selected at a time)
        - Player mode selection: Human vs AI (checkbox)
        - Difficulty selection: Easy, Medium, Hard, Extreme (only enabled if Human vs AI is selected, only one can be selected at a time)
        - Time limit selection: 5s, 10s, 30s, 90s (only one can be selected at a time)
        - Begin Game (enabled only when all required options are selected)
        - Quit (always enabled)

        Upon pressing begin game a signal is sent to the main function that the game has started.
        If quit is pressed the eventHandler closes the app.
        """

        #Still technically a widget because layouts
        super().__init__(parent)
        #Just in case

        #Screen dimensions
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.SCREEN_WIDTH = geometry.width()
        self.SCREEN_HEIGHT = geometry.height()
        #print(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        #TITLES
        fontTimes = "Times New Roman"
        fontButtons = "Arial"
        mainTitle = "Pentalath, Yavalath, Susan"
        newGameSubtitle = "Create New Game"



        #Smart way to do background without using built in background
        self.backgroundFrame = QFrame(self)
        self.backgroundFrame.setStyleSheet("background-color: black;")
        self.backgroundFrame.setGeometry(self.rect())
        self.backgroundFrame.lower()
        self.backgroundFrame.setFixedSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #dddddd;
                font-family: Times New Roman;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }
        """)

        #Main margins
        mainVerticalLayout = QVBoxLayout(self)
        mainVerticalLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        mainVerticalLayout.setSpacing(self.standardised(15))

        #Title box setup
        self.titleContainer = QFrame(self)
        borderRadius = self.standardised(20)
        border = 2
        self.titleContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: {border}px solid #444444;"
        )
        self.titleContainer.setFixedHeight(self.standardised(100))
        titleLayout = QVBoxLayout(self.titleContainer)
        titleLayout.setContentsMargins(0, 0, 0, 0)

        #Title text
        self.titleLabel = QLabel(mainTitle, self.titleContainer)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont(fontTimes, self.standardised(40), QFont.Bold))
        self.titleLabel.setStyleSheet("background: transparent; color: white; border: none;")
        titleLayout.addWidget(self.titleLabel)
        mainVerticalLayout.addWidget(self.titleContainer)

    
        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        mainLayout.setSpacing(self.standardised(40))

        #Left box
        self.leftContainer = QFrame()
        borderRadius = self.standardised(20)
        self.leftContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: 2px solid #444444;"
        )
        self.leftContainer.setFixedWidth(self.standardised(440))
        mainLayout.addWidget(self.leftContainer)

        #Right box
        self.rightContainer = QFrame()
        self.rightContainer.setStyleSheet(
            "background-color: #1E1E1E; border-radius: 20px; border: 2px solid #444444;"
        )
        mainLayout.addWidget(self.rightContainer)
        #Right box margins
        rightLayout = QVBoxLayout(self.rightContainer)
        rightLayout.setContentsMargins(self.standardised(40), self.standardised(40), self.standardised(40), self.standardised(40))
        rightLayout.setSpacing(self.standardised(20))
        rightLayout.setAlignment(Qt.AlignCenter)

        #Board params
        self.boardSize = 5
        self.boardHexRadius = self.standardised(60)
        self.selectedColors = {
            "player1": QColor("white"),
            "player2": QColor("#FF4080"),
            "empty": QColor("#1E283C"),
            "border": QColor("#00C8FF"),
        }
        #Unused artificial delay for AI vs AI games to make an impression of thinking
        self.demoBoardMoveDelay = 1000

        #Board object creation
        self.boardWidget = Board(
            side=self.boardSize,
            radius=self.boardHexRadius,
            colors=self.selectedColors,
            ai_move_delay=self.demoBoardMoveDelay,
            mode="ai_vs_ai"
        )

        #Idk what this actually does but it allows resizing
        self.boardWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        #Board params math
        boardWidth = int(self.boardHexRadius * 2 * (self.boardSize + 0.5)) * 2
        boardHeight = int(math.sqrt(3) * self.boardHexRadius * (self.boardSize + 1)) * 2
        self.boardWidget.setMinimumSize(boardWidth, boardHeight)

        #Board container widget creation
        boardContainer = QVBoxLayout()
        boardContainer.addStretch(1)
        boardContainer.addWidget(self.boardWidget, alignment=Qt.AlignCenter)
        boardContainer.addStretch(1)
        rightLayout.addLayout(boardContainer)


        mainVerticalLayout.addLayout(mainLayout)
        #left laout widget creation within leftContainer - also margins
        self.leftLayout = QVBoxLayout(self.leftContainer)
        self.leftLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        self.leftLayout.setSpacing(self.standardised(25))

        #Subtitile label creation
        self.subtitleLabel = QLabel(newGameSubtitle)
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel.setFont(QFont("Arial", self.standardised(26), QFont.Bold))
        self.subtitleLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.subtitleLabel)

        #Logo widget setup and creation - it is aggregated to the leftlayout widget
        self.logoWidgetSize = 350
        self.logoWidget = StarLogoWidget(self.leftContainer)
        self.logoWidget.setFixedSize(self.standardised(self.logoWidgetSize), 
                                self.standardised(self.logoWidgetSize))
        self.leftLayout.insertWidget(0, self.logoWidget, alignment=Qt.AlignCenter)

        #Label text
        modeLabel = QLabel("Select Game Mode:")
        modeLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        modeLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(modeLabel)

        #Button creation and labels
        self.modeButtons = [TextButton(name, checkable=True) for name in ["Yavalath", "Pentalath", "Susan"]] #Fancy
        modeLayout = QHBoxLayout()
        modeLayout.setSpacing(self.standardised(20))

        #Setup each button to be identical
        for btn in self.modeButtons:
            btn.setFixedSize(self.standardised(130), self.standardised(50))
            btn.clicked.connect(self.handleGameModeClicked)
            btn.setToolTip(self.rules.get(btn.text(), ""))
            btn.setStyleSheet("border: none; background: transparent;")
            modeLayout.addWidget(btn)
        self.leftLayout.addLayout(modeLayout)

        # Add Player Mode Selection (Human vs AI)
        playerModeLabel = QLabel("Game Type:")
        playerModeLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        playerModeLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(playerModeLabel)

        #More setup for player mode button - checkbox
        self.playerModeButton = TickBoxButton(text="Human vs AI", checkable=True)
        self.playerModeButton.setFixedSize(self.standardised(200), self.standardised(40))
        self.playerModeButton.setChecked(True)  # Default to Human vs AI
        self.playerModeButton.checkedChanged.connect(self.handlePlayerModeChanged)
        self.playerModeButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.playerModeButton, alignment=Qt.AlignLeft)

        #Difficulty button label
        difficultyLabel = QLabel("Select Difficulty:")
        difficultyLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        difficultyLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(difficultyLabel)

        #Difficulty button creation and setup - only one can be selected
        self.difficultyButtons = []
        difficultyLayout = QHBoxLayout()
        difficultyLayout.setSpacing(self.standardised(15))
        for label in ["Easy", "Medium", "Hard", "Extreme"]:
            btn = TextButton(label, checkable=True)
            btn.setFixedSize(self.standardised(100), self.standardised(40))
            btn.clicked.connect(self.handleDifficultyClicked)
            btn.setStyleSheet("border: none; background: transparent;")
            self.difficultyButtons.append(btn)
            difficultyLayout.addWidget(btn)
        self.leftLayout.addLayout(difficultyLayout)

        #Label for time option buttons
        timeLabel = QLabel("Move Time Limit:")
        timeLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        timeLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(timeLabel)

        #Options for time limit - buttons - only one can be selected
        self.timeOptionButtons = []
        timeOptionsLayout = QHBoxLayout()
        timeOptionsLayout.setSpacing(self.standardised(18))
        timeValues = [("5s", 5000), ("10s", 10000), ("30s", 30000), ("90s", 90000)]
        for label, ms in timeValues:
            btn = TextButton(label, checkable=True)
            btn.time_ms = ms
            btn.setFixedSize(self.standardised(90), self.standardised(40))
            btn.clicked.connect(self.handleTimeOptionClicked)
            btn.setStyleSheet("border: none; background: transparent;")
            self.timeOptionButtons.append(btn)
            timeOptionsLayout.addWidget(btn)
        self.leftLayout.addLayout(timeOptionsLayout)

        self.leftLayout.addStretch()

        #Begin game button setup - only enabled when all required options are selected
        self.beginGameButton = TextButton("Begin Game", checkable=False)
        self.beginGameButton.setFixedSize(self.standardised(200), self.standardised(52))
        self.beginGameButton.clicked.connect(self.onStartGameClicked)
        self.beginGameButton.setEnabled(False)
        self.beginGameButton.setClickable(False)
        self.beginGameButton.setOpacity(0.4)
        self.beginGameButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.beginGameButton, alignment=Qt.AlignCenter)


        #Always visible quit button
        self.quitButton = TextButton("Quit", checkable=False)
        self.quitButton.setFixedSize(self.standardised(120), self.standardised(44))
        self.quitButton.clicked.connect(self.closeApp)
        self.quitButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.quitButton, alignment=Qt.AlignCenter)

        # Initialize UI button state
        for btn in self.difficultyButtons:
            btn.setEnabled(True)
            btn.setClickable(True)
            btn.setOpacity(1.0)

        for btn in self.timeOptionButtons:
            btn.setEnabled(True)
            btn.setClickable(True)
            btn.setOpacity(1.0)

        #Default options are only that vs computer player is on
        self.modeButtons[0].setChecked(True)
        self.handleGameModeClicked()

    def standardised(self,value):
        """Scales values based on screen height"""
        return int(value * self.SCREEN_HEIGHT / 1600) 
    
    def handlePlayerModeChanged(self, is_ai_game):
        # Difficulty buttons only matter for AI games

        for btn in self.difficultyButtons:
            btn.setEnabled(is_ai_game)
            btn.setClickable(is_ai_game)
            btn.setOpacity(1.0 if is_ai_game else 0.4)

        # Preserve current selection for time options
        selected_time_btn = next((btn for btn in self.timeOptionButtons if btn.checked), None)

        for btn in self.timeOptionButtons:
            btn.setEnabled(True)
            btn.setClickable(True)
            btn.setOpacity(1.0)
            btn.setChecked(btn == selected_time_btn)  # Restore visual state

        
        # If switching to human vs human, uncheck difficulty options only
        if not is_ai_game:
            for btn in self.difficultyButtons:
                btn.setChecked(False)

        self.updateBeginGameButton()



    def handleGameModeClicked(self):
        #Ensures that only one game mode can be selected at any time
        sender = self.sender()
        #Sender method returns the object that triggered the function

        if sender and isinstance(sender, TextButton):
            for btn in self.modeButtons:
                btn.setChecked(btn == sender)
        else:
            for btn in self.modeButtons:
                btn.setChecked(False)

        self.updateBeginGameButton()

    def handleDifficultyClicked(self):
        #Handler method to make sure that only one difficulty can be selected
        sender = self.sender()
        if not sender:
            return
        for btn in self.difficultyButtons:
            btn.setChecked(btn == sender)
        self.updateBeginGameButton()

    def handleTimeOptionClicked(self):
        #Ensures that only one time option can be selected at any time
        sender = self.sender()
        if not sender:
            return
        for btn in self.timeOptionButtons:
            btn.setChecked(btn == sender)
        self.selectedAiMoveDelay = sender.time_ms
        self.updateBeginGameButton()

    def updateBeginGameButton(self):
        #Handles the begin game button. If all requirements are met it is enabled and clickable.
        modeSelected = any(btn.checked for btn in self.modeButtons)
        isAiGame = self.playerModeButton.isChecked()

        # Difficulty is required only if playing against AI
        difficultySelected = True if not isAiGame else any(btn.checked for btn in self.difficultyButtons)

        # Time option is always required
        timeOptionSelected = any(btn.checked for btn in self.timeOptionButtons)

        canBegin = modeSelected and difficultySelected and timeOptionSelected

        self.beginGameButton.setEnabled(canBegin)
        self.beginGameButton.setClickable(canBegin)
        self.beginGameButton.setOpacity(1.0 if canBegin else 0.4)


    def gatherGameSettings(self):
        """
        Method to collect all the settings that are selected by the user. Only called after the begin game button is pressed, 
        so it can be assumed that all required settings are selected and valid. It returns a dictionary of settings ready to be processed by the game.
        """
        selectedMode = next((btn.text() for btn in self.modeButtons if btn.checked), None)

        selectedDifficulty = None
        if self.playerModeButton.isChecked():  # Only for AI games
            selectedDifficulty = next((btn.text() for btn in self.difficultyButtons if btn.checked), None)

        #Always fall back to default if none selected
        selectedAiDelay = next((btn.time_ms for btn in self.timeOptionButtons if btn.checked), self.selectedAiMoveDelay)

        settings = {
            "mode": selectedMode,
            "difficulty": selectedDifficulty,
            "ai_move_delay": selectedAiDelay,
            "game_type": "ai_vs_ai" if self.playerModeButton.isChecked() else "human"
        }
        return settings


    def onStartGameClicked(self):
        #Small method that is called when the begin game function is pressed
        settings = self.gatherGameSettings()
        print("DEBUG: Starting game with settings:", settings)
        self.startGameRequested.emit(settings)

    def closeApp(self):
        #Closes app when quit button pressed
        QApplication.quit()
