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

        #Populate all valid axial coordinates for a hexagonal board of the given side length
        for q in range(-side + 1, side):
            for r in range(-side + 1, side):
                if -q - r >= -side + 1 and -q - r <= side - 1:
                    self.board[(q, r)] = 0

    def get_valid_moves(self):
        #Returns all empty cells as legal placement targets
        return [pos for pos, val in self.board.items() if val == 0]

    def make_move(self, pos, player):
        """
        Places the player's piece at pos, then checks for any newly surrounded groups
        and removes them. Returns a list of captured positions, or an empty list if the
        cell was already occupied or the position is invalid.
        """
        if pos in self.board and self.board[pos] == 0:
            self.board[pos] = player
            self.move_history.append(pos)

            #Snapshot the board before captures are applied
            preBoard = dict(self.board)

            self.remove_surrounded_hexagons()

            #Captured = positions that were non-empty before but are now cleared
            captured = [
                p for p in preBoard
                if preBoard[p] != 0 and self.board.get(p, 0) == 0 and p != pos
            ]

            return captured
        return []

    def remove_surrounded_hexagons(self):
        """
        Flood-fills each connected group of same-coloured pieces to determine whether
        the group has any adjacent empty cell (a liberty). Any group with no liberties
        is fully surrounded and all its members are removed from the board.
        Cells on the boundary of the hex grid (outside the board dict) are ignored
        rather than treated as liberties, so edge pieces can be captured.
        """
        visited = set()
        groupsToRemove = []

        def neighbors(pos):
            q, r = pos
            return [(q + dq, r + dr) for dq, dr in self.DIRECTIONS]

        for pos, val in self.board.items():
            if val == 0 or pos in visited:
                continue

            groupColor = val
            group = set()
            stack = [pos]
            surrounded = True

            #BFS to collect the full connected group and check for liberties
            while stack:
                current = stack.pop()
                if current in group:
                    continue
                group.add(current)
                visited.add(current)

                for n in neighbors(current):
                    nVal = self.board.get(n, None)
                    if nVal == 0:
                        #Adjacent empty hex - group is not surrounded
                        surrounded = False
                    elif nVal == groupColor and n not in group:
                        stack.append(n)
                    #None means outside the board - not treated as a liberty

            if surrounded:
                groupsToRemove.append(group)

        #Clear all surrounded groups from the board
        for group in groupsToRemove:
            for pos in group:
                self.board[pos] = 0
                if pos in self.move_history:
                    self.move_history.remove(pos)

    def undo_move(self, pos):
        #Clears the cell and removes it from history, used by the minimax search to backtrack
        if pos in self.move_history:
            self.board[pos] = 0
            self.move_history.remove(pos)

    def is_terminal(self):
        """
        Checks whether the game has reached an end state.
        A game ends when the last player forms five in a row (win),
        or the board is completely full (draw).
        """
        #Anti-crash guard for empty history
        if not self.move_history:
            return False

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]

        #Win: five in a row (Pentalath rule)
        if self._has_consecutive(lastPos, lastPlayer, 5):
            return True

        #Draw: no empty cells remain
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
                checkPos = (q + dq * i, r + dr * i)
                if self.board.get(checkPos) == player:
                    count += 1
                else:
                    break

            #Extend backward along the direction
            for i in range(1, length):
                checkPos = (q - dq * i, r - dr * i)
                if self.board.get(checkPos) == player:
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

        #Weighting the counts to produce a heuristic score
        return (
            1000 * playerFour + 100 * playerThree + 10 * playerTwo
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
                #Avoid double counting lines by tracking starting points and directions
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
                    #Mark all positions in this line to avoid double counting in this direction
                    for p in line:
                        checked.add((p, (dq, dr)))

        return count

    def get_winner(self):
        """
        Returns the winning player id (1 or 2), 0 for a draw,
        or None if the game is still in progress.
        """
        if not self.move_history:
            return None

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]

        #Five in a row is a win
        if self._has_consecutive(lastPos, lastPlayer, 5):
            return lastPlayer

        #Board full with no decisive line is a draw
        if all(val != 0 for val in self.board.values()):
            return 0

        return None

    def get_winning_line(self):
        """
        Traces back along each direction from the last move to find and return
        the exact sequence of five cells that forms the decisive run.
        Returns an empty list if no winning line is found.
        """
        if not self.move_history:
            return []

        lastPos = self.move_history[-1]
        lastPlayer = self.board[lastPos]
        q, r = lastPos

        #Pentalath winning length is five
        length = 5

        for dq, dr in self.DIRECTIONS:
            line = [lastPos]

            #Extend forward
            for i in range(1, length):
                pos = (q + dq * i, r + dr * i)
                if self.board.get(pos) == lastPlayer:
                    line.append(pos)
                else:
                    break

            #Extend backward
            for i in range(1, length):
                pos = (q - dq * i, r - dr * i)
                if self.board.get(pos) == lastPlayer:
                    line.insert(0, pos)
                else:
                    break

            if len(line) >= length:
                return line[:length]

        return []