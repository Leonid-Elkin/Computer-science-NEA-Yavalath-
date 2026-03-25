import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from Pentalath.PentalathGamestate import GameState
from ElkUtils.ThreadWorker import AIWorker
from UI.BoardUI import BoardGraphics  # UI widget
from copy import deepcopy


class Board(QWidget):
    #Signals emitted on game events
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
        mode="ai_vs_ai",
        human_player=1,
        depth=4,
        beamwidth=10,
        wait_for_message=False,
        message_handler=None,  # external message handler, like in Yavalath
        parent=None
    ):
        super().__init__(parent)
        #Params
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
        self.message_handler = message_handler
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.ai_worker = None

        #For consistency margins are 0
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.board_graphics = BoardGraphics(controller=self, radius=self.radius, colors=self.colors)
        self.layout.addWidget(self.board_graphics)

        #Update board graphics every time move made
        self.moveMade.connect(self.board_graphics.update)

        self.start_game()

        #Disable hover and last-move markers for AI vs AI because no human interactions
        if self.mode == "ai_vs_ai":
            self.board_graphics.toggleHover(False)
            self.board_graphics.show_last_move = False
        else:
            self.board_graphics.toggleHover(True)
            self.board_graphics.show_last_move = True

    def start_game(self):
        self.reset_game()

        #Kick off the first AI turn if applicable
        if self.mode == "ai_vs_ai":
            self.start_ai_turn()
        elif self.mode == "ai" and self.current_player != self.human_player:
            self.start_ai_turn()

    def reset_game(self):
        #Rebuilds game state and resets all tracking variables to their initial values
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.recent_moves = []

        #reset signal catcher
        if hasattr(self.board_graphics, "reset"):
            self.board_graphics.reset()

        #Update
        self.moveMade.emit()

    def start_ai_turn(self):
        if self.game_over:
            return
        if self.mode == "human":
            return

        #Avoid launching a second worker if one is already running
        if self.ai_worker and self.ai_worker.isRunning():
            return

        #Param passing into AIWorker
        game_state_copy = deepcopy(self.game_state)
        self.ai_worker = AIWorker(
            game_state_copy,
            self.current_player,
            max_depth=self.depth,
            beam_width=self.beamwidth,
            ai="Pentalath"
        )
        #Communicator
        self.ai_worker.moveReady.connect(self.on_ai_move_ready)
        self.ai_worker.start()

    def on_ai_move_ready(self, move):
        #Receives the move chosen by the AI worker thread and applies it to the live game state
        if not move or self.game_over:
            return

        #Logger
        captured = self.game_state.make_move(move, self.current_player)
        msg = f"AI Player {self.current_player} placed piece in {move[0]},{move[1]}"
        if captured:
            msg += f" | Captured: {captured}"
        self._send_message(msg)

        self.moveMade.emit()
        self.current_player = 3 - self.current_player  #swap players

        #Check game-ending conditions
        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("Game over")

            if not self.wait_for_message:
                QTimer.singleShot(1000, self.start_game)
            return

        #Schedule the next AI turn after the configured delay
        if self.mode == "ai_vs_ai" or (self.mode == "ai" and self.current_player != self.human_player):
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

    def make_human_move(self, move):
        #Reject input if it is not this human's turn
        if self.mode == "ai" and self.current_player != self.human_player:
            return False
        if self.mode not in ["human", "ai"]:
            return False
        if self.game_over:
            return False

        #Reject if the target cell is already occupied
        if self.game_state.board.get(move, -1) != 0:
            return False

        #Logger for valid move
        captured = self.game_state.make_move(move, self.current_player)
        msg = f"Player {self.current_player} placed piece in {move[0]},{move[1]}"
        if captured:
            msg += f" | Captured: {captured}"
        self._send_message(msg)

        self.moveMade.emit()  #Update
        self.current_player = 3 - self.current_player

        #Terminal move checker
        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("Game over")

            if not self.wait_for_message:
                QTimer.singleShot(1000, self.start_game)
            return True

        #Start AI turn only when ai_vs_ai is enabled to prevent the two bots from instantly moving
        if self.mode in ["ai_vs_ai", "ai"]:
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

        return True

    def _emit_game_result(self):
        winner = None
        self.winning_line = []

        #Receives signal of who won
        if hasattr(self.game_state, "get_winner"):
            winner = self.game_state.get_winner()

        #Retrieve the winning line only for a decisive result
        if winner in [1, 2]:
            self.winning_line = self.game_state.get_winning_line()

        #Show message of who wins
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

    def continue_game(self):
        #Called externally once an awaited message has been acknowledged
        if self.game_over and self.wait_for_message:
            self.start_game()

    def _on_game_over(self):
        #Internal slot connected to the gameOver signal
        self.reset_game()

    def play_again(self):
        #Called when the Play Again button is pressed
        self.start_game()

    def _send_message(self, msg):
        #Keep a rolling window of the last 5 messages for local inspection
        self.recent_moves.append(msg)
        if len(self.recent_moves) > 5:
            self.recent_moves.pop(0)

        #Forward to the external handler if one was provided
        if self.message_handler:
            if callable(self.message_handler):
                self.message_handler(msg)
            elif hasattr(self.message_handler, "send_message"):
                self.message_handler.send_message(msg)