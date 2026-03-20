DIRECTIONS = [
    (1, 0), (0, 1), (-1, 1),
    (-1, 0), (0, -1), (1, -1)
]


def hex_distance(a, b):
    q1, r1 = a
    q2, r2 = b
    s1 = -q1 - r1
    s2 = -q2 - r2
    return max(abs(q1 - q2), abs(r1 - r2), abs(s1 - s2))
    #Stupid coords

def count_consecutive(board, pos, player, target_length, directions=DIRECTIONS):
    count = 0

    for dq, dr in directions:
        total_length = 1

        for direction_sign in [1, -1]:
            q, r = pos

            while True:
                q += direction_sign * dq
                r += direction_sign * dr

                if board.get((q, r), 0) == player:
                    total_length += 1
                else:
                    break

        if total_length >= target_length:
            count += 1

    return count

    #More O(N^2) operations for no reason


def is_winning_move(board, pos, player, directions=DIRECTIONS):
    board[pos] = player
    winning_lines = count_consecutive(board, pos, player, 4, directions)
    del board[pos]
    return winning_lines > 0


def creates_three_in_a_row(board, pos, player, directions=DIRECTIONS):
    board[pos] = player
    has_three = count_consecutive(board, pos, player, 3, directions)
    del board[pos]
    return has_three > 0


def find_opponent_gap_fours(board, opponent, directions=DIRECTIONS):
    threats = []
    visited = set()

    for position, value in board.items():
        if value != opponent:
            continue

        for dq, dr in directions:
            if (position, dq, dr) in visited:
                continue

            line = [position]
            q, r = position

            for _ in range(4):
                q += dq
                r += dr
                line.append((q, r))

            if len(line) < 5:
                continue

            opponent_stones = [p for p in line if board.get(p) == opponent]
            empty_cells = [p for p in line if board.get(p) == 0]

            if len(opponent_stones) == 4 and len(empty_cells) == 1:
                threats.append((empty_cells[0], line))

            for p in line:
                visited.add((p, dq, dr))

    return threats

#This is stupid stupid stupid


def detect_forced_lose_scenario(board, player, opponent, directions=DIRECTIONS):
    threats = find_opponent_gap_fours(board, opponent, directions)

    for gap_position, line in threats:
        board[gap_position] = player
        if count_consecutive(board, gap_position, player, 3, directions):
            del board[gap_position]
            return True
        del board[gap_position]

    return False


def find_all_forced_losses(board, player, opponent, directions=DIRECTIONS):
    forced_losses = []
    threats = find_opponent_gap_fours(board, opponent, directions)

    for gap_position, line in threats:
        board[gap_position] = player
        if count_consecutive(board, gap_position, player, 3, directions):
            forced_losses.append((gap_position, line))
        del board[gap_position]

    return forced_losses


def opponent_has_double_threat(board, opponent, directions=DIRECTIONS):
    threats = find_opponent_gap_fours(board, opponent, directions)
    return len(threats) >= 2


def find_fork_moves(board, opponent, directions=DIRECTIONS):
    fork_moves = []
    empty_positions = [pos for pos, value in board.items() if value == 0]

    for move in empty_positions:
        board[move] = opponent
        threats = find_opponent_gap_fours(board, opponent, directions)
        del board[move]

        if len(threats) >= 2:
            fork_moves.append(move)

    return fork_moves


def count_open_sequences(board, player, length, directions=DIRECTIONS):
    open_sequence_count = 0
    visited = set()

    for position, value in board.items():
        if value != player:
            continue

        for direction in directions:
            if (position, direction) in visited:
                continue

            dq, dr = direction
            sequence = [position]
            q, r = position

            for _ in range(length - 1):
                q += dq
                r += dr
                if board.get((q, r), 0) == player:
                    sequence.append((q, r))
                else:
                    break

            if len(sequence) == length:
                before = (position[0] - dq, position[1] - dr)
                after = (q + dq, r + dr)

                if board.get(before, 0) == 0 and board.get(after, 0) == 0:
                    open_sequence_count += 1

                    for cell in sequence:
                        visited.add((cell, direction))

    return open_sequence_count
