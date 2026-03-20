# AI/GameState.py
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

        # Initialize hexagonal board coordinates
        for q in range(-side + 1, side):
            for r in range(-side + 1, side):
                if -q - r >= -side + 1 and -q - r <= side - 1:
                    self.board[(q, r)] = 0

    def get_valid_moves(self):
        return [pos for pos, val in self.board.items() if val == 0]

    def make_move(self, pos, player):
        if pos in self.board and self.board[pos] == 0:
            self.board[pos] = player
            self.move_history.append(pos)
            return True
        return False

    def undo_move(self, pos):
        if pos in self.move_history:
            self.board[pos] = 0
            self.move_history.remove(pos)

    def is_terminal(self):
        if not self.move_history:
            return False

        last_pos = self.move_history[-1]
        last_player = self.board[last_pos]

        # Win: 4 in a row
        if self._has_consecutive(last_pos, last_player, 4):
            return True

        # Loss: 3 in a row (for last player)
        if self._has_consecutive(last_pos, last_player, 3):
            return True

        # Draw: no empty cells
        if all(val != 0 for val in self.board.values()):
            return True

        return False

    def _has_consecutive(self, pos, player, length):
        q, r = pos
        for dq, dr in self.DIRECTIONS:
            count = 1
            # Forward direction
            for i in range(1, length):
                check_pos = (q + dq * i, r + dr * i)
                if self.board.get(check_pos) == player:
                    count += 1
                else:
                    break
            # Backward direction
            for i in range(1, length):
                check_pos = (q - dq * i, r - dr * i)
                if self.board.get(check_pos) == player:
                    count += 1
                else:
                    break
            if count >= length:
                return True
        return False

    def evaluate(self, player):
        opponent = 1 if player == 2 else 2

        # Terminal states high priority:
        if self.is_terminal():
            last_pos = self.move_history[-1]
            last_player = self.board[last_pos]

            if self._has_consecutive(last_pos, last_player, 4):
                return 10000 if last_player == player else -10000

            if self._has_consecutive(last_pos, last_player, 3):
                return -10000 if last_player == player else 10000

        # Evaluate potential lines with different weights:
        player_four = self._count_potential_lines(player, 4)
        player_three = self._count_potential_lines(player, 3)
        player_two = self._count_potential_lines(player, 2)

        opponent_four = self._count_potential_lines(opponent, 4)
        opponent_three = self._count_potential_lines(opponent, 3)
        opponent_two = self._count_potential_lines(opponent, 2)

        # Weighting the counts to get heuristic score
        score = (
            1000 * player_four + 100 * player_three + 10 * player_two
            - 1000 * opponent_four - 150 * opponent_three - 20 * opponent_two
        )

        return score

    def _count_potential_lines(self, player, length):
        count = 0
        # Only need 3 directions since opposite directions are checked by moving backward
        checked = set()
        for pos in self.board:
            if self.board[pos] != 0 and self.board[pos] != player:
                continue

            for dq, dr in self.DIRECTIONS[:3]:
                # Avoid double counting lines by tracking starting points and directions
                if (pos, (dq, dr)) in checked:
                    continue

                line = []
                blocked = False
                for i in range(length):
                    check_pos = (pos[0] + dq * i, pos[1] + dr * i)
                    val = self.board.get(check_pos, -1)
                    if val == -1 or (val != 0 and val != player):
                        blocked = True
                        break
                    line.append(check_pos)

                if not blocked and len(line) == length:
                    count += 1
                    # Mark all positions in this line to avoid double counting in this direction
                    for p in line:
                        checked.add((p, (dq, dr)))
        return count

    def get_winner(self):
        if not self.move_history:
            return None  # Game just started
        
        last_pos = self.move_history[-1]
        last_player = self.board[last_pos]

        # Check if last player has 4 in a row => win
        if self._has_consecutive(last_pos, last_player, 4):
            return last_player

        # Check if last player has 3 in a row => loss (so other player wins)
        if self._has_consecutive(last_pos, last_player, 3):
            return 3 - last_player  # The other player

        # Check draw: no empty spots
        if all(val != 0 for val in self.board.values()):
            return 0  # Draw
        
        return None  # Game ongoing

    # In GameState.py

    def get_winning_line(self):
        if not self.move_history:
            return []

        last_pos = self.move_history[-1]
        last_player = self.board[last_pos]
        q, r = last_pos

        # Check both 4-in-a-row (win) and 3-in-a-row (loss)
        for length in [4, 3]:
            for dq, dr in self.DIRECTIONS:
                line = [last_pos]

                # Forward direction
                for i in range(1, length):
                    pos = (q + dq * i, r + dr * i)
                    if self.board.get(pos) == last_player:
                        line.append(pos)
                    else:
                        break

                # Backward direction
                for i in range(1, length):
                    pos = (q - dq * i, r - dr * i)
                    if self.board.get(pos) == last_player:
                        line.insert(0, pos)
                    else:
                        break

                if len(line) >= length:
                    print(line[:length])
                    return line[:length]

        return []


