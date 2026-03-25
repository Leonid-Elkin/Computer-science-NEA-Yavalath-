import math
import random
from copy import deepcopy


class SusanMinimaxPlayer:
    def __init__(self, player_id, max_depth=4, beam_width=15):
        self.player_id = player_id
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.transposition_table = {}

    # --- Entry point ---

    def get_move(self, game_state):
        """
        Main entry point for move selection. Iterates all valid moves, immediately
        returns any that win outright, otherwise runs a full minimax search and
        returns the move with the highest score.
        """
        validMoves = self.get_all_valid_moves(game_state, self.player_id)
        if not validMoves:
            return None

        bestScore = -math.inf
        bestMove = None
        alpha = -math.inf
        beta = math.inf

        for move in validMoves:
            gsCopy = deepcopy(game_state)
            success = self.apply_move(gsCopy, move, self.player_id)
            if not success:
                continue

            #Return immediately if this move wins the game outright
            if gsCopy.get_winner() == self.player_id:
                return move

            score = self.min_value(gsCopy, 1, alpha, beta)
            if score > bestScore:
                bestScore = score
                bestMove = move

            alpha = max(alpha, bestScore)

        return bestMove if bestMove else (validMoves[0] if validMoves else None)

    # --- Alpha-beta search ---

    def max_value(self, game_state, depth, alpha, beta):
        """
        Maximising node - self.player_id moves here.
        Returns the terminal score immediately for decisive positions,
        falls back to the heuristic evaluation at the depth limit.
        """
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        elif winner == 0:
            return 0

        if depth >= self.max_depth:
            return self.evaluate(game_state)

        value = -math.inf
        moves = self.get_ordered_moves(game_state, self.player_id, depth)

        for move in moves:
            gsCopy = deepcopy(game_state)
            success = self.apply_move(gsCopy, move, self.player_id)
            if not success:
                continue

            score = self.min_value(gsCopy, depth + 1, alpha, beta)
            value = max(value, score)

            if value >= beta:
                return value
            alpha = max(alpha, value)

        return value if value != -math.inf else self.evaluate(game_state)

    def min_value(self, game_state, depth, alpha, beta):
        """
        Minimising node - the opponent moves here.
        Mirrors max_value but searches from the opponent's perspective.
        """
        opponent = 3 - self.player_id

        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == opponent:
            return -1000000
        elif winner == 0:
            return 0

        if depth >= self.max_depth:
            return self.evaluate(game_state)

        value = math.inf
        moves = self.get_ordered_moves(game_state, opponent, depth)

        for move in moves:
            gsCopy = deepcopy(game_state)
            success = self.apply_move(gsCopy, move, opponent)
            if not success:
                continue

            score = self.max_value(gsCopy, depth + 1, alpha, beta)
            value = min(value, score)

            if value <= alpha:
                return value
            beta = min(beta, value)

        return value if value != math.inf else self.evaluate(game_state)

    # --- Move generation ---

    def get_all_valid_moves(self, game_state, player):
        """
        Returns all legal moves for `player`: placements on any empty cell,
        and movements of existing pieces to any adjacent empty cell.
        Each candidate is validated against the game state to filter illegal self-captures.
        """
        moves = []

        #Placement moves: any empty cell that does not cause self-capture
        for pos, val in game_state.board.items():
            if val == 0:
                gsTest = deepcopy(game_state)
                if gsTest.make_move(pos, player):
                    moves.append(pos)

        #Movement moves: slide an existing piece to an adjacent empty cell
        for pos, val in game_state.board.items():
            if val != player:
                continue
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) != 0:
                    continue
                gsTest = deepcopy(game_state)
                if gsTest.make_move(adj, player, from_pos=pos):
                    moves.append((pos, adj))

        return moves

    def get_ordered_moves(self, game_state, player, depth):
        """
        Returns all legal moves sorted by estimated quality.
        Scores each move based on: immediate win/loss detection, capture threats,
        self-capture danger, vulnerability change for both players, movement preference,
        and centre proximity. Pruned to beam_width at depth > 1.
        """
        moves = self.get_all_valid_moves(game_state, player)
        if not moves:
            return []

        scoredMoves = []
        opponent = 3 - player

        for move in moves:
            score = 0
            gsTest = deepcopy(game_state)
            success = self.apply_move(gsTest, move, player)
            if not success:
                continue

            winner = gsTest.get_winner()
            if winner == player:
                score += 10000000
            elif winner == opponent:
                score -= 10000000

            #Reward moves that put opponent pieces in immediate capture danger
            captureThreats = self.count_immediate_capture_threats(gsTest, opponent)
            score += captureThreats * 100000

            #Penalise moves that leave our own pieces in immediate capture danger
            ourDanger = self.count_immediate_capture_threats(gsTest, player)
            score -= ourDanger * 150000

            #Reward reducing our own vulnerability and increasing opponent's
            ourVulnBefore  = self.count_vulnerable_pieces(game_state, player)
            ourVulnAfter   = self.count_vulnerable_pieces(gsTest, player)
            oppVulnBefore  = self.count_vulnerable_pieces(game_state, opponent)
            oppVulnAfter   = self.count_vulnerable_pieces(gsTest, opponent)
            score += (ourVulnBefore - ourVulnAfter) * 8000
            score += (oppVulnAfter - oppVulnBefore) * 5000

            #Prefer movement over placement as it tends to be more tactical
            if isinstance(move, tuple) and isinstance(move[0], tuple):
                score += 1000

            #Centre proximity bonus for the target cell
            targetPos = move[1] if isinstance(move, tuple) and isinstance(move[0], tuple) else move
            score -= self.hex_distance(targetPos, (0, 0)) * 10

            scoredMoves.append((score, move))

        scoredMoves.sort(key=lambda x: x[0], reverse=True)

        #Prune to beam width at deeper levels to limit branching
        if depth > 1:
            scoredMoves = scoredMoves[:self.beam_width]

        return [m[1] for m in scoredMoves]

    def apply_move(self, game_state, move, player):
        """
        Dispatches either a movement (2-tuple of positions) or a placement (single position)
        to the game state's make_move method.
        """
        if isinstance(move, tuple) and len(move) == 2 and isinstance(move[0], tuple):
            fromPos, toPos = move
            return game_state.make_move(toPos, player, from_pos=fromPos)
        else:
            return game_state.make_move(move, player)

    # --- Heuristic evaluation ---

    def evaluate(self, game_state):
        """
        Heuristic board evaluation from self.player_id's perspective.
        Combines: material count, total liberties, piece vulnerability,
        immediate capture threat counts, minimum liberty safety, and centre control.
        Terminal positions are handled separately with fixed large scores.
        """
        winner = game_state.get_winner()
        if winner == self.player_id:
            return 1000000
        elif winner == (3 - self.player_id):
            return -1000000
        elif winner == 0:
            return 0

        score = 0
        opponent = 3 - self.player_id

        #Material count: more pieces on the board is better
        myPieces  = sum(1 for v in game_state.board.values() if v == self.player_id)
        oppPieces = sum(1 for v in game_state.board.values() if v == opponent)
        score += (myPieces - oppPieces) * 10000

        #Liberty count: more breathing room is safer
        myLiberties  = self.count_total_liberties(game_state, self.player_id)
        oppLiberties = self.count_total_liberties(game_state, opponent)
        score += (myLiberties - oppLiberties) * 2000

        #Piece vulnerability: fewer pieces with low liberty counts is better
        myVulnerable  = self.count_vulnerable_pieces(game_state, self.player_id)
        oppVulnerable = self.count_vulnerable_pieces(game_state, opponent)
        score -= myVulnerable  * 8000
        score += oppVulnerable * 5000

        #Immediate capture threats for both sides
        myCaptureDanger  = self.count_immediate_capture_threats(game_state, self.player_id)
        oppCaptureDanger = self.count_immediate_capture_threats(game_state, opponent)
        score -= myCaptureDanger  * 15000
        score += oppCaptureDanger * 10000

        #Minimum liberty safety: one liberty is very dangerous, two is risky
        myMinLib  = self.get_minimum_liberties(game_state, self.player_id)
        oppMinLib = self.get_minimum_liberties(game_state, opponent)
        if myMinLib == 1:
            score -= 20000
        elif myMinLib == 2:
            score -= 5000
        if oppMinLib == 1:
            score += 15000
        elif oppMinLib == 2:
            score += 3000

        #Centre control: pieces closer to the centre receive a small bonus
        center = (0, 0)
        for pos, val in game_state.board.items():
            if val == self.player_id:
                score += max(0, 5 - self.hex_distance(pos, center)) * 50
            elif val == opponent:
                score -= max(0, 5 - self.hex_distance(pos, center)) * 50

        return score

    # --- Utility methods ---

    def count_total_liberties(self, game_state, player):
        """
        Counts the total number of unique empty cells adjacent to any of `player`s pieces.
        Each empty cell is counted only once even if it borders multiple pieces.
        """
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
        #Counts pieces that have only one or two liberties and are therefore in danger
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
        Counts how many of `player`s pieces can be captured on the very next move.
        A piece is considered threatened if it has exactly one liberty and the opponent
        can legally fill that liberty, causing the piece to be removed.
        """
        threats = 0
        opponent = 3 - player

        for pos, val in game_state.board.items():
            if val != player:
                continue

            #Find all liberties for this piece
            liberties = []
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0:
                    liberties.append(adj)

            #Threat exists if the single liberty can be legally filled by the opponent
            if len(liberties) == 1:
                gsTest = deepcopy(game_state)
                if gsTest.make_move(liberties[0], opponent):
                    if gsTest.board.get(pos, 0) != player:
                        threats += 1

        return threats

    def get_minimum_liberties(self, game_state, player):
        """
        Returns the smallest liberty count across all of `player`s pieces.
        Used to detect worst-case vulnerability; returns 6 if the player has no pieces.
        """
        minLib = math.inf

        for pos, val in game_state.board.items():
            if val != player:
                continue

            liberties = 0
            for dq, dr in game_state.DIRECTIONS:
                adj = (pos[0] + dq, pos[1] + dr)
                if game_state.board.get(adj, None) == 0:
                    liberties += 1

            minLib = min(minLib, liberties)

        return minLib if minLib != math.inf else 6

    def hex_distance(self, a, b):
        #Calculates the hex grid distance between two axial coordinates
        aq, ar = a
        bq, br = b
        return (abs(aq - bq) + abs(aq + ar - bq - br) + abs(ar - br)) // 2