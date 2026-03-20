# ElkUtils/ThreadWorker.py
from PyQt5.QtCore import QThread, pyqtSignal
from Yavalath.YavalathMinimax import MinimaxPlayer as YavalathAI
from Pentalath.MinimaxAiPentalath import PentalathMinimaxPlayer as PentalathAI
from Susan.MinimaxAiSusan import SusanMinimaxPlayer as SusanAI


class AIWorker(QThread):
    """
    Worker thread for running AI calculations without blocking the GUI.
    Supports different game types: Yavalath, Pentalath, and Susan.
    """
    moveReady = pyqtSignal(object)  # Emits the best move when ready

    def __init__(self, game_state, player_id, max_depth=4, beam_width=10, ai="Yavalath", parent=None):
        super().__init__(parent)
        self.game_state = game_state
        self.player_id = player_id
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.ai_type = ai
        self.best_move = None

    def run(self):
        """
        Execute the AI calculation in a separate thread.
        This method is called automatically when start() is called on this thread.
        """
        try:
            # Create the appropriate AI player based on game type
            if self.ai_type == "Yavalath":
                ai_player = YavalathAI(
                    player_id=self.player_id,
                    max_depth=self.max_depth,
                    beam_width=self.beam_width
                )
                self.best_move = ai_player.make_move(self.game_state)
                
            elif self.ai_type == "Pentalath":
                ai_player = PentalathAI(
                    player_id=self.player_id,
                    max_depth=self.max_depth,
                    beam_width=self.beam_width
                )
                self.best_move = ai_player.make_move(self.game_state)
                
            elif self.ai_type == "Susan":
                ai_player = SusanAI(
                    player_id=self.player_id,
                    max_depth=self.max_depth,
                    beam_width=self.beam_width
                )
                self.best_move = ai_player.get_move(self.game_state)
                
            else:
                print(f"Unknown AI type: {self.ai_type}")
                self.best_move = None

            # Emit the result
            self.moveReady.emit(self.best_move)
            
        except Exception as e:
            print(f"AI Worker error: {e}")
            import traceback
            traceback.print_exc()
            self.moveReady.emit(None)