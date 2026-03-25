from PyQt5.QtCore import QThread, pyqtSignal
from Yavalath.YavalathMinimax import MinimaxPlayer as YavalathAI
from Pentalath.MinimaxAiPentalath import PentalathMinimaxPlayer as PentalathAI
from Susan.MinimaxAiSusan import SusanMinimaxPlayer as SusanAI


class AIWorker(QThread):
    moveReady = pyqtSignal(object)

    def __init__(self, game_state, player_id, max_depth=4,
                 beam_width=10, ai="Yavalath", parent=None):
        """
        AI WORKER THREAD - USED TO RUN AI MOVE CALCULATIONS WITHOUT FREEZING THE GUI
        Interface between GUI and AI logic, handles loading in different minimax players
        
        Supports:
        - Yavalath
        - Pentalath
        - Susan

        Once calculation is complete, sends out the best move via moveReady signal
        """

        super().__init__(parent)

        # Store game configuration
        self.gameState = game_state
        self.playerId = player_id
        self.maxDepth = max_depth
        self.beamWidth = beam_width
        self.aiType = ai

        # Output
        self.bestMove = None

    def run(self):
        """
        Main execution method for the thread
        Automatically called when start() is invoked because this class inherits from QThread
        """

        # Select appropriate AI based on game type
        if self.aiType == "Yavalath":
            aiPlayer = YavalathAI(
                player_id=self.playerId,
                max_depth=self.maxDepth,
                beam_width=self.beamWidth
            )
            self.bestMove = aiPlayer.make_move(self.gameState)

        elif self.aiType == "Pentalath":
            aiPlayer = PentalathAI(
                player_id=self.playerId,
                max_depth=self.maxDepth,
                beam_width=self.beamWidth
            )
            self.bestMove = aiPlayer.make_move(self.gameState)

        elif self.aiType == "Susan":
            aiPlayer = SusanAI(
                player_id=self.playerId,
                max_depth=self.maxDepth,
                beam_width=self.beamWidth
            )
            self.bestMove = aiPlayer.get_move(self.gameState)

        else:
            print("ERROR: You mistyped the ai name")
            self.bestMove = None

        # Emit result back to GUI thread
        self.moveReady.emit(self.bestMove)