import math


class GameState:
    #Class-level directions for axial hex grid
    DIRECTIONS = [
        (1, 0), (0, 1), (-1, 1),
        (-1, 0), (0, -1), (1, -1)
    ]

    def __init__(self, side=5):
        self.side = side
        self.board = {}
        self.move_history = []
        self.last_move_captured_players = []
        self.winner = None

        #Populate all valid axial coordinates for a hexagonal board of the given side length
        for q in range(-side + 1, side):
            for r in range(-side + 1, side):
                if -q - r >= -side + 1 and -q - r <= side - 1:
                    self.board[(q, r)] = 0

    def get_valid_moves(self):
        #Returns all empty cells as legal placement targets
        return [pos for pos, val in self.board.items() if val == 0]

    def is_adjacent(self, pos1, pos2):
        #Returns True if pos2 is exactly one step from pos1 in any axial direction
        dq = pos2[0] - pos1[0]
        dr = pos2[1] - pos1[1]
        return (dq, dr) in self.DIRECTIONS

    def make_move(self, pos, player, from_pos=None):
        """
        Applies either a placement (from_pos is None) or a movement (from_pos provided).
        After placing the piece, surrounded groups are removed. If the placed piece itself
        is immediately captured (self-capture), the move is rolled back and False is returned.
        Updates last_move_captured_players and self.winner based on which player lost pieces.
        Returns True on success, False if the move is illegal.
        """
        #Validate target position
        if pos not in self.board:
            return False

        if from_pos is None:
            #Placement: target cell must be empty
            if self.board[pos] != 0:
                return False
        else:
            #Movement: source must contain this player's piece, target must be empty and adjacent
            if from_pos not in self.board:
                return False
            if self.board[from_pos] != player:
                return False
            if self.board[pos] != 0:
                return False
            if not self.is_adjacent(from_pos, pos):
                return False

        #Backup state in case the move needs to be rolled back
        originalBoard   = self.board.copy()
        originalHistory = self.move_history.copy()

        if from_pos is None:
            #Place new piece
            self.board[pos] = player
            self.move_history.append(pos)
        else:
            #Move existing piece: clear source, occupy target, update history
            self.board[from_pos] = 0
            self.board[pos] = player
            if from_pos in self.move_history:
                self.move_history.remove(from_pos)
            self.move_history.append(pos)

        #Count pieces before and after capture resolution
        piecesBefore = {1: 0, 2: 0}
        for p, v in self.board.items():
            if v in [1, 2]:
                piecesBefore[v] += 1

        self.remove_surrounded_hexagons()

        piecesAfter = {1: 0, 2: 0}
        for p, v in self.board.items():
            if v in [1, 2]:
                piecesAfter[v] += 1

        #Self-capture check: if the placed piece was immediately surrounded, roll back
        if self.board.get(pos, 0) != player:
            self.board = originalBoard
            self.move_history = originalHistory
            self.last_move_captured_players = []
            return False

        #Record which players lost pieces this turn
        self.last_move_captured_players = []
        for playerId in [1, 2]:
            if piecesAfter[playerId] < piecesBefore[playerId]:
                self.last_move_captured_players.append(playerId)

        #Determine winner: opponent captured but current player not, or vice versa
        opponent = 3 - player
        if opponent in self.last_move_captured_players and player not in self.last_move_captured_players:
            self.winner = player
        elif player in self.last_move_captured_players and opponent not in self.last_move_captured_players:
            self.winner = opponent

        return True

    def _is_fully_surrounded(self, pos):
        #Returns True if every neighbour of pos is occupied (no empty liberties)
        for dq, dr in self.DIRECTIONS:
            neighbor = (pos[0] + dq, pos[1] + dr)
            if self.board.get(neighbor, 0) == 0:
                return False
        return True

    def remove_surrounded_hexagons(self):
        """
        Scans all occupied cells and removes any piece that has no adjacent empty cell.
        Unlike the flood-fill variant used in Pentalath, Susan checks each piece
        individually rather than by connected group, matching its simpler capture rule.
        """
        toRemove = []

        def neighbors(pos):
            q, r = pos
            return [(q + dq, r + dr) for dq, dr in self.DIRECTIONS]

        #Collect all pieces with no empty neighbour
        for pos, val in self.board.items():
            if val == 0:
                continue
            if all(self.board.get(n, 0) != 0 for n in neighbors(pos)):
                toRemove.append(pos)

        #Clear captured pieces and remove them from history
        for pos in toRemove:
            self.board[pos] = 0
            if pos in self.move_history:
                self.move_history.remove(pos)

    def undo_move(self, pos):
        #Clears the cell and removes it from history, used by the minimax search to backtrack
        if pos in self.move_history:
            self.board[pos] = 0
            self.move_history.remove(pos)

    def is_terminal(self, last_player=None):
        """
        The game is terminal if a winner has been determined (a player was surrounded)
        or the board is completely full (draw).
        """
        if self.winner is not None:
            return True

        #Full board with no captures decided yet is a draw
        if all(val != 0 for val in self.board.values()):
            return True

        return False

    def get_winner(self, last_player=None):
        """
        Returns 1 or 2 if that player has won, 0 for a draw (board full, no capture),
        or None if the game is still in progress.
        """
        #Winner already recorded from a capture event
        if self.winner is not None:
            return self.winner

        #Board full with no decisive capture is a draw
        if all(val != 0 for val in self.board.values()):
            return 0

        return None

    def get_winning_line(self):
        #Susan has no line-based win condition; return empty
        return []