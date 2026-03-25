import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from Susan.SusanGamestate import GameState
from ElkUtils.ThreadWorker import AIWorker
from Susan.SusanBoardUI import BoardGraphics
from copy import deepcopy


class Board(QWidget):
    #Signals emitted on game events
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
        mode="human_vs_ai",
        human_player=1,
        depth=4,
        beamwidth=10,
        wait_for_message=False,
        message_handler=None,
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
        self.has_moved_this_turn = False

        #For consistency margins are 0
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.board_graphics = BoardGraphics(controller=self, radius=self.radius, colors=self.colors)
        self.layout.addWidget(self.board_graphics)

        #Update board graphics every time a move is made
        self.moveMade.connect(self.board_graphics.update)

        #Delay AI start until after the widget is fully initialised
        QTimer.singleShot(100, self.start_game)

    def set_human_vs_ai(self, human_vs_ai=True, human_player=1):
        """
        Reconfigures the board mode at runtime.
        Pass human_vs_ai=True to play against the AI, or False for a human vs human game.
        """
        if human_vs_ai:
            self.mode = "human_vs_ai"
            self.human_player = human_player
        else:
            self.mode = "human"
            self.human_player = None

    def is_ai_turn(self):
        #Returns True if the AI should be moving in the current game state
        if self.mode == "ai_vs_ai":
            return True
        if self.mode in ("human_vs_ai", "ai"):
            return self.current_player != self.human_player
        return False

    def start_game(self):
        self.reset_game()

        #Kick off the first AI turn if applicable
        if self.is_ai_turn():
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

    def reset_game(self):
        #Rebuilds game state and resets all tracking variables to their initial values
        self.game_state = GameState(side=self.side)
        self.current_player = 1
        self.game_over = False
        self.has_moved_this_turn = False
        self.winning_line = []

        #Reset signal catcher
        if hasattr(self.board_graphics, "reset"):
            self.board_graphics.reset()

        #Update
        self.moveMade.emit()

    def start_ai_turn(self):
        if self.game_over:
            return
        if not self.is_ai_turn():
            return

        #Avoid launching a second worker if one is already running
        if self.ai_worker and self.ai_worker.isRunning():
            return

        #Param passing into AIWorker
        gameStateCopy = deepcopy(self.game_state)
        self.ai_worker = AIWorker(
            gameStateCopy,
            self.current_player,
            max_depth=self.depth,
            beam_width=self.beamwidth,
            ai="Susan"
        )
        #Communicator
        self.ai_worker.moveReady.connect(self.on_ai_move_ready)
        self.ai_worker.start()

    def on_ai_move_ready(self, move):
        #Receives the move chosen by the AI worker thread and applies it to the live game state
        if self.game_over or move is None:
            return

        #Dispatch movement vs placement and log the result
        if isinstance(move, tuple) and len(move) == 2 and isinstance(move[0], tuple):
            fromPos, toPos = move
            success = self.game_state.make_move(toPos, self.current_player, from_pos=fromPos)
            moveDesc = f"AI Player {self.current_player} moved piece from {fromPos} to {toPos}"
        else:
            toPos = move
            success = self.game_state.make_move(toPos, self.current_player)
            moveDesc = f"AI Player {self.current_player} placed piece at {toPos}"

        if not success:
            self._send_message(f"Illegal AI move attempted by Player {self.current_player}: {move}")
            return

        self._send_message(moveDesc)
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
        if self.is_ai_turn():
            QTimer.singleShot(self.ai_move_delay, self.start_ai_turn)

    def make_human_move(self, move, from_pos=None):
        #Reject input if the game is over or it is not this human's turn
        if self.game_over:
            return False
        if self.is_ai_turn():
            return False

        currentPlayer = self.current_player
        success = self.game_state.make_move(move, currentPlayer, from_pos=from_pos)

        if not success:
            #Notify listeners that an illegal move was attempted
            self.illegalMove.emit()
            self._send_message(f"Illegal move attempted by Player {currentPlayer}: {move}")
            return False

        #Logger for valid move
        action = f"placed at {move}" if from_pos is None else f"moved from {from_pos} to {move}"
        self._send_message(f"Player {currentPlayer} {action}")

        self.moveMade.emit()  #Update
        self.current_player = 3 - currentPlayer

        #Terminal move checker
        if self.game_state.is_terminal():
            self.game_over = True
            self.gameOver.emit()
            self._emit_game_result()
            self._send_message("Game over")

            if not self.wait_for_message:
                QTimer.singleShot(1000, self.start_game)
            return True

        #Start AI turn if applicable
        if self.is_ai_turn():
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