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
        ),
    }

    def __init__(self, parent=None):
        #Still technically a widget because layouts yay might not be the right way to do 
        super().__init__(parent)

        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        self.SCREEN_WIDTH = geometry.width()
        self.SCREEN_HEIGHT = geometry.height()

    
        
        print(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        #TITLES!
        fontTimes = "Times New Roman"
        fontButtons = "Arial"
        mainTitle = "Pentalath, Yavalath, Susan"
        newGameSubtitle = "Create New Game"



        #based 'background'
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

        mainVerticalLayout = QVBoxLayout(self)
        mainVerticalLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        mainVerticalLayout.setSpacing(self.standardised(15))

        self.titleContainer = QFrame(self)
        borderRadius = self.standardised(20)
        border = 2
        self.titleContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: {border}px solid #444444;"
        )
        self.titleContainer.setFixedHeight(self.standardised(100))
        titleLayout = QVBoxLayout(self.titleContainer)
        titleLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = QLabel(mainTitle, self.titleContainer)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.titleLabel.setFont(QFont(fontTimes, self.standardised(40), QFont.Bold))
        self.titleLabel.setStyleSheet("background: transparent; color: white; border: none;")
        titleLayout.addWidget(self.titleLabel)
        mainVerticalLayout.addWidget(self.titleContainer)

        mainLayout = QHBoxLayout()
        mainLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        mainLayout.setSpacing(self.standardised(40))

        self.leftContainer = QFrame()
        borderRadius = self.standardised(20)
        self.leftContainer.setStyleSheet(
            f"background-color: #1E1E1E; border-radius: {borderRadius}px; border: 2px solid #444444;"
        )
        self.leftContainer.setFixedWidth(self.standardised(440))
        mainLayout.addWidget(self.leftContainer)

        self.rightContainer = QFrame()
        self.rightContainer.setStyleSheet(
            "background-color: #1E1E1E; border-radius: 20px; border: 2px solid #444444;"
        )
        mainLayout.addWidget(self.rightContainer)

        rightLayout = QVBoxLayout(self.rightContainer)
        rightLayout.setContentsMargins(self.standardised(40), self.standardised(40), self.standardised(40), self.standardised(40))
        rightLayout.setSpacing(self.standardised(20))
        rightLayout.setAlignment(Qt.AlignCenter)

        self.boardSize = 5
        self.boardHexRadius = self.standardised(60)
        self.selectedColors = {
            "player1": QColor("white"),
            "player2": QColor("#FF4080"),
            "empty": QColor("#1E283C"),
            "border": QColor("#00C8FF"),
        }
        self.demoBoardMoveDelay = 1000


        self.boardWidget = Board(
            side=self.boardSize,
            radius=self.boardHexRadius,
            colors=self.selectedColors,
            ai_move_delay=self.demoBoardMoveDelay,
            mode="ai_vs_ai"
        )

        self.boardWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        boardWidth = int(self.boardHexRadius * 2 * (self.boardSize + 0.5)) * 2
        boardHeight = int(math.sqrt(3) * self.boardHexRadius * (self.boardSize + 1)) * 2
        self.boardWidget.setMinimumSize(boardWidth, boardHeight)

        boardContainer = QVBoxLayout()
        boardContainer.addStretch(1)
        boardContainer.addWidget(self.boardWidget, alignment=Qt.AlignCenter)
        boardContainer.addStretch(1)
        rightLayout.addLayout(boardContainer)


        mainVerticalLayout.addLayout(mainLayout)

        self.leftLayout = QVBoxLayout(self.leftContainer)
        self.leftLayout.setContentsMargins(self.standardised(30), self.standardised(30), self.standardised(30), self.standardised(30))
        self.leftLayout.setSpacing(self.standardised(25))

        self.subtitleLabel = QLabel(newGameSubtitle)
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        self.subtitleLabel.setFont(QFont("Arial", self.standardised(26), QFont.Bold))
        self.subtitleLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.subtitleLabel)

        self.logoWidgetSize = 350
        self.logoWidget = StarLogoWidget(self.leftContainer)
        self.logoWidget.setFixedSize(self.standardised(self.logoWidgetSize), 
                                self.standardised(self.logoWidgetSize))
        self.leftLayout.insertWidget(0, self.logoWidget, alignment=Qt.AlignCenter)

        modeLabel = QLabel("Select Game Mode:")
        modeLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        modeLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(modeLabel)

        self.modeButtons = [TextButton(name, checkable=True) for name in ["Yavalath", "Pentalath", "Susan"]]
        modeLayout = QHBoxLayout()
        modeLayout.setSpacing(self.standardised(20))
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

        self.playerModeButton = TickBoxButton(text="Human vs AI", checkable=True)
        self.playerModeButton.setFixedSize(self.standardised(200), self.standardised(40))
        self.playerModeButton.setChecked(True)  # Default to Human vs AI
        self.playerModeButton.checkedChanged.connect(self.handlePlayerModeChanged)
        self.playerModeButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.playerModeButton, alignment=Qt.AlignLeft)

        difficultyLabel = QLabel("Select Difficulty:")
        difficultyLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        difficultyLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(difficultyLabel)

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

        timeLabel = QLabel("Move Time Limit:")
        timeLabel.setFont(QFont("Arial", self.standardised(18), QFont.Bold))
        timeLabel.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(timeLabel)

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

        self.beginGameButton = TextButton("Begin Game", checkable=False)
        self.beginGameButton.setFixedSize(self.standardised(200), self.standardised(52))
        self.beginGameButton.clicked.connect(self.onStartGameClicked)
        self.beginGameButton.setEnabled(False)
        self.beginGameButton.setClickable(False)
        self.beginGameButton.setOpacity(0.4)
        self.beginGameButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.beginGameButton, alignment=Qt.AlignCenter)

        self.quitButton = TextButton("Quit", checkable=False)
        self.quitButton.setFixedSize(self.standardised(120), self.standardised(44))
        self.quitButton.clicked.connect(self.closeApp)
        self.quitButton.setStyleSheet("border: none; background: transparent;")
        self.leftLayout.addWidget(self.quitButton, alignment=Qt.AlignCenter)

        # Initialize UI state
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
        sender = self.sender()




        #Temp solution to prevent computer games with Susan
        if sender and isinstance(sender, TextButton):
            for btn in self.modeButtons:
                btn.setChecked(btn == sender)
        else:
            for btn in self.modeButtons:
                btn.setChecked(False)
        
        selectedMode = next((btn.text() for btn in self.modeButtons if btn.checked), None)
        #      # if selectedMode == "Susan":
         #    #  print("susandetected")
          #  #   self.playerModeButton = TickBoxButton(text="Human vs AI", checkable=False)
           ##    self.playerModeButton.setFixedSize(self.standardised(200), self.standardised(40))
           ##    self.playerModeButton.setChecked(True)  # Default to Human vs AI
          #  #   self.playerModeButton.checkedChanged.connect(self.handlePlayerModeChanged)
         #    #  self.playerModeButton.setStyleSheet("border: none; background: transparent;")
        #      # self.leftLayout.addWidget(self.playerModeButton, alignment=Qt.AlignLeft)

        self.updateBeginGameButton()
        # This disables SUSAN computer player if I can't figure out a way to get my architecture to work with two move types.
        #Fuck fuck fuck fuck why haven't I planned this fuck its such a pain to do this i need to redo like everything I don't even remember how and why half my code works.

#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⣾⠿⠭⠽⠯⠯⠽⠿⣷⡶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣫⠎⠁⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠫⣛⠶⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⣠⣄⣄⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣾⡕⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠺⢝⡶⣄⡀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⡴⠶⠛⠉⠉⠁⠀⠈⠉⠉⠛⠳⠶⣤⢀⠀⠀⠀⠀⠀⣰⣿⠏⠀⢀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⣿⣦⡀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠶⠛⠋⢉⣡⠴⢦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠳⠶⣤⣼⠏⢀⣿⠟⠛⠛⠛⠿⢶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣻⣆⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠋⠁⢠⠖⠮⡉⠀⠀⠀⠙⣏⠐⠀⢇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠾⢷⣄⠀⠀⠀⠀⠀⠈⠙⠳⢦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣽⣧⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⡞⠀⠀⡸⢦⠀⠀⠀⠘⡆⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠴⣤⣀⠀⠀⠀⠀⠀⠉⠳⢦⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣾⣇
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣤⡀⠀⠀⠀⣯⠀⠀⣸⡄⢀⡼⠋⠀⢇⠀⠀⠀⢹⠀⡎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⢦⢄⠀⠀⠀⠀⠀⠉⠛⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿
#⠀⠀⠀⠀⠀⠀⢀⢤⣾⡿⠿⢿⣿⣷⣿⣿⣿⣿⣿⣷⣶⣿⣾⣥⠆⠀⠀⠸⡀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⣵⡀⠀⠀⠀⠀⠀⠀⠙⢷⣄⠀⠀⠀⠀⠀⢀⠆⣿
#⠀⠀⠀⠀⢠⣶⣿⠋⠁⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⡇⠀⠀⠀⢣⠀⠀⠀⠀⣴⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠙⣦⠀⠀⠀⠀⡎⢸⡏
#⠀⠀⢠⣶⣿⣿⣶⣾⣄⣤⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣋⣀⠀⠀⠀⡇⠀⠀⠀⡸⠀⠀⢀⠜⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣆⠀⠀⡜⢰⡟⠀
#⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⠏⠉⠠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⡁⠀⠀⢰⠁⠀⠀⠀⡇⠀⣠⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣦⠞⢰⡟⠀⠀
#⠀⢸⣿⣿⣿⢻⣿⣿⣿⣿⡿⠖⠀⣈⣙⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⡏⠀⠀⠀⠀⡇⡰⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡿⣧⡀⠀⠀⠀⠀⠀⠀⢀⣾⠃⢠⡟⠀⠀⠀
#⠀⣾⣿⣿⣧⣾⣿⣿⣿⣿⣿⣦⠈⣻⣿⣿⣿⣿⣿⣿⣿⡿⠁⠀⠀⠀⡸⠀⠀⠀⠀⢠⡗⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠈⢿⡄⠀⠀⠀⠀⢀⣾⠃⢠⡟⠁⠀⠀⠀
#⠘⣿⡟⣿⣿⣿⣿⣿⣿⣿⣿⣦⣄⣿⣿⣿⣿⣿⣿⣿⣿⠗⠀⠀⠀⢠⠇⠀⠀⠀⢀⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠄⠀⠀⠀⠀⠀⠀⠀⠀⢠⡻⠀⠀⠀⠀⢀⡾⠁⣰⡟⠀⠀⠀⠀⠀
#⠀⢽⣇⠉⢹⣿⣿⣿⠿⡇⠙⣿⣿⣿⣿⣿⣿⣿⣿⣟⡓⣤⣀⠀⠀⠘⢆⣀⡀⢀⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠴⠁⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣣⠀⠀⠀⢠⡾⠁⣰⡛⠀⠀⠀⠀⠀⠀
#⠀⠸⣿⣦⣼⣿⡟⠟⢀⡀⣶⣿⣿⣿⣿⣿⣿⣟⡭⠤⠜⠛⠋⠀⠀⣠⣞⣀⣼⠏⠀⢀⠄⠀⠀⠑⠤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⡻⠀⠀⢠⡾⠁⣰⠟⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠘⢿⣿⣿⣷⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⠿⠋⠀⠀⣠⣾⣿⣿⣿⡏⠐⠈⠀⠀⠀⠀⠀⠀⠈⠑⠢⠤⠄⣀⣀⠀⠀⡠⠊⠀⠀⠀⠀⠀⠀⠀⣀⣤⣴⣾⣿⣿⣿⡇⠀⢠⡾⠁⣴⠏⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣤⣴⣾⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣩⣏⣀⠀⠤⠄⠀⠀⠀⠀⣨⣾⣿⣿⣿⣿⣿⣿⣳⣴⡟⠀⣼⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⢸⡯⢿⣿⣿⣿⣿⡿⠟⠿⣿⣿⣿⣿⠙⢿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠴⢺⡁⠀⠀⠀⠀⠀⢀⣠⣴⣾⣿⣿⣿⣿⣿⣿⣿⡿⢈⠟⢀⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠸⠯⢿⣿⣿⡑⠒⠲⢞⡙⠈⠻⠇⠀⠀⠈⠙⠛⠿⠿⣿⣿⣿⣿⠆⠀⠀⠀⠀⠀⠀⠀⠠⠔⠈⠀⠀⠀⣿⣷⣶⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢁⠎⢀⠎⠈⠚⢵⣄⣀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠿⣇⣉⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠉⠻⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⠁⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢃⠎⢀⠎⠀⠀⠀⠀⠈⠹⣧⡀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢿⣿⣿⣿⣿⣿⣷⣦⣄⠀⠀⠀⠀⠀⠀⠈⠑⣄⠀⠀⠀⠀⠀⡠⠊⠀⠀⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⢁⠎⢠⣯⣽⣿⠆⠀⢀⡠⠜⠉⣿⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣶⣄⡀⠀⠀⠀⠀⠈⠢⡀⠀⠀⠀⢀⡀⠴⢒⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⢠⣷⣺⣿⣿⠟⠙⡖⠊⢉⣠⡶⠞⠁⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⣀⡀⠀⠀⠈⠁⠒⠈⠉⠀⠀⢘⣿⣿⣿⣿⣿⣿⡿⠿⠛⠉⠀⠀⠀⠀⠀⣠⠛⢼⠿⠛⣋⡆⠀⢳⡞⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢫⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣶⣤⣀⡀⠀⠀⠀⠀⠘⣿⡿⠿⠛⠋⠁⠀⠀⠀⠀⠀⢀⣀⠤⡾⢁⣠⣷⠶⠟⠛⣿⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣿⣿⣿⣿⡿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣄⣠⠞⠁⠀⠀⠀⠀⠀⢀⣠⠤⠖⢚⣉⣤⡾⠁⣨⡿⠁⠀⠀⠀⢹⡇⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢿⠷⣦⡈⠙⠶⣤⠤⠖⠒⣉⣩⣤⣒⠈⠉⠻⡟⠀⢰⡻⠁⠀⠀⠀⠀⠈⢿⡀⠈⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠈⠙⢶⣤⢤⡴⠾⠛⠋⠉⠀⠙⠷⣤⡜⠀⣰⠻⢷⢄⠀⠀⠀⠀⠀⠘⣧⠀⢹⡇⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⡄⠀⠀⠁⠁⠀⠀⠀⠀⠀⠀⠀⣰⠟⠀⣰⣧⣀⠀⠙⠻⣦⣀⠀⠀⠀⢻⡄⠈⣿⡀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡿⣿⣟⡿⠿⣿⣿⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏⠀⣰⡟⠁⠙⠷⢦⣀⠈⠛⢵⣄⡀⠸⣧⠀⠸⣇⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣼⡿⠿⣿⡿⠃⠀⠘⠛⠃⠀⢘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⢠⡟⠀⠀⠀⠀⠀⠻⢧⣄⠀⠘⠿⣻⣿⡀⠀⣿⡄⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡾⢭⣀⠀⠀⠸⡀⠀⠀⢀⣠⣔⣲⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣾⡄⠀⠀⠀⠀⠀⠀⣰⠟⠀⣰⠟⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⣦⡀⠈⠛⠇⠀⠸⣇⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠀⠀⠀⠑⣄⠀⣇⣠⣒⣽⠟⠉⠁⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⢀⣼⠏⠀⣴⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠷⣤⣀⣠⣼⠟⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢟⣖⡲⠤⠤⠞⢊⣡⠾⠋⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⢠⣾⠃⠀⣼⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠛⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀⢽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣷⣤⡿⠁⢀⣾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⢏⠁⢳⠈⠙⠀⢠⡾⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠾⠿⣟⣿⣟⣿⠿⠛⠉⠀⢀⣈⠷⢺⣧⣀⣠⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⠿⣅⠀⠀⠀⠚⣟⠡⠀⠀⣠⠖⢉⣤⡶⠟⠉⠉⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠇⠀⠈⢧⠀⠀⢠⠃⠁⢠⠞⢁⡴⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣷⡤⠤⠯⠤⠤⠧⠔⢺⣡⡶⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠛⠚⠛⠓⠒⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀



    def handleDifficultyClicked(self):
        sender = self.sender()
        if not sender:
            return
        for btn in self.difficultyButtons:
            btn.setChecked(btn == sender)
        self.updateBeginGameButton()

    def handleTimeOptionClicked(self):
        sender = self.sender()
        if not sender:
            return
        for btn in self.timeOptionButtons:
            btn.setChecked(btn == sender)
        self.selectedAiMoveDelay = sender.time_ms
        self.updateBeginGameButton()

    def updateBeginGameButton(self):
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
        selectedMode = next(
            (btn.text() for btn in self.modeButtons if btn.checked),
            None
        )

        # Difficulty only applies if playing vs AI
        selectedDifficulty = None
        if self.playerModeButton.isChecked():
            selectedDifficulty = next(
                (btn.text() for btn in self.difficultyButtons if btn.checked),
                None
            )

        # Always pick a move delay
        selectedAiDelay = next(
            (btn.time_ms for btn in self.timeOptionButtons if btn.checked),
            self.selectedAiMoveDelay
        )

        # Translate checkbox → GameScreen contract
        if self.playerModeButton.isChecked():
            computers = "1 Computer"      # Human vs AI
        else:
            computers = "0 Computers"     # Human vs Human

        settings = {
            "mode": selectedMode,
            "difficulty": selectedDifficulty,
            "ai_move_delay": selectedAiDelay,
            "computers": computers
        }

        return settings



    def onStartGameClicked(self):
        settings = self.gatherGameSettings()
        print("Starting game with settings:", settings)
        self.startGameRequested.emit(settings)

    def closeApp(self):
        QApplication.quit()
