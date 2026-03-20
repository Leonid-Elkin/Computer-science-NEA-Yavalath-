import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from Yavalath.YavalathGamestate import GameState
from ElkUtils.ThreadWorker import AIWorker
from UI.BoardUI import BoardGraphics  # UI widget
from copy import deepcopy

class Board(QWidget):
    moveMade = pyqtSignal()
    gameOver = pyqtSignal()
    player1Win = pyqtSignal()
    player2Win = pyqtSignal()
    drawGame = pyqtSignal()

    def __init__(
    self,
    side=5,
    radius=30,
    colors=None,
    ai_move_delay=500,
    mode="ai",
    human_player=1,
    depth=4,
    beamwidth=10,
    wait_for_message=False,
    message_handler=None,  # NEW: external message handler
    parent=None
):
        super().__init__(parent)

        print("Created new object")
        self.side = side
        self.radius = radius
        self.colors = colors
        self.depth = depth
        self.beamwidth = beamwidth
        self.ai_move_delay = ai_move_delay
        self.mode = mode
        self.human_player = human_player
        self.wait_for_message = wait_for_message
        self.winning_line = []
        self.recent_moves = []

        self.message_handler = message_handler  # external communicator

        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.ai_worker = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.board_graphics = BoardGraphics(controller=self, radius=self.radius, colors=self.colors)
        self.layout.addWidget(self.board_graphics)

        self.moveMade.connect(self.board_graphics.update)

        self.start_game()
        print(self.mode)

        if self.mode == "ai_vs_ai":
            self.board_graphics.toggleHover(False)
            # Optional: also prevent last-move marker for AI vs AI
            self.board_graphics.show_last_move = False
        else:
            self.board_graphics.toggleHover(True)
            self.board_graphics.show_last_move = True

    def start_game(self):
        self.reset_game()
        if self.mode == "ai_vs_ai":
            self.start_ai_turn()
        elif self.mode == "ai" and self.current_player != self.human_player:
            self.start_ai_turn()
        # NO AI turns started if mode == "human"


    def reset_game(self):
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.recent_moves = []
        if hasattr(self.board_graphics, "reset"):
            self.board_graphics.reset()
        self.moveMade.emit()

    def start_ai_turn(self):
        if self.game_over:
            return
        if self.mode == "human":
            return  # No AI turns at all in human mode
        if self.mode == "ai_vs_ai" or self.mode == "ai":
            pass  # Allow AI turn regardless of current_player
        if self.ai_worker and self.ai_worker.isRunning():
            return

        game_state_copy = deepcopy(self.game_state)
        self.ai_worker = AIWorker(game_state_copy, self.current_player, max_depth=self.depth, beam_width=self.beamwidth)
        self.ai_worker.moveReady.connect(self.on_ai_move_ready)
        self.ai_worker.start()



    def on_ai_move_ready(self, move):
        if move and not self.game_over:
            self.game_state.make_move(move, self.current_player)

            msg = f"Player {self.current_player} placed piece in {move[0]},{move[1]}"
            self._send_message(msg)  # UPDATED

            self.moveMade.emit()
            self.current_player = 3 - self.current_player

            if self.game_state.is_terminal():
                self.game_over = True
                self.gameOver.emit()
                self._emit_game_result()
                self._send_message("Game over")  # UPDATED
                if not self.wait_for_message:
                    QTimer.singleShot(1000, self.start_game)
                return

            if self.mode == "ai_vs_ai" or (self.mode == "ai" and self.current_player != self.human_player):
                QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)


    def make_human_move(self, move):
        if self.mode == "human":
            pass
        elif self.mode == "ai":
            if self.current_player != self.human_player:
                return False
        else:
            return False

        if self.game_over:
            return False
        if self.game_state.board.get(move, -1) != 0:
            return False

        self.game_state.make_move(move, self.current_player)

        msg = f"Player {self.current_player} placed piece in {move[0]},{move[1]}"
        self._send_message(msg)  # UPDATED

        self.moveMade.emit()
        self.current_player = 3 - self.current_player

        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("Game over")  # UPDATED
            if not self.wait_for_message:
                QTimer.singleShot(1000, self.start_game)
            return True

        if self.mode in ["ai_vs_ai", "ai"]:
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

        return True



    def _emit_game_result(self):
        winner = None
        self.winning_line = []
        if hasattr(self.game_state, 'get_winner'):
            winner = self.game_state.get_winner()
        if winner in [1, 2]:
            self.winning_line = self.game_state.get_winning_line()

        if winner == 1:
            self.player1Win.emit()
            self._send_message("Player 1 wins!")  # UPDATED
        elif winner == 2:
            self.player2Win.emit()
            self._send_message("Player 2 wins!")  # UPDATED
        elif winner == 0:
            self.drawGame.emit()
            self._send_message("Game is a draw!")  # UPDATED
        else:
            self._send_message("DEBUG: NO WIN/DRAW CONDITION")  # UPDATED

        self.moveMade.emit()  


    def continue_game(self):
        if self.game_over and self.wait_for_message:
            self.start_game()

    def _on_game_over(self):
        self.reset_game()

    def play_again(self):
        """
        Called when the Play Again button is pressed.
        Resets the board and starts the game loop based on the current mode.
        """
        self.start_game()

    def _send_message(self, msg):
        # Keep recent moves locally
        self.recent_moves.append(msg)
        if len(self.recent_moves) > 5:
            self.recent_moves.pop(0)

        # Send to external handler if provided
        if self.message_handler:
            if callable(self.message_handler):
                self.message_handler(msg)
            elif hasattr(self.message_handler, "send_message"):
                self.message_handler.send_message(msg)
