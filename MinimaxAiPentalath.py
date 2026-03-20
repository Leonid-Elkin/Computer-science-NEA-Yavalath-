import math
import random
import multiprocessing
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
        
        # Killer moves for better move ordering
        self.killer_moves = [[None, None] for _ in range(max_depth + 1)]
        self.history_scores = {}

    def start_search(self, game_state):
        if self._process and self._process.is_alive():
            return
        self.transposition_table.clear()
        self._sequence_cache.clear()
        self.history_scores.clear()
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
        return None

    def make_move(self, game_state):
        valid_moves = game_state.get_valid_moves()
        if not valid_moves:
            return None

        # Opening book: prefer center or near-center
        if len(game_state.move_history) < 2:
            center = (0, 0)
            if center in valid_moves:
                return center
            scored = [(-hex_distance(m, center) + random.uniform(-0.3, 0.3), m) for m in valid_moves]
            scored.sort(reverse=True)
            return scored[0][1]

        # Iterative deepening for better move ordering
        best_move = None
        best_score = -math.inf
        
        for depth in range(2, self.max_depth + 1, 2):
            alpha = -math.inf
            beta = math.inf
            moves = self.get_ordered_moves(game_state, 0)
            
            current_best = None
            current_best_score = -math.inf
            
            for move in moves:
                captured = game_state.make_move(move, self.player_id)
                score = self.min_value(game_state, 1, alpha, beta, depth)
                self.undo_full_move(game_state, move, captured)
                
                if score > current_best_score:
                    current_best_score = score
                    current_best = move
                    
                alpha = max(alpha, current_best_score)
            
            if current_best:
                best_move = current_best
                best_score = current_best_score

        return best_move if best_move else valid_moves[0]

    def max_value(self, game_state, depth, alpha, beta, max_depth=None):
        if max_depth is None:
            max_depth = self.max_depth
            
        state_hash = self.hash_state(game_state)
        if state_hash in self.transposition_table:
            entry = self.transposition_table[state_hash]
            if entry['depth'] >= (max_depth - depth):
                return entry['score']

        if game_state.is_terminal():
            score = self.evaluate_terminal(game_state)
            self.transposition_table[state_hash] = {'score': score, 'depth': max_depth - depth}
            return score
            
        if depth >= max_depth:
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
                # Update killer moves
                if depth < len(self.killer_moves):
                    if self.killer_moves[depth][0] != move:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = move
                        
            if value >= beta:
                # Update history heuristic
                self.history_scores[move] = self.history_scores.get(move, 0) + (max_depth - depth) ** 2
                self.transposition_table[state_hash] = {'score': value, 'depth': max_depth - depth}
                return value
            alpha = max(alpha, value)

        self.transposition_table[state_hash] = {'score': value, 'depth': max_depth - depth}
        return value

    def min_value(self, game_state, depth, alpha, beta, max_depth=None):
        if max_depth is None:
            max_depth = self.max_depth
            
        state_hash = self.hash_state(game_state)
        if state_hash in self.transposition_table:
            entry = self.transposition_table[state_hash]
            if entry['depth'] >= (max_depth - depth):
                return entry['score']

        if game_state.is_terminal():
            score = self.evaluate_terminal(game_state)
            self.transposition_table[state_hash] = {'score': score, 'depth': max_depth - depth}
            return score
            
        if depth >= max_depth:
            score = self.quiescence_search(game_state, alpha, beta, 3 - self.player_id, 2)
            return score

        value = math.inf
        opponent_id = 3 - self.player_id
        moves = self.get_ordered_moves(game_state, depth)
        
        for move in moves:
            captured = game_state.make_move(move, opponent_id)
            score = self.max_value(game_state, depth + 1, alpha, beta, max_depth)
            self.undo_full_move(game_state, move, captured)
            
            if score < value:
                value = score
                if depth < len(self.killer_moves):
                    if self.killer_moves[depth][0] != move:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = move
                        
            if value <= alpha:
                self.history_scores[move] = self.history_scores.get(move, 0) + (max_depth - depth) ** 2
                self.transposition_table[state_hash] = {'score': value, 'depth': max_depth - depth}
                return value
            beta = min(beta, value)

        self.transposition_table[state_hash] = {'score': value, 'depth': max_depth - depth}
        return value

    def quiescence_search(self, game_state, alpha, beta, player, depth_left):
        """Search tactical positions to avoid horizon effect"""
        stand_pat = self.evaluate(game_state)
        
        if depth_left == 0:
            return stand_pat
            
        if player == self.player_id:
            if stand_pat >= beta:
                return beta
            alpha = max(alpha, stand_pat)
            
            # Only consider captures and threats
            tactical_moves = self.get_tactical_moves(game_state, player)
            for move in tactical_moves[:5]:  # Limit quiescence width
                captured = game_state.make_move(move, player)
                if captured:  # Only continue if something was captured
                    score = self.quiescence_search(game_state, alpha, beta, 3 - player, depth_left - 1)
                    self.undo_full_move(game_state, move, captured)
                    if score >= beta:
                        return beta
                    alpha = max(alpha, score)
                else:
                    self.undo_full_move(game_state, move, captured)
            return alpha
        else:
            if stand_pat <= alpha:
                return alpha
            beta = min(beta, stand_pat)
            
            tactical_moves = self.get_tactical_moves(game_state, player)
            for move in tactical_moves[:5]:
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
        """Get moves that create threats or captures"""
        valid_moves = game_state.get_valid_moves()
        tactical = []
        
        for move in valid_moves:
            captured = game_state.make_move(move, player)
            
            # Check if this move captures or creates immediate threats
            is_tactical = len(captured) > 0
            if not is_tactical:
                # Check if it creates a 4-in-a-row threat
                is_tactical = game_state._has_consecutive(move, player, 4)
            
            self.undo_full_move(game_state, move, captured)
            
            if is_tactical:
                tactical.append(move)
        
        return tactical

    def get_sequences(self, game_state):
        state_hash = self.hash_state(game_state)
        if state_hash in self._sequence_cache:
            return self._sequence_cache[state_hash]

        player = self.player_id
        opponent = 3 - player
        result = {
            "player_fives": count_open_sequences(game_state.board, player, 5),
            "player_fours": count_open_sequences(game_state.board, player, 4),
            "player_threes": count_open_sequences(game_state.board, player, 3),
            "opponent_fives": count_open_sequences(game_state.board, opponent, 5),
            "opponent_fours": count_open_sequences(game_state.board, opponent, 4),
            "opponent_threes": count_open_sequences(game_state.board, opponent, 3),
        }
        self._sequence_cache[state_hash] = result
        return result

    def get_ordered_moves(self, game_state, depth=0):
        valid_moves = game_state.get_valid_moves()
        if not valid_moves:
            return []

        center = (0, 0)
        seq = self.get_sequences(game_state)
        scored_moves = []

        for move in valid_moves:
            score = 0
            
            # Killer move heuristic
            if depth < len(self.killer_moves):
                if move == self.killer_moves[depth][0]:
                    score += 9000
                elif move == self.killer_moves[depth][1]:
                    score += 8000
            
            # History heuristic
            score += self.history_scores.get(move, 0)
            
            # Distance to center (early game)
            if len(game_state.move_history) < 10:
                score -= hex_distance(move, center) * 10
            
            # CRITICAL: Check if this move causes our pieces to be captured
            captured = game_state.make_move(move, self.player_id)
            
            # Check if we lost any of our own pieces (very bad!)
            our_pieces_lost = sum(1 for c in captured if c in game_state.board and game_state.board.get(c, 0) == 0)
            if our_pieces_lost > 0:
                # Massive penalty for losing our own pieces
                score -= our_pieces_lost * 100000
            
            # Heavy bonus for capturing opponent pieces
            opponent_pieces_captured = len(captured)
            if opponent_pieces_captured > 0:
                score += opponent_pieces_captured * 8000
            
            # Check threats created
            if game_state._has_consecutive(move, self.player_id, 4):
                score += 15000
            elif game_state._has_consecutive(move, self.player_id, 3):
                score += 2000
            
            # Check if blocking opponent threats
            opponent_id = 3 - self.player_id
            game_state.board[move] = opponent_id
            if game_state._has_consecutive(move, opponent_id, 4):
                score += 10000
            elif game_state._has_consecutive(move, opponent_id, 3):
                score += 1500
            
            self.undo_full_move(game_state, move, captured)
            
            # Pattern bonuses
            score += seq["player_fours"] * 3000
            score += seq["player_threes"] * 500
            score -= seq["opponent_fours"] * 4000
            score -= seq["opponent_threes"] * 600
            
            scored_moves.append((score, move))

        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        # Beam search pruning at deeper levels
        if depth > 2:
            scored_moves = scored_moves[:self.beam_width]
        elif depth > 0:
            scored_moves = scored_moves[:self.beam_width * 2]

        return [m[1] for m in scored_moves]

    def undo_full_move(self, game_state, move, captured):
        game_state.undo_move(move)
        opponent = 3 - self.player_id
        for c in captured:
            game_state.board[c] = opponent
            if c not in game_state.move_history:
                game_state.move_history.append(c)

    def evaluate_terminal(self, game_state):
        """Evaluate terminal positions"""
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        return 0  # Draw

    def evaluate(self, game_state):
        """Enhanced evaluation function with capture vulnerability"""
        seq = self.get_sequences(game_state)
        
        # Check terminal
        if game_state.is_terminal():
            return self.evaluate_terminal(game_state)
        
        score = 0
        
        # Winning sequences
        score += seq["player_fives"] * 1000000
        score -= seq["opponent_fives"] * 1200000
        
        # Immediate threats (4 in a row)
        score += seq["player_fours"] * 50000
        score -= seq["opponent_fours"] * 60000
        
        # Building threats (3 in a row)
        score += seq["player_threes"] * 5000
        score -= seq["opponent_threes"] * 6000
        
        # Material advantage (pieces on board) - VERY IMPORTANT
        player_pieces = sum(1 for v in game_state.board.values() if v == self.player_id)
        opponent_pieces = sum(1 for v in game_state.board.values() if v == (3 - self.player_id))
        material_diff = player_pieces - opponent_pieces
        score += material_diff * 2000  # Increased weight significantly
        
        # CRITICAL: Evaluate vulnerability to capture
        player_vulnerability = self.evaluate_capture_vulnerability(game_state, self.player_id)
        opponent_vulnerability = self.evaluate_capture_vulnerability(game_state, 3 - self.player_id)
        
        # Heavy penalty for vulnerable groups, bonus for opponent vulnerability
        score -= player_vulnerability * 8000
        score += opponent_vulnerability * 6000
        
        # Central control bonus
        center = (0, 0)
        for pos, val in game_state.board.items():
            if val == self.player_id:
                score += max(0, 5 - hex_distance(pos, center)) * 10
            elif val == (3 - self.player_id):
                score -= max(0, 5 - hex_distance(pos, center)) * 10
        
        return score
    
    def evaluate_capture_vulnerability(self, game_state, player):
        """
        Evaluate how vulnerable a player's groups are to being captured.
        Returns a score representing the danger level.
        """
        visited = set()
        total_vulnerability = 0
        
        def neighbors(pos):
            q, r = pos
            return [(q + dq, r + dr) for dq, dr in game_state.DIRECTIONS]
        
        # Find all groups of this player
        for pos, val in game_state.board.items():
            if val != player or pos in visited:
                continue
            
            # BFS to find connected group
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
                    n_val = game_state.board.get(n, None)
                    if n_val == 0:
                        liberties.add(n)
                    elif n_val == player and n not in group:
                        stack.append(n)
            
            # Calculate vulnerability based on liberties
            lib_count = len(liberties)
            group_size = len(group)
            
            if lib_count == 0:
                # Already captured (shouldn't happen in normal eval)
                total_vulnerability += group_size * 10
            elif lib_count == 1:
                # One liberty - VERY vulnerable
                total_vulnerability += group_size * 5
            elif lib_count == 2:
                # Two liberties - vulnerable
                total_vulnerability += group_size * 2
            elif lib_count == 3:
                # Three liberties - somewhat vulnerable
                total_vulnerability += group_size * 0.5
            # 4+ liberties = relatively safe
        
        return total_vulnerability


        #I fucking hate result hashing its bad and poopy and did di mention bad and poopy and Im goignt o fail exams and cry mysef to sleep its so bad help me please
    def hash_state(self, game_state):
        return hash(frozenset(game_state.board.items()))