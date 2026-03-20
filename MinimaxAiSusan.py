import math
import random
from copy import deepcopy

class SusanMinimaxPlayer:
    def __init__(self, player_id, max_depth=4, beam_width=15):
        self.player_id = player_id
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.transposition_table = {}

    # -------------------- Entry point --------------------
    def get_move(self, game_state):
        """Main entry point for getting the best move"""
        valid_moves = self.get_all_valid_moves(game_state, self.player_id)
        
        if not valid_moves:
            return None
            
        best_score = -math.inf
        best_move = None
        alpha = -math.inf
        beta = math.inf

        # Evaluate all moves
        for move in valid_moves:
            gs_copy = deepcopy(game_state)
            success = self.apply_move(gs_copy, move, self.player_id)
            
            if not success:
                continue
            
            # Check if this move wins immediately
            if gs_copy.get_winner() == self.player_id:
                return move
                
            score = self.min_value(gs_copy, 1, alpha, beta)
            
            if score > best_score:
                best_score = score
                best_move = move
            alpha = max(alpha, best_score)

        return best_move if best_move else (valid_moves[0] if valid_moves else None)

    # -------------------- Minimax --------------------
    def max_value(self, game_state, depth, alpha, beta):
        """Maximizing player (AI)"""
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        elif winner == 0:  # draw
            return 0
            
        if depth >= self.max_depth:
            return self.evaluate(game_state)

        value = -math.inf
        moves = self.get_ordered_moves(game_state, self.player_id, depth)
        
        for move in moves:
            gs_copy = deepcopy(game_state)
            success = self.apply_move(gs_copy, move, self.player_id)
            
            if not success:
                continue
                
            score = self.min_value(gs_copy, depth + 1, alpha, beta)
            value = max(value, score)
            
            if value >= beta:
                return value
            alpha = max(alpha, value)
            
        return value if value != -math.inf else self.evaluate(game_state)

    def min_value(self, game_state, depth, alpha, beta):
        """Minimizing player (opponent)"""
        opponent = 3 - self.player_id
        
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == opponent:
            return -1000000
        elif winner == 0:  # draw
            return 0
            
        if depth >= self.max_depth:
            return self.evaluate(game_state)

        value = math.inf
        moves = self.get_ordered_moves(game_state, opponent, depth)
        
        for move in moves:
            gs_copy = deepcopy(game_state)
            success = self.apply_move(gs_copy, move, opponent)
            
            if not success:
                continue
                
            score = self.max_value(gs_copy, depth + 1, alpha, beta)
            value = min(value, score)
            
            if value <= alpha:
                return value
            beta = min(beta, value)
            
        return value if value != math.inf else self.evaluate(game_state)

    # -------------------- Move Generation --------------------
    def get_all_valid_moves(self, game_state, player):
        """Get all legal moves: placements and piece movements"""
        moves = []
        
        # 1) Placement moves - place new piece on any empty cell
        for pos, val in game_state.board.items():
            if val == 0:
                # Test if this placement is legal (doesn't self-capture)
                gs_test = deepcopy(game_state)
                if gs_test.make_move(pos, player):
                    moves.append(pos)
        
        # 2) Movement moves - move existing piece to adjacent empty cell
        for pos, val in game_state.board.items():
            if val != player:
                continue
                
            # Try moving this piece to each adjacent empty cell
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                
                if game_state.board.get(adj, None) != 0:
                    continue
                    
                # Test if this move is legal
                gs_test = deepcopy(game_state)
                if gs_test.make_move(adj, player, from_pos=pos):
                    moves.append((pos, adj))
                    
        return moves

    def get_ordered_moves(self, game_state, player, depth):
        """Get moves ordered by heuristic quality"""
        moves = self.get_all_valid_moves(game_state, player)
        
        if not moves:
            return []
        
        scored_moves = []
        opponent = 3 - player
        
        for move in moves:
            score = 0
            gs_test = deepcopy(game_state)
            
            # Apply move and check results
            success = self.apply_move(gs_test, move, player)
            if not success:
                continue
            
            # HUGE bonus for winning moves
            winner = gs_test.get_winner()
            if winner == player:
                score += 10000000
            elif winner == opponent:
                score -= 10000000
            
            # Count pieces that can be captured (opponent pieces with 1 liberty)
            capture_threats = self.count_immediate_capture_threats(gs_test, opponent)
            score += capture_threats * 100000
            
            # Heavily penalize if we can be captured next turn
            our_danger = self.count_immediate_capture_threats(gs_test, player)
            score -= our_danger * 150000
            
            # Prefer moves that reduce vulnerability (pieces with few liberties)
            our_vuln_before = self.count_vulnerable_pieces(game_state, player)
            our_vuln_after = self.count_vulnerable_pieces(gs_test, player)
            score += (our_vuln_before - our_vuln_after) * 8000
            
            # Prefer moves that increase opponent vulnerability
            opp_vuln_before = self.count_vulnerable_pieces(game_state, opponent)
            opp_vuln_after = self.count_vulnerable_pieces(gs_test, opponent)
            score += (opp_vuln_after - opp_vuln_before) * 5000
            
            # Prefer movement over placement (more tactical)
            if isinstance(move, tuple) and isinstance(move[0], tuple):
                score += 1000
            
            # Center control bonus
            if isinstance(move, tuple) and isinstance(move[0], tuple):
                target_pos = move[1]
            else:
                target_pos = move
            score -= self.hex_distance(target_pos, (0, 0)) * 10
            
            scored_moves.append((score, move))
        
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        # Beam search pruning at deeper levels
        if depth > 1:
            scored_moves = scored_moves[:self.beam_width]
        
        return [m[1] for m in scored_moves]

    def apply_move(self, game_state, move, player):
        """Apply a move to the game state"""
        if isinstance(move, tuple) and len(move) == 2 and isinstance(move[0], tuple):
            # Movement: (from_pos, to_pos)
            from_pos, to_pos = move
            return game_state.make_move(to_pos, player, from_pos=from_pos)
        else:
            # Placement: just a position
            return game_state.make_move(move, player)

    # -------------------- Heuristic Evaluation --------------------
    def evaluate(self, game_state):
        """Evaluate the position for the AI player"""
        # Check for terminal state
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        elif winner == 0:
            return 0
        
        score = 0
        opponent = 3 - self.player_id
        
        # 1. Material count (pieces on board) - more pieces is good
        my_pieces = sum(1 for v in game_state.board.values() if v == self.player_id)
        opp_pieces = sum(1 for v in game_state.board.values() if v == opponent)
        score += (my_pieces - opp_pieces) * 10000
        
        # 2. Liberty count (breathing room) - more liberties is safer
        my_liberties = self.count_total_liberties(game_state, self.player_id)
        opp_liberties = self.count_total_liberties(game_state, opponent)
        score += (my_liberties - opp_liberties) * 2000
        
        # 3. Vulnerability (pieces with few liberties) - fewer is better
        my_vulnerable = self.count_vulnerable_pieces(game_state, self.player_id)
        opp_vulnerable = self.count_vulnerable_pieces(game_state, opponent)
        score -= my_vulnerable * 8000
        score += opp_vulnerable * 5000
        
        # 4. Immediate capture threats - can opponent capture us next turn?
        my_capture_danger = self.count_immediate_capture_threats(game_state, self.player_id)
        opp_capture_danger = self.count_immediate_capture_threats(game_state, opponent)
        score -= my_capture_danger * 15000
        score += opp_capture_danger * 10000
        
        # 5. Minimum liberty of any piece (worst case scenario)
        my_min_lib = self.get_minimum_liberties(game_state, self.player_id)
        opp_min_lib = self.get_minimum_liberties(game_state, opponent)
        if my_min_lib == 1:
            score -= 20000  # Very dangerous
        elif my_min_lib == 2:
            score -= 5000   # Somewhat dangerous
        if opp_min_lib == 1:
            score += 15000  # Opponent in danger
        elif opp_min_lib == 2:
            score += 3000
        
        # 6. Center control (minor factor)
        center = (0, 0)
        for pos, val in game_state.board.items():
            if val == self.player_id:
                dist = self.hex_distance(pos, center)
                score += max(0, 5 - dist) * 50
            elif val == opponent:
                dist = self.hex_distance(pos, center)
                score -= max(0, 5 - dist) * 50
        
        return score

    def count_total_liberties(self, game_state, player):
        """Count total liberties (empty adjacent cells) for all player's pieces"""
        liberties = 0
        counted = set()
        
        for pos, val in game_state.board.items():
            if val != player:
                continue
            
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0 and adj not in counted:
                    liberties += 1
                    counted.add(adj)
        
        return liberties

    def count_vulnerable_pieces(self, game_state, player):
        """Count pieces with only 1 or 2 liberties (in danger)"""
        vulnerable = 0
        
        for pos, val in game_state.board.items():
            if val != player:
                continue
            
            liberties = 0
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0:
                    liberties += 1
            
            if liberties <= 2:
                vulnerable += 1
        
        return vulnerable

    def count_immediate_capture_threats(self, game_state, player):
        """
        Count how many of player's pieces can be captured on the very next move.
        A piece can be captured if it has only 1 liberty and opponent can fill it legally.
        """
        threats = 0
        opponent = 3 - player
        
        for pos, val in game_state.board.items():
            if val != player:
                continue
            
            # Find all liberties for this piece
            liberties = []
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0:
                    liberties.append(adj)
            
            # If only 1 liberty, check if opponent can fill it
            if len(liberties) == 1:
                gs_test = deepcopy(game_state)
                # Try opponent filling the last liberty
                if gs_test.make_move(liberties[0], opponent):
                    # Check if our piece got captured
                    if gs_test.board.get(pos, 0) != player:
                        threats += 1
        
        return threats

    def get_minimum_liberties(self, game_state, player):
        """Get the minimum number of liberties among all pieces"""
        min_lib = math.inf
        
        for pos, val in game_state.board.items():
            if val != player:
                continue
            
            liberties = 0
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0:
                    liberties += 1
            
            min_lib = min(min_lib, liberties)
        
        return min_lib if min_lib != math.inf else 6

    # -------------------- Utility --------------------
    def hex_distance(self, a, b):
        """Calculate hex distance between two positions"""
        aq, ar = a
        bq, br = b
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2