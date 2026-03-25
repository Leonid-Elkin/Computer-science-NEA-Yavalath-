import math


class GameState:
    DIRECTIONS = [
        (1, 0), (0, 1), (-1, 1),
        (-1, 0), (0, -1), (1, -1)
    ]

    def __init__(self, side=5):
        self.side = side
        self.board = {}
        self.move_history = []

        #Populate all valid axial coordinates for a hexagonal board of the given side length
        for q in range(-side + 1, side):
            for r in range(-side + 1, side):
                if -side + 1 <= -q - r <= side - 1:
                    self.board[(q, r)] = 0

    def get_valid_moves(self):
        #Returns all empty cells as legal placement targets
        return [pos for pos, val in self.board.items() if val == 0]

    def make_move(self, pos, player):
        #Places the player's piece and records the move; returns False if the cell is occupied or invalid
        if pos in self.board and self.board[pos] == 0:
            self.board[pos] = player
            self.move_history.append(pos)
            return True
        return False

    def undo_move(self, pos):
        #Clears the cell and removes it from history, used by the minimax search to backtrack
        if pos in self.move_history:
            self.board[pos] = 0
            self.move_history.remove(pos)

    def is_terminal(self):
        """
        Checks whether the game has reached an end state.
        A game ends when the last player forms four in a row (win),
        three in a row (self-loss), or the board is completely full (draw).
        """
        #Anti-crash guard for empty history
        if not self.move_history:
            return False

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]

        #Four in a row is a win - three in a row is a self-loss - both end the game
        if self._has_consecutive(lastPos, lastPlayer, 4):
            return True
        if self._has_consecutive(lastPos, lastPlayer, 3):
            return True

        #Board full with no decisive line is a draw
        if all(val != 0 for val in self.board.values()):
            return True

        return False

    def _has_consecutive(self, pos, player, length):
        """
        Checks whether the given player has a run of at least `length` pieces
        passing through `pos` in any of the six axial directions.
        Counts outward from pos in both the positive and negative direction along each axis.
        """
        q, r = pos
        for dq, dr in self.DIRECTIONS:
            count = 1

            #Extend forward along the direction
            for i in range(1, length):
                if self.board.get((q + dq * i, r + dr * i)) == player:
                    count += 1
                else:
                    break

            #Extend backward along the direction
            for i in range(1, length):
                if self.board.get((q - dq * i, r - dr * i)) == player:
                    count += 1
                else:
                    break

            if count >= length:
                return True

        return False

    def evaluate(self, player):
        """
        Heuristic board evaluation from `player`s perspective.
        Returns a large terminal score for decisive positions, otherwise
        weights potential line counts for both players to estimate positional strength.
        """
        opponent = 3 - player

        #Return a large terminal score immediately to short-circuit further evaluation
        if self.is_terminal():
            lastPos = self.move_history[-1]
            lastPlayer = self.board[lastPos]

            if self._has_consecutive(lastPos, lastPlayer, 4):
                return 10000 if lastPlayer == player else -10000
            if self._has_consecutive(lastPos, lastPlayer, 3):
                return -10000 if lastPlayer == player else 10000

        playerFour   = self._count_potential_lines(player, 4)
        playerThree  = self._count_potential_lines(player, 3)
        playerTwo    = self._count_potential_lines(player, 2)
        opponentFour  = self._count_potential_lines(opponent, 4)
        opponentThree = self._count_potential_lines(opponent, 3)
        opponentTwo   = self._count_potential_lines(opponent, 2)

        #Opponent three-in-a-row lines are weighted higher than our own to prioritise defence
        return (
              1000 * playerFour   + 100 * playerThree   + 10 * playerTwo
            - 1000 * opponentFour - 150 * opponentThree - 20 * opponentTwo
        )

    def _count_potential_lines(self, player, length):
        """
        Counts unblocked lines of exactly `length` cells containing only this player's
        pieces or empty cells. Only three of the six directions are iterated to avoid
        counting each line twice. Already-counted starting positions are tracked in a set.
        """
        count = 0
        checked = set()

        for pos in self.board:
            if self.board[pos] != 0 and self.board[pos] != player:
                continue

            for dq, dr in self.DIRECTIONS[:3]:
                if (pos, (dq, dr)) in checked:
                    continue

                line = []
                blocked = False

                for i in range(length):
                    checkPos = (pos[0] + dq * i, pos[1] + dr * i)
                    val = self.board.get(checkPos, -1)
                    if val == -1 or (val != 0 and val != player):
                        blocked = True
                        break
                    line.append(checkPos)

                if not blocked and len(line) == length:
                    count += 1
                    for p in line:
                        checked.add((p, (dq, dr)))

        return count

    def get_winner(self):
        """
        Returns the winning player id (1 or 2), 0 for a draw,
        or None if the game is still in progress.
        Three in a row is a self-loss, so the winner is the other player in that case.
        """
        if not self.move_history:
            return None

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]

        if self._has_consecutive(lastPos, lastPlayer, 4):
            return lastPlayer

        #Three in a row is a self-loss, so the other player wins
        if self._has_consecutive(lastPos, lastPlayer, 3):
            return 3 - lastPlayer

        if all(val != 0 for val in self.board.values()):
            return 0

        return None

    def get_winning_line(self):
        """
        Traces back along each direction from the last move to find and return
        the exact sequence of cells that forms the decisive run.
        Checks four-in-a-row first (win condition), then three-in-a-row (loss condition).
        Returns an empty list if no winning line is found.
        """
        if not self.move_history:
            return []

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]
        q, r = lastPos

        #Check four-in-a-row first (win), then three-in-a-row (loss)
        for length in [4, 3]:
            for dq, dr in self.DIRECTIONS:
                line = [lastPos]

                for i in range(1, length):
                    pos = (q + dq * i, r + dr * i)
                    if self.board.get(pos) == lastPlayer:
                        line.append(pos)
                    else:
                        break

                for i in range(1, length):
                    pos = (q - dq * i, r - dr * i)
                    if self.board.get(pos) == lastPlayer:
                        line.insert(0, pos)
                    else:
                        break

                if len(line) >= length:
                    return line[:length]

        return []