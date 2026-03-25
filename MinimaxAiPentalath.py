import math
import random
from ElkUtils.HexagonUtils import (
    hex_distance,
    count_open_sequences
)


class PentalathMinimaxPlayer:
    def __init__(self, player_id, max_depth=8, beam_width=25):
        self.player_id = player_id
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.transposition_table = {}
        self._sequence_cache = {}
        self._process = None
        self._parent_conn = None
        self.best_move = None

        #Killer moves and history heuristic tables for better move ordering
        self.killer_moves = [[None, None] for _ in range(max_depth + 1)]
        self.history_scores = {}


    def start_search(self, game_state):
        #Clears all cached data before beginning a fresh search
        if self._process and self._process.is_alive():
            return
        self.transposition_table.clear()
        self._sequence_cache.clear()
        self.history_scores.clear()

    def _run_minimax(self, game_state, conn):
        #Entry point for the worker process - sends the chosen move back through the pipe
        move = self.make_move(game_state)
        conn.send(move)
        conn.close()

    def get_best_move(self, timeout=None):
        #Polls the pipe for a completed result; returns None if the search is still running
        if not self._parent_conn:
            return None
        if self._parent_conn.poll(timeout):
            self.best_move = self._parent_conn.recv()
            self._parent_conn.close()
            self._parent_conn = None
            return self.best_move
        return None

    # MOVE SELECTION/PREFERENCE

    def make_move(self, game_state):
        """
        Top-level move selection using iterative deepening.
        On the first two moves, returns a centre-biased opening move.
        Otherwise, runs iterative deepening from depth 2 up to max_depth,
        keeping the best result found so far in case the search is cut short.
        """
        validMoves = game_state.get_valid_moves()
        if not validMoves:
            return None

        #Opening: prefer centre or near-centre for the first two plies
        if len(game_state.move_history) < 2:
            center = (0, 0)
            if center in validMoves:
                return center
            scored = [(-hex_distance(m, center) + random.uniform(-0.3, 0.3), m) for m in validMoves]
            scored.sort(reverse=True)
            return scored[0][1]

        #Iterative deepening for better move ordering across increasing horizons
        bestMove = None
        bestScore = -math.inf

        for depth in range(2, self.max_depth + 1, 2):
            alpha = -math.inf
            beta = math.inf
            moves = self.get_ordered_moves(game_state, 0)

            currentBest = None
            currentBestScore = -math.inf

            for move in moves:
                captured = game_state.make_move(move, self.player_id)
                score = self.min_value(game_state, 1, alpha, beta, depth)
                self.undo_full_move(game_state, move, captured)

                if score > currentBestScore:
                    currentBestScore = score
                    currentBest = move

                alpha = max(alpha, currentBestScore)

            if currentBest:
                bestMove = currentBest
                bestScore = currentBestScore

        return bestMove if bestMove else validMoves[0]

    # ALPHA BETA PRUNING SEARCH

    def max_value(self, game_state, depth, alpha, beta, max_depth=None):
        """
        Maximising node - self.player_id moves here.
        Uses the transposition table to skip already-evaluated states.
        Falls through to quiescence search at the depth limit to reduce the horizon effect.
        Updates killer moves and the history heuristic on beta cut-offs.
        """
        if max_depth is None:
            max_depth = self.max_depth

        stateHash = self.hash_state(game_state)
        if stateHash in self.transposition_table:
            entry = self.transposition_table[stateHash]
            if entry['depth'] >= (max_depth - depth):
                return entry['score']

        if game_state.is_terminal():
            score = self.evaluate_terminal(game_state)
            self.transposition_table[stateHash] = {'score': score, 'depth': max_depth - depth}
            return score

        if depth >= max_depth:
            #Quiescence search to avoid cutting off mid-tactical sequence
            score = self.quiescence_search(game_state, alpha, beta, self.player_id, 2)
            return score

        value = -math.inf
        moves = self.get_ordered_moves(game_state, depth)

        for move in moves:
            captured = game_state.make_move(move, self.player_id)
            score = self.min_value(game_state, depth + 1, alpha, beta, max_depth)
            self.undo_full_move(game_state, move, captured)

            if score > value:
                value = score
                #Update killer move table for this depth
                if depth < len(self.killer_moves):
                    if self.killer_moves[depth][0] != move:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = move

            if value >= beta:
                #Beta cut-off
                self.history_scores[move] = self.history_scores.get(move, 0) + (max_depth - depth) ** 2
                self.transposition_table[stateHash] = {'score': value, 'depth': max_depth - depth}
                return value

            alpha = max(alpha, value)

        self.transposition_table[stateHash] = {'score': value, 'depth': max_depth - depth}
        return value

    def min_value(self, game_state, depth, alpha, beta, max_depth=None):
        """
        Minimising node - the opponent moves here.
        Mirrors max_value but searches from the opponent's perspective.
        """
        if max_depth is None:
            max_depth = self.max_depth

        stateHash = self.hash_state(game_state)
        if stateHash in self.transposition_table:
            entry = self.transposition_table[stateHash]
            if entry['depth'] >= (max_depth - depth):
                return entry['score']

        if game_state.is_terminal():
            score = self.evaluate_terminal(game_state)
            self.transposition_table[stateHash] = {'score': score, 'depth': max_depth - depth}
            return score

        if depth >= max_depth:
            score = self.quiescence_search(game_state, alpha, beta, 3 - self.player_id, 2)
            return score

        value = math.inf
        opponentId = 3 - self.player_id
        moves = self.get_ordered_moves(game_state, depth)

        for move in moves:
            captured = game_state.make_move(move, opponentId)
            score = self.max_value(game_state, depth + 1, alpha, beta, max_depth)
            self.undo_full_move(game_state, move, captured)

            if score < value:
                value = score
                #Update killer move table for this depth
                if depth < len(self.killer_moves):
                    if self.killer_moves[depth][0] != move:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = move

            if value <= alpha:
                #Alpha cut-off
                self.history_scores[move] = self.history_scores.get(move, 0) + (max_depth - depth) ** 2
                self.transposition_table[stateHash] = {'score': value, 'depth': max_depth - depth}
                return value

            beta = min(beta, value)

        self.transposition_table[stateHash] = {'score': value, 'depth': max_depth - depth}
        return value

    # QUESCENCE SEARCH

    def quiescence_search(self, game_state, alpha, beta, player, depth_left):
        """
        Extends the search beyond the horizon for tactical positions to avoid
        cutting off mid-capture sequences. Evaluates a static stand-pat score first;
        if that already exceeds the bound the position is accepted immediately.
        Only capturing moves are expanded, and width is limited to five candidates.
        """
        standPat = self.evaluate(game_state)

        if depth_left == 0:
            return standPat

        if player == self.player_id:
            if standPat >= beta:
                return beta
            alpha = max(alpha, standPat)

            #Only consider captures and immediate threats
            tacticalMoves = self.get_tactical_moves(game_state, player)
            for move in tacticalMoves[:5]:
                captured = game_state.make_move(move, player)
                if captured:
                    score = self.quiescence_search(game_state, alpha, beta, 3 - player, depth_left - 1)
                    self.undo_full_move(game_state, move, captured)
                    if score >= beta:
                        return beta
                    alpha = max(alpha, score)
                else:
                    self.undo_full_move(game_state, move, captured)
            return alpha
        else:
            if standPat <= alpha:
                return alpha
            beta = min(beta, standPat)

            tacticalMoves = self.get_tactical_moves(game_state, player)
            for move in tacticalMoves[:5]:
                captured = game_state.make_move(move, player)
                if captured:
                    score = self.quiescence_search(game_state, alpha, beta, 3 - player, depth_left - 1)
                    self.undo_full_move(game_state, move, captured)
                    if score <= alpha:
                        return alpha
                    beta = min(beta, score)
                else:
                    self.undo_full_move(game_state, move, captured)
            return beta

    def get_tactical_moves(self, game_state, player):
        """
        Returns only the moves that result in a capture or create an immediate
        four-in-a-row threat, used to seed the quiescence search.
        """
        validMoves = game_state.get_valid_moves()
        tactical = []

        for move in validMoves:
            captured = game_state.make_move(move, player)

            #Tactical if a capture occurred or a four-in-a-row threat is created
            isTactical = len(captured) > 0
            if not isTactical:
                isTactical = game_state._has_consecutive(move, player, 4)

            self.undo_full_move(game_state, move, captured)

            if isTactical:
                tactical.append(move)

        return tactical

    # Move order

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
            "player_fives":    count_open_sequences(game_state.board, player,   5),
            "player_fours":    count_open_sequences(game_state.board, player,   4),
            "player_threes":   count_open_sequences(game_state.board, player,   3),
            "opponent_fives":  count_open_sequences(game_state.board, opponent, 5),
            "opponent_fours":  count_open_sequences(game_state.board, opponent, 4),
            "opponent_threes": count_open_sequences(game_state.board, opponent, 3),
        }
        self._sequence_cache[stateHash] = result
        return result

    def get_ordered_moves(self, game_state, depth=0):
        """
        Returns all valid moves sorted by estimated quality.
        Priority order: killer moves, history heuristic, capture bonus,
        five/four-in-a-row threats, three-in-a-row blocks, centre proximity.
        At depth > 2 the list is pruned to beam_width; at depth > 0 to beam_width * 2.
        Moves that cause self-capture receive a heavy penalty.
        """
        validMoves = game_state.get_valid_moves()
        if not validMoves:
            return []

        center = (0, 0)
        seq = self.get_sequences(game_state)
        scoredMoves = []

        for move in validMoves:
            score = 0

            #Killer move heuristic: reward moves that caused cut-offs at this depth before
            if depth < len(self.killer_moves):
                if move == self.killer_moves[depth][0]:
                    score += 9000
                elif move == self.killer_moves[depth][1]:
                    score += 8000

            #History heuristic: reward moves that have historically caused cut-offs
            score += self.history_scores.get(move, 0)

            #Centre proximity bonus in the opening phase
            if len(game_state.move_history) < 10:
                score -= hex_distance(move, center) * 10

            #Simulate the move to inspect captures and immediate threats
            captured = game_state.make_move(move, self.player_id)

            #Heavy penalty for self-capture: losing our own pieces is very bad
            ourPiecesLost = sum(1 for c in captured if c in game_state.board and game_state.board.get(c, 0) == 0)
            if ourPiecesLost > 0:
                score -= ourPiecesLost * 100000

            #Bonus for capturing opponent pieces
            opponentCaptured = len(captured)
            if opponentCaptured > 0:
                score += opponentCaptured * 8000

            #Bonus for creating immediate five- or four-in-a-row threats
            if game_state._has_consecutive(move, self.player_id, 4):
                score += 15000
            elif game_state._has_consecutive(move, self.player_id, 3):
                score += 2000

            #Bonus for blocking an opponent four- or three-in-a-row
            opponentId = 3 - self.player_id
            game_state.board[move] = opponentId
            if game_state._has_consecutive(move, opponentId, 4):
                score += 10000
            elif game_state._has_consecutive(move, opponentId, 3):
                score += 1500

            self.undo_full_move(game_state, move, captured)

            #Sequence-based pattern bonuses from the cached counts
            score += seq["player_fours"]    * 3000
            score += seq["player_threes"]   *  500
            score -= seq["opponent_fours"]  * 4000
            score -= seq["opponent_threes"] *  600

            scoredMoves.append((score, move))

        scoredMoves.sort(key=lambda x: x[0], reverse=True)

        #Beam search pruning: tighten at deeper levels to limit branching
        if depth > 2:
            scoredMoves = scoredMoves[:self.beam_width]
        elif depth > 0:
            scoredMoves = scoredMoves[:self.beam_width * 2]

        return [m[1] for m in scoredMoves]

    # small helper for undos

    def undo_full_move(self, game_state, move, captured):
        """
        Reverses a move by clearing the placed cell and restoring all captured
        opponent pieces to their original positions in both the board and move history.
        """
        game_state.undo_move(move)
        opponent = 3 - self.player_id
        for c in captured:
            game_state.board[c] = opponent
            if c not in game_state.move_history:
                game_state.move_history.append(c)

    # EVALUATIOn

    def evaluate_terminal(self, game_state):
        """
        Returns a fixed large score for decisive terminal positions.
        A win for this player is +1 000 000, a loss is -1 000 000, a draw is 0.
        """
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        return 0

    def evaluate(self, game_state):
        """
        Heuristic board evaluation from self.player_id's perspective for non-terminal states.
        Combines sequence counts, material difference, centre control, and a group
        vulnerability assessment that penalises pieces with few liberties.
        """
        seq = self.get_sequences(game_state)

        #Short-circuit to terminal evaluation if the game is already decided
        if game_state.is_terminal():
            return self.evaluate_terminal(game_state)

        score = 0

        #Winning and immediate-threat sequences
        score += seq["player_fives"]    * 1000000
        score -= seq["opponent_fives"]  * 1200000
        score += seq["player_fours"]    *   50000
        score -= seq["opponent_fours"]  *   60000
        score += seq["player_threes"]   *    5000
        score -= seq["opponent_threes"] *    6000

        #Material advantage: each extra piece on the board is worth a significant bonus
        playerPieces   = sum(1 for v in game_state.board.values() if v == self.player_id)
        opponentPieces = sum(1 for v in game_state.board.values() if v == (3 - self.player_id))
        materialDiff = playerPieces - opponentPieces
        score += materialDiff * 2000

        #Capture vulnerability: penalise our exposed groups, reward opponent exposure
        playerVuln   = self.evaluate_capture_vulnerability(game_state, self.player_id)
        opponentVuln = self.evaluate_capture_vulnerability(game_state, 3 - self.player_id)
        score -= playerVuln   * 8000
        score += opponentVuln * 6000

        #Centre control bonus: pieces closer to the centre score higher
        center = (0, 0)
        for pos, val in game_state.board.items():
            if val == self.player_id:
                score += max(0, 5 - hex_distance(pos, center)) * 10
            elif val == (3 - self.player_id):
                score -= max(0, 5 - hex_distance(pos, center)) * 10

        return score

    def evaluate_capture_vulnerability(self, game_state, player):
        """
        BFS-floods each connected group of `player`s pieces to count liberties.
        Groups with fewer liberties are weighted more heavily, reflecting how close
        they are to being fully surrounded and captured.
        Returns a total vulnerability score summed across all groups.
        """
        visited = set()
        totalVulnerability = 0

        def neighbors(pos):
            q, r = pos
            return [(q + dq, r + dr) for dq, dr in game_state.DIRECTIONS]

        for pos, val in game_state.board.items():
            if val != player or pos in visited:
                continue

            #BFS to collect the connected group and its liberties
            group = set()
            stack = [pos]
            liberties = set()

            while stack:
                current = stack.pop()
                if current in group:
                    continue
                group.add(current)
                visited.add(current)

                for n in neighbors(current):
                    nVal = game_state.board.get(n, None)
                    if nVal == 0:
                        liberties.add(n)
                    elif nVal == player and n not in group:
                        stack.append(n)

            #Score vulnerability based on liberty count relative to group size
            libCount   = len(liberties)
            groupSize  = len(group)

            if libCount == 0:
                #Already captured - should not occur during normal evaluation
                totalVulnerability += groupSize * 10
            elif libCount == 1:
                #One liberty - extremely vulnerable
                totalVulnerability += groupSize * 5
            elif libCount == 2:
                #Two liberties - vulnerable
                totalVulnerability += groupSize * 2
            elif libCount == 3:
                #Three liberties - somewhat exposed
                totalVulnerability += groupSize * 0.5
            #Four or more liberties - relatively safe, no penalty

        return totalVulnerability

    def hash_state(self, game_state):
        #Produces a hashable key from the current board for transposition table lookups
        return hash(frozenset(game_state.board.items()))