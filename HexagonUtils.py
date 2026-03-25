DIRECTIONS = [
    (1, 0), (0, 1), (-1, 1),
    (-1, 0), (0, -1), (1, -1)
]


def hex_distance(a, b):
    # Calculates the axial distance between two points in the hexagon
    q1, r1 = a
    q2, r2 = b
    s1 = -q1 - r1
    s2 = -q2 - r2
    return max(abs(q1 - q2), abs(r1 - r2), abs(s1 - s2))


def count_consecutive(board, pos, player, target_length, directions=DIRECTIONS):
    """
    Counts the amount of consecutive patterns of given length.
    Accepts the board array.
    """
    count = 0

    # Considers all 6 directions from the picked hexagon
    for dq, dr in directions:
        totalLength = 1

        # Sees how much it can go in each direction without a color change
        for directionSign in [1, -1]:
            q, r = pos

            while True:
                q += directionSign * dq
                r += directionSign * dr

                if board.get((q, r), 0) == player:
                    totalLength += 1
                else:
                    break

        # If that length is the same as the target then add 1 to the count
        if totalLength >= target_length:
            count += 1

    return count


def is_winning_move(board, pos, player, directions=DIRECTIONS):
    """
    Yavalath-specific method that simply checks if there is a four in a row
    pattern and if so deletes the object and returns True.
    """
    board[pos] = player
    winningLines = count_consecutive(board, pos, player, 4, directions)
    del board[pos]
    return winningLines > 0


def creates_three_in_a_row(board, pos, player, directions=DIRECTIONS):
    """
    Yavalath-specific method that simply checks if there is a three in a row
    pattern and if so deletes the object and returns True.
    """
    board[pos] = player
    hasThree = count_consecutive(board, pos, player, 3, directions)
    del board[pos]
    return hasThree > 0


def find_opponent_gap_fours(board, opponent, directions=DIRECTIONS):
    """
    Method used in the minimax evaluation function that checks if a potential
    4 in a row is possible next move. This method specifically detects if there
    is an imminent lose threat. Stores threats in a list in the format
    (empty cell, full line).
    """
    threats = []
    visited = set()  # Keeps track of already visited areas

    # Iterate over every opponent piece
    for position, value in board.items():
        if value != opponent:
            continue

        # Don't check already visited areas
        for dq, dr in directions:
            if (position, dq, dr) in visited:
                continue

            # Build a line in this direction
            line = [position]
            q, r = position

            # Extend line to length 4
            for i in range(4):
                q += dq
                r += dr
                line.append((q, r))

            # See how many opponent stones are on the line
            opponentStones = [p for p in line if board.get(p) == opponent]

            # See how many empty cells are on the line
            emptyCells = [p for p in line if board.get(p) == 0]

            # If exactly 4 opponent stones and 1 empty cell, there is a gap threat
            if len(opponentStones) == 4 and len(emptyCells) == 1:
                threats.append((emptyCells[0], line))

            for p in line:
                visited.add((p, dq, dr))

    # Return details about every threat
    return threats


def count_open_sequences(board, player, length, directions=DIRECTIONS):
    """
    Counts the number of open sequences of a given length for a player.
    An open sequence has empty cells on both ends, meaning it can still be extended.
    """
    openSequenceCount = 0
    visited = set()  #Keeps track of already visited sequences

    #Iterate over every player piece
    for position, value in board.items():
        if value != player:
            continue

        #Consider all 6 directions
        for direction in directions:
            if (position, direction) in visited:
                continue

            dq, dr = direction

            #Build a sequence in this direction
            sequence = [position]
            q, r = position

            # Extend sequence to the target length
            for _ in range(length - 1):
                q += dq
                r += dr

                if board.get((q, r), 0) == player:
                    sequence.append((q, r))
                else:
                    break

            #Only count if the sequence reaches the target length
            if len(sequence) == length:
                beforeCell = (position[0] - dq, position[1] - dr)
                afterCell = (q + dq, r + dr)

                #Check both ends are open (empty), meaning the sequence can still grow
                if board.get(beforeCell, 0) == 0 and board.get(afterCell, 0) == 0:
                    openSequenceCount += 1

                    #Mark all cells in this sequence as visited to avoid double counting
                    for cell in sequence:
                        visited.add((cell, direction))

    return openSequenceCount

