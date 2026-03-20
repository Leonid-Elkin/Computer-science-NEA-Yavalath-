import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from Susan.SusanGamestate import GameState
from ElkUtils.ThreadWorker import AIWorker
from Susan.BoardUI import BoardGraphics  # UI widget
from copy import deepcopy


class Board(QWidget):
    moveMade = pyqtSignal()
    gameOver = pyqtSignal()
    player1Win = pyqtSignal()
    player2Win = pyqtSignal()
    drawGame = pyqtSignal()
    illegalMove = pyqtSignal()

    def __init__(
        self,
        side=5,
        radius=30,
        colors=None,
        ai_move_delay=500,
        mode="human_vs_ai",  # "human", "human_vs_ai", or "ai_vs_ai"
        human_player=1,
        depth=4,
        beamwidth=10,
        wait_for_message=False,
        message_handler=None,
        parent=None
    ):
        super().__init__(parent)

        print(f"[SusanBoard] Created new Susan board with mode={mode}, human_player={human_player}")
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

        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.ai_worker = None

        self.recent_moves = []
        self.message_handler = message_handler

        self.has_moved_this_turn = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.board_graphics = BoardGraphics(controller=self, radius=self.radius, colors=self.colors)
        self.layout.addWidget(self.board_graphics)

        self.moveMade.connect(self.board_graphics.update)

        # Use QTimer to delay AI start until after widget is fully initialized
        QTimer.singleShot(100, self.start_game)

    # -------------------------
    # Message Handling
    # -------------------------
    def _send_message(self, msg):
        self.recent_moves.append(msg)
        if len(self.recent_moves) > 5:
            self.recent_moves.pop(0)

        if self.message_handler:
            if callable(self.message_handler):
                self.message_handler(msg)
            elif hasattr(self.message_handler, "send_message"):
                self.message_handler.send_message(msg)

    # -------------------------
    # AI / Game Mode Control
    # -------------------------
    def set_human_vs_ai(self, human_vs_ai=True, human_player=1):
        """
        Configure board to play against AI or human.
        """
        if human_vs_ai:
            self.mode = "human_vs_ai"
            self.human_player = human_player
        else:
            self.mode = "human"
            self.human_player = None
        
        print(f"[SusanBoard] Mode set to {self.mode}, human_player={self.human_player}")

    def is_ai_turn(self):
        """Check if it's currently the AI's turn"""
        if self.mode == "ai_vs_ai":
            return True
        elif self.mode == "human_vs_ai":
            is_ai = self.current_player != self.human_player
            print(f"[SusanBoard] is_ai_turn check: current_player={self.current_player}, human_player={self.human_player}, result={is_ai}")
            return is_ai
        else:  # mode == "human"
            return False

    def start_game(self):
        print(f"[SusanBoard] Starting game with mode={self.mode}, human_player={self.human_player}, current_player={self.current_player}")
        self.reset_game()
        
        # Check if AI should play first and schedule it
        if self.is_ai_turn():
            print(f"[SusanBoard] AI should move first, scheduling AI turn")
            # Use a small delay to ensure everything is ready
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)
        else:
            print(f"[SusanBoard] Human should move first")

    def reset_game(self):
        print(f"[SusanBoard] Resetting game - mode={self.mode}, human_player={self.human_player}")
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.has_moved_this_turn = False
        self.winning_line = []
        if hasattr(self.board_graphics, "reset"):
            self.board_graphics.reset()
        self.moveMade.emit()

    # -------------------------
    # AI Turn
    # -------------------------
    def start_ai_turn(self):
        print(f"[SusanBoard] start_ai_turn called - game_over={self.game_over}, mode={self.mode}, current_player={self.current_player}")
        
        if self.game_over:
            print("[SusanBoard] Game over, not starting AI turn")
            return
        
        if not self.is_ai_turn():
            print(f"[SusanBoard] Not AI turn (mode={self.mode}, current_player={self.current_player}, human={self.human_player})")
            return
            
        if self.ai_worker and self.ai_worker.isRunning():
            print("[SusanBoard] AI worker already running")
            return

        print(f"[SusanBoard] Starting AI worker for player {self.current_player}")
        game_state_copy = deepcopy(self.game_state)
        self.ai_worker = AIWorker(
            game_state_copy,
            self.current_player,
            max_depth=self.depth,
            beam_width=self.beamwidth,
            ai="Susan"
        )
        self.ai_worker.moveReady.connect(self.on_ai_move_ready)
        self.ai_worker.start()
        print(f"[SusanBoard] AI worker started")

    def on_ai_move_ready(self, move):
        print(f"[SusanBoard] on_ai_move_ready called with move={move}, game_over={self.game_over}")
        
        if self.game_over or move is None:
            if move is None:
                print("[SusanBoard] AI returned no move")
            return

        print(f"[SusanBoard] Processing AI move: {move}")

        if isinstance(move, tuple) and len(move) == 2 and isinstance(move[0], tuple):
            from_pos, to_pos = move
            success = self.game_state.make_move(to_pos, self.current_player, from_pos=from_pos)
            move_desc = f"AI Player {self.current_player} moved piece from {from_pos} to {to_pos}"
        else:
            to_pos = move
            success = self.game_state.make_move(to_pos, self.current_player)
            move_desc = f"AI Player {self.current_player} placed piece at {to_pos}"

        if not success:
            self._send_message(f"Illegal AI move attempted by Player {self.current_player}: {move}")
            print(f"[SusanBoard] Illegal AI move: {move}")
            return

        print(f"[SusanBoard] AI move successful: {move_desc}")
        self._send_message(move_desc)
        self.moveMade.emit()
        self.current_player = 3 - self.current_player
        print(f"[SusanBoard] Current player now: {self.current_player}")

        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("AI move caused game over")
            if not self.wait_for_message:
                QTimer.singleShot(1000, self.start_game)
            return

        # Check if next turn is also AI
        if self.is_ai_turn():
            print(f"[SusanBoard] Next turn is also AI, scheduling next AI move")
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)
        else:
            print(f"[SusanBoard] Next turn is human")

    # -------------------------
    # Human Move
    # -------------------------
    def make_human_move(self, move, from_pos=None):
        print(f"[SusanBoard] make_human_move called: move={move}, from_pos={from_pos}, game_over={self.game_over}")
        
        if self.game_over:
            print("[SusanBoard] Game over, ignoring human move")
            return False

        # Check if it's human's turn
        if self.is_ai_turn():
            print(f"[SusanBoard] Not human's turn (mode={self.mode}, current={self.current_player})")
            return False

        current_player = self.current_player
        success = self.game_state.make_move(move, current_player, from_pos=from_pos)
        if not success:
            self.illegalMove.emit()
            self._send_message(f"Illegal move attempted by Player {current_player}: {move}")
            print(f"[SusanBoard] Illegal human move")
            return False

        action = f"placed at {move}" if from_pos is None else f"moved from {from_pos} to {move}"
        self._send_message(f"Player {current_player} {action}")
        print(f"[SusanBoard] Human move successful: {action}")
        self.moveMade.emit()
        self.current_player = 3 - current_player
        print(f"[SusanBoard] Current player now: {self.current_player}")

        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("Human move caused game over")
        else:
            # Check if next turn is AI
            if self.is_ai_turn():
                print(f"[SusanBoard] Next turn is AI, scheduling AI move")
                QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

        return True

    # -------------------------
    # Game Result / UI
    # -------------------------
    def _emit_game_result(self):
        winner = None
        self.winning_line = []
        if hasattr(self.game_state, 'get_winner'):
            winner = self.game_state.get_winner()
        if winner in [1, 2]:
            self.winning_line = self.game_state.get_winning_line()

        if winner == 1:
            self.player1Win.emit()
            self._send_message("Player 1 wins!")
        elif winner == 2:
            self.player2Win.emit()
            self._send_message("Player 2 wins!")
        elif winner == 0:
            self.drawGame.emit()
            self._send_message("Game is a draw!")
        else:
            self._send_message("Game not finished or unknown result")

        self.moveMade.emit()
        self._send_message("Game over")

    # -------------------------
    # Reset / Continue
    # -------------------------
    def continue_game(self):
        if self.game_over and self.wait_for_message:
            self.start_game()

    def reset_board_state(self):
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.has_moved_this_turn = False
        if hasattr(self.board_graphics, "reset"):
            self.board_graphics.reset()
        self.moveMade.emit()
        self.board_graphics.update()