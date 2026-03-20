import math
import random
import multiprocessing
from ElkUtils.HexagonUtils import (
    hex_distance,
    find_opponent_gap_fours,
    detect_forced_lose_scenario,
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
        self._sequence_cache = {}  # Cache for open sequences

        self._process = None
        self._parent_conn = None
        self.best_move = None

    def start_search(self, game_state):
        """Starts minimax search in a separate process."""
        if self._process and self._process.is_alive():
            return

        self.transposition_table.clear()
        self._sequence_cache.clear()  # Clear cache for new search
        parent_conn, child_conn = multiprocessing.Pipe()
        self._parent_conn = parent_conn

        self._process = multiprocessing.Process(target=self._run_minimax, args=(game_state, child_conn))
        self._process.daemon = True
        self._process.start()

    def _run_minimax(self, game_state, conn):
        move = self.make_move(game_state)
        conn.send(move)
        conn.close()

    def get_best_move(self, timeout=None):
        if not self._parent_conn:
            return None
        if self._parent_conn.poll(timeout):
            self.best_move = self._parent_conn.recv()
            self._parent_conn.close()
            self._parent_conn = None
            return self.best_move
        else:
            return None

    def make_move(self, game_state):
        # Opening move: prefer center area with randomness
        if all(val == 0 for val in game_state.board.values()):
            valid_moves = game_state.get_valid_moves()
            if not valid_moves:
                return None
            center = (0, 0)
            scored_moves = []
            for move in valid_moves:
                dist = hex_distance(move, center)
                score = -dist + random.uniform(-0.5, 0.5)
                scored_moves.append((score, move))
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            top_moves = scored_moves[:3]
            return random.choice([m[1] for m in top_moves])

        # Detect forced lose due to gap threats
        opponent = 3 - self.player_id
        gap_threats = find_opponent_gap_fours(game_state.board, opponent)
        forced_lose = detect_forced_lose_scenario(game_state.board, self.player_id, opponent)

        if forced_lose:
            valid_moves = game_state.get_valid_moves()
            return random.choice(valid_moves) if valid_moves else None

        if gap_threats:
            for gap_pos, line in gap_threats:
                if not creates_three_in_a_row(game_state.board, gap_pos, self.player_id):
                    return gap_pos

        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

        moves = self.get_ordered_moves(game_state)

        for move in moves:
            game_state.make_move(move, self.player_id)
            score = self.min_value(game_state, 1, alpha, beta)
            game_state.undo_move(move)
            if score > best_score:
                best_score = score
                best_move = move
            if best_score > alpha:
                alpha = best_score

        return best_move

    def max_value(self, game_state, depth, alpha, beta):
        state_hash = self.hash_state(game_state)
        if state_hash in self.transposition_table:
            return self.transposition_table[state_hash]

        if game_state.is_terminal() or depth >= self.max_depth:
            val = self.evaluate(game_state)
            self.transposition_table[state_hash] = val
            return val

        value = -math.inf
        moves = self.get_ordered_moves(game_state, depth)
        for move in moves:
            game_state.make_move(move, self.player_id)
            value = max(value, self.min_value(game_state, depth + 1, alpha, beta))
            game_state.undo_move(move)
            if value >= beta:
                self.transposition_table[state_hash] = value
                return value
            if value > alpha:
                alpha = value

        self.transposition_table[state_hash] = value
        return value

    def min_value(self, game_state, depth, alpha, beta):
        state_hash = self.hash_state(game_state)
        if state_hash in self.transposition_table:
            return self.transposition_table[state_hash]

        if game_state.is_terminal() or depth >= self.max_depth:
            val = self.evaluate(game_state)
            self.transposition_table[state_hash] = val
            return val

        value = math.inf
        opponent_id = 3 - self.player_id
        moves = self.get_ordered_moves(game_state, depth)
        for move in moves:
            game_state.make_move(move, opponent_id)
            value = min(value, self.max_value(game_state, depth + 1, alpha, beta))
            game_state.undo_move(move)
            if value <= alpha:
                self.transposition_table[state_hash] = value
                return value
            if value < beta:
                beta = value

        self.transposition_table[state_hash] = value
        return value

    # --- Efficient sequence caching ---
    def get_sequences(self, game_state):
        state_hash = self.hash_state(game_state)
        if state_hash in self._sequence_cache:
            return self._sequence_cache[state_hash]

        player = self.player_id
        opponent = 3 - player

        result = {
            "player_fours": count_open_sequences(game_state.board, player, 4),
            "player_threes": count_open_sequences(game_state.board, player, 3),
            "opponent_fours": count_open_sequences(game_state.board, opponent, 4),
            "opponent_threes": count_open_sequences(game_state.board, opponent, 3),
        }

        self._sequence_cache[state_hash] = result
        return result

    # --- Ordered moves using cached sequences ---
    def get_ordered_moves(self, game_state, depth=0):
        valid_moves = game_state.get_valid_moves()
        if not valid_moves:
            return []

        center = (0, 0)
        opponent = 3 - self.player_id
        seq = self.get_sequences(game_state)

        forced_lose = detect_forced_lose_scenario(game_state.board, self.player_id, opponent)
        gap_threats = find_opponent_gap_fours(game_state.board, opponent)

        blocking_moves = []
        other_moves = []

        if forced_lose:
            return valid_moves

        for gap_pos, line in gap_threats:
            if gap_pos in valid_moves:
                if not creates_three_in_a_row(game_state.board, gap_pos, self.player_id):
                    blocking_moves.append((30000, gap_pos))

        blocking_set = {m[1] for m in blocking_moves}
        for move in valid_moves:
            if move in blocking_set:
                continue
            if self.blocks_opponent_three(game_state, move, opponent):
                dist_score = -hex_distance(move, center) * 10
                blocking_moves.append((10000 + dist_score, move))
            else:
                dist_score = -hex_distance(move, center)
                score = dist_score + seq["player_threes"] * 50 - seq["opponent_threes"] * 70
                other_moves.append((score, move))

        blocking_moves.sort(key=lambda x: x[0], reverse=True)
        other_moves.sort(key=lambda x: x[0], reverse=True)

        combined = blocking_moves + other_moves
        if depth > 1:
            combined = combined[:self.beam_width]

        return [m[1] for m in combined]

    def blocks_opponent_three(self, game_state, move, opponent):
        board = game_state.board
        for direction in DIRECTIONS:
            q, r = move
            dq, dr = direction

            prev1 = (q - dq, r - dr)
            prev2 = (q - 2*dq, r - 2*dr)
            next1 = (q + dq, r + dr)
            next2 = (q + 2*dq, r + 2*dr)

            if board.get(prev1, 0) == opponent and board.get(prev2, 0) == opponent:
                return True
            if board.get(prev1, 0) == opponent and board.get(next1, 0) == opponent:
                return True
            if board.get(next1, 0) == opponent and board.get(next2, 0) == opponent:
                return True
        return False

    def evaluate(self, game_state):
        seq = self.get_sequences(game_state)
        player_fours = seq["player_fours"]
        player_threes = seq["player_threes"]
        opponent_fours = seq["opponent_fours"]
        opponent_threes = seq["opponent_threes"]

        if game_state.is_terminal():
            last_pos = game_state.move_history[-1] if game_state.move_history else None
            if last_pos is not None:
                last_player = game_state.board[last_pos]
                if game_state._has_consecutive(last_pos, last_player, 4):
                    return 100000 if last_player == self.player_id else -100000
                if game_state._has_consecutive(last_pos, last_player, 3):
                    return -100000 if last_player == self.player_id else 100000
            return 0

        score = 0
        score += player_fours * 10000
        score -= opponent_fours * 12000
        score -= player_threes * 8000
        score += opponent_threes * 7000

        center = (0, 0)
        player_positions = [pos for pos, val in game_state.board.items() if val == self.player_id]
        opponent_positions = [pos for pos, val in game_state.board.items() if val == 3 - self.player_id]

        player_dist = [hex_distance(pos, center) for pos in player_positions]
        opp_dist = [hex_distance(pos, center) for pos in opponent_positions]

        if player_dist:
            score += 200 / (1 + min(player_dist))
        if opp_dist:
            score -= 250 / (1 + min(opp_dist))

        return score

    def hash_state(self, game_state):
        return hash(frozenset(game_state.board.items()))
