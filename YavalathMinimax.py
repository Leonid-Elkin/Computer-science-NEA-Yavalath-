import math
import random
from ElkUtils.HexagonUtils import (
    hex_distance,
    find_opponent_gap_fours,
    creates_three_in_a_row,
    DIRECTIONS,
    count_open_sequences
)


class MinimaxPlayer:
    def __init__(self, player_id, max_depth=8, beam_width=20):
        self.player_id = player_id
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.transposition_table = {}
        self._sequence_cache = {}
        self._process = None
        self._parent_conn = None
        self.best_move = None

    # --- Process management ---

    def start_search(self, game_state):
        #Launches the minimax search in a separate process to avoid blocking the UI
        if self._process and self._process.is_alive():
            return

        self.transposition_table.clear()
        self._sequence_cache.clear()

    def _run_minimax(self, game_state, conn):
        #Entry point for the worker process - sends the chosen move back through the pipe
        move = self.make_move(game_state)
        conn.send(move)
        conn.close()

    def get_best_move(self):
        #Old pipe remnant
        return self.best_move

    # MOVE SELECTION

    def make_move(self, game_state):
        """
        Three-phase move selection:
          Phase 1 - empty board: pick randomly from the cells closest to the centre.
          Phase 2 - forced block: immediately respond to any gap-four threat.
          Phase 3 - search: no forcing move available, run full alpha-beta.
        """
        #Phase 1: on an empty board pick randomly from the three closest cells to centre
        if self._board_is_empty(game_state):
            return self._opening_move(game_state)

        #Phase 2: block any gap-four threat the opponent already has
        forcedMove = self._find_forced_block(game_state)
        if forcedMove is not None:
            return forcedMove

        #Phase 3: no forced response available, run the full alpha-beta search
        return self._search(game_state)

    def _board_is_empty(self, game_state):
        #Returns True if no pieces have been placed yet
        return all(val == 0 for val in game_state.board.values())

    def _opening_move(self, game_state):
        """
        Scores each cell by distance to centre, adds a small random jitter to
        avoid deterministic openings, then picks randomly from the top three candidates.
        """
        validMoves = game_state.get_valid_moves()
        if not validMoves:
            return None

        center = (0, 0)
        scored = [
            (-hex_distance(move, center) + random.uniform(-0.5, 0.5), move)
            for move in validMoves
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return random.choice([m[1] for m in scored[:3]])

    def _find_forced_block(self, game_state):
        """
        Searches for any opponent gap-four threat that must be blocked immediately.
        A candidate block is skipped if filling it would create a three-in-a-row
        self-loss for this player.
        """
        opponent = 3 - self.player_id
        gapThreats = find_opponent_gap_fours(game_state.board, opponent)

        for gapPos, _line in gapThreats:
            if not creates_three_in_a_row(game_state.board, gapPos, self.player_id):
                return gapPos

        return None

    def _search(self, game_state):
        """
        Iterates all top-level moves, runs a full minimax subtree for each,
        and returns the move with the highest score.
        Alpha-beta pruning is seeded from the root level.
        """
        bestScore = -math.inf
        bestMove = None
        alpha = -math.inf
        beta = math.inf

        for move in self.get_ordered_moves(game_state):
            game_state.make_move(move, self.player_id)
            score = self.min_value(game_state, depth=1, alpha=alpha, beta=beta)
            game_state.undo_move(move)

            if score > bestScore:
                bestScore = score
                bestMove = move

            alpha = max(alpha, bestScore)

        return bestMove

    # ALPHA BETA PRUNING

    def max_value(self, game_state, depth, alpha, beta):
        """
        Maximising node - self.player_id moves here.
        Looks up the current state in the transposition table before expanding;
        stores the result on the way back up.
        """
        stateHash = self.hash_state(game_state)
        if stateHash in self.transposition_table:
            return self.transposition_table[stateHash]

        if game_state.is_terminal() or depth >= self.max_depth:
            val = self.evaluate(game_state)
            self.transposition_table[stateHash] = val
            return val

        value = -math.inf
        for move in self.get_ordered_moves(game_state, depth):
            game_state.make_move(move, self.player_id)
            value = max(value, self.min_value(game_state, depth + 1, alpha, beta))
            game_state.undo_move(move)

            #Beta cut-off: opponent has path that avoids this score
            if value >= beta:
                self.transposition_table[stateHash] = value
                return value

            alpha = max(alpha, value)

        self.transposition_table[stateHash] = value
        return value

    def min_value(self, game_state, depth, alpha, beta):
        """
        Minimising node - the opponent moves here.
        Mirrors max_value but searches from the opponent's perspective.
        """
        stateHash = self.hash_state(game_state)
        if stateHash in self.transposition_table:
            return self.transposition_table[stateHash]

        if game_state.is_terminal() or depth >= self.max_depth:
            val = self.evaluate(game_state)
            self.transposition_table[stateHash] = val
            return val

        value = math.inf
        opponentId = 3 - self.player_id

        for move in self.get_ordered_moves(game_state, depth):
            game_state.make_move(move, opponentId)
            value = min(value, self.max_value(game_state, depth + 1, alpha, beta))
            game_state.undo_move(move)

            #Alpha cut-off: already a better path to this
            if value <= alpha:
                self.transposition_table[stateHash] = value
                return value

            beta = min(beta, value)

        self.transposition_table[stateHash] = value
        return value

    # MOVE ORDER

    def get_ordered_moves(self, game_state, depth=0):
        """
        Returns all valid moves sorted by estimated quality.
        Gap-four blocks are scored highest, then three-in-a-row blocks,
        then general positional moves weighted by centre proximity and sequence counts.
        At depth > 1 the list is pruned to beam_width to limit the search tree.
        """
        validMoves = game_state.get_valid_moves()
        if not validMoves:
            return []

        center = (0, 0)
        opponent = 3 - self.player_id
        seq = self.get_sequences(game_state)
        gapThreats = find_opponent_gap_fours(game_state.board, opponent)

        gapBlockMoves = set()
        scoredMoves = []

        #Gap-four blocks are scored highest to ensure they are always searched first
        for gapPos, _line in gapThreats:
            if gapPos in validMoves:
                if not creates_three_in_a_row(game_state.board, gapPos, self.player_id):
                    scoredMoves.append((30000, gapPos))
                    gapBlockMoves.add(gapPos)

        for move in validMoves:
            if move in gapBlockMoves:
                continue

            distScore = -hex_distance(move, center)

            #Three-in-a-row blocks rank below gap-four blocks but above general play
            if self.blocks_opponent_three(game_state, move, opponent):
                scoredMoves.append((10000 + distScore * 10, move))
            else:
                score = distScore + seq["player_threes"] * 50 - seq["opponent_threes"] * 70
                scoredMoves.append((score, move))

        scoredMoves.sort(key=lambda x: x[0], reverse=True)

        #Prune to beam width at deeper levels to limit branching
        if depth > 1:
            scoredMoves = scoredMoves[:self.beam_width]

        return [m[1] for m in scoredMoves]

    def blocks_opponent_three(self, game_state, move, opponent):
        """
        Returns True if placing at `move` would block the opponent from completing
        a three-in-a-row. Checks all three window positions that include the candidate
        cell along each axis:
          [prev2, prev1, MOVE]  - move extends a run of two behind it
          [prev1, MOVE,  next1] - move fills the gap between two opponent pieces
          [MOVE,  next1, next2] - move extends a run of two ahead of it
        """
        board = game_state.board
        for dq, dr in DIRECTIONS:
            q, r = move

            prev1 = (q - dq,     r - dr)
            prev2 = (q - 2 * dq, r - 2 * dr)
            next1 = (q + dq,     r + dr)
            next2 = (q + 2 * dq, r + 2 * dr)

            endOfRun    = board.get(prev1, 0) == opponent and board.get(prev2, 0) == opponent
            middleOfRun = board.get(prev1, 0) == opponent and board.get(next1, 0) == opponent
            startOfRun  = board.get(next1, 0) == opponent and board.get(next2, 0) == opponent

            if endOfRun or middleOfRun or startOfRun:
                return True

        return False

    # EVALUATION FUNCTION

    def get_sequences(self, game_state):
        """
        Returns open-sequence counts for both players, cached by board state hash
        to avoid recomputing the same position multiple times during a search.
        """
        stateHash = self.hash_state(game_state)
        if stateHash in self._sequence_cache:
            return self._sequence_cache[stateHash]

        player = self.player_id
        opponent = 3 - player

        result = {
            "player_fours":    count_open_sequences(game_state.board, player,   4),
            "player_threes":   count_open_sequences(game_state.board, player,   3),
            "opponent_fours":  count_open_sequences(game_state.board, opponent, 4),
            "opponent_threes": count_open_sequences(game_state.board, opponent, 3),
        }

        self._sequence_cache[stateHash] = result
        return result

    def evaluate(self, game_state):
        """
        Scores the board from self.player_id's perspective.
        Terminal positions return a fixed large value.
        Non-terminal positions are scored using sequence counts and
        centre proximity, with player_threes penalised because forming
        three-in-a-row is a self-loss in Yavalath.
        """
        seq = self.get_sequences(game_state)

        if game_state.is_terminal():
            if not game_state.move_history:
                return 0

            lastPos = game_state.move_history[-1]
            lastPlayer = game_state.board[lastPos]

            if game_state._has_consecutive(lastPos, lastPlayer, 4):
                return 100000 if lastPlayer == self.player_id else -100000

            #Three-in-a-row is a self-loss in Yavalath, so the winner is the other player
            if game_state._has_consecutive(lastPos, lastPlayer, 3):
                return -100000 if lastPlayer == self.player_id else 100000

            #Board full with no decisive line - draw
            return 0

        score = 0

        #player_threes are penalised because three-in-a-row is a self-loss in Yavalath
        #opponent_threes are rewarded because they risk the opponent losing
        score += seq["player_fours"]    * 10000
        score -= seq["opponent_fours"]  * 12000
        score -= seq["player_threes"]   *  8000
        score += seq["opponent_threes"] *  7000

        #Reward proximity to centre; opponent centre proximity is penalised slightly more
        center = (0, 0)
        playerDists   = [hex_distance(pos, center) for pos, val in game_state.board.items() if val == self.player_id]
        opponentDists = [hex_distance(pos, center) for pos, val in game_state.board.items() if val == 3 - self.player_id]

        if playerDists:
            score += 200 / (1 + min(playerDists))
        if opponentDists:
            score -= 250 / (1 + min(opponentDists))

        return score

    def hash_state(self, game_state):
        #Produces a hashable key from the current board for transposition table lookups
        return hash(frozenset(game_state.board.items()))