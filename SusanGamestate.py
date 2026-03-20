import math

class GameState:
    # Class-level directions for axial hex grid
    DIRECTIONS = [
        (1, 0), (0, 1), (-1, 1),
        (-1, 0), (0, -1), (1, -1)
    ]

    def __init__(self, side=5):
        self.side = side
        self.board = {}  # {(q, r): player_id}, 0 means empty
        self.move_history = []
        self.last_move_captured_players = []  # list of players who lost pieces
        self.winner = None  # Track the winner once determined

        # Initialize hexagonal board coordinates
        for q in range(-side + 1, side):
            for r in range(-side + 1, side):
                if -q - r >= -side + 1 and -q - r <= side - 1:
                    self.board[(q, r)] = 0

    def get_valid_moves(self):
        return [pos for pos, val in self.board.items() if val == 0]

    def is_adjacent(self, pos1, pos2):
        dq = pos2[0] - pos1[0]
        dr = pos2[1] - pos1[1]
        return (dq, dr) in self.DIRECTIONS

    def make_move(self, pos, player, from_pos=None):
        """
        If from_pos is None: place a new piece at pos.
        Else: move piece from from_pos to pos (adjacent).
        Returns True if move was successful, False if illegal.
        """
        # Check valid positions
        if pos not in self.board:
            return False

        if from_pos is None:
            # Place a new piece
            if self.board[pos] != 0:
                return False
        else:
            # Move existing piece
            if from_pos not in self.board:
                return False
            if self.board[from_pos] != player:
                return False
            if self.board[pos] != 0:
                return False
            if not self.is_adjacent(from_pos, pos):
                return False

        # Backup state
        original_board = self.board.copy()
        original_history = self.move_history.copy()

        if from_pos is None:
            # Place new piece
            self.board[pos] = player
            self.move_history.append(pos)
        else:
            # Move piece
            self.board[from_pos] = 0
            self.board[pos] = player
            # Update move history: remove old pos, add new pos
            if from_pos in self.move_history:
                self.move_history.remove(from_pos)
            self.move_history.append(pos)

        # Track pieces before removal
        pieces_before = {1: 0, 2: 0}
        for p, v in self.board.items():
            if v in [1, 2]:
                pieces_before[v] += 1

        # Remove surrounded hexagons
        self.remove_surrounded_hexagons()

        # Track pieces after removal
        pieces_after = {1: 0, 2: 0}
        for p, v in self.board.items():
            if v in [1, 2]:
                pieces_after[v] += 1

        # Self-capture check: the piece moved/placed must still belong to player
        if self.board.get(pos, 0) != player:
            # Illegal move – undo
            self.board = original_board
            self.move_history = original_history
            self.last_move_captured_players = []
            return False

        # Determine who lost pieces
        self.last_move_captured_players = []
        for player_id in [1, 2]:
            if pieces_after[player_id] < pieces_before[player_id]:
                self.last_move_captured_players.append(player_id)

        # Check for winner: if opponent lost pieces but current player didn't
        opponent = 3 - player
        if opponent in self.last_move_captured_players and player not in self.last_move_captured_players:
            self.winner = player
        elif player in self.last_move_captured_players and opponent not in self.last_move_captured_players:
            # Current player got surrounded - they lose
            self.winner = opponent

        return True

    def _is_fully_surrounded(self, pos):
        for dq, dr in self.DIRECTIONS:
            neighbor = (pos[0] + dq, pos[1] + dr)
            if self.board.get(neighbor, 0) == 0:
                return False
        return True

    def remove_surrounded_hexagons(self):
        """Remove all pieces that are completely surrounded"""
        to_remove = []

        def neighbors(pos):
            q, r = pos
            return [(q + dq, r + dr) for dq, dr in self.DIRECTIONS]

        for pos, val in self.board.items():
            if val == 0:
                continue
            # Check if all neighbors are non-empty
            if all(self.board.get(n, 0) != 0 for n in neighbors(pos)):
                to_remove.append(pos)

        for pos in to_remove:
            self.board[pos] = 0
            if pos in self.move_history:
                self.move_history.remove(pos)

    def undo_move(self, pos):
        if pos in self.move_history:
            self.board[pos] = 0
            self.move_history.remove(pos)
            
    def is_terminal(self, last_player=None):
        """
        The game is terminal if:
        - A winner has been determined (someone got surrounded)
        - The board is completely full
        """
        if self.winner is not None:
            return True
        
        # Check if board is full
        if all(val != 0 for val in self.board.values()):
            return True
            
        return False

    def get_winner(self, last_player=None):
        """
        Returns:
        - 1 if player 1 won
        - 2 if player 2 won  
        - 0 if draw (board full, no one surrounded)
        - None if game not over
        """
        # If winner already determined
        if self.winner is not None:
            return self.winner

        # Check if board is full (draw condition)
        if all(val != 0 for val in self.board.values()):
            return 0  # draw

        return None

    def get_winning_line(self):
        """Susan doesn't have winning lines like Yavalath, return empty"""
        return []