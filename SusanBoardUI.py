import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPolygonF, QPainterPath, QGuiApplication
from PyQt5.QtCore import Qt, QPointF


class BoardGraphics(QWidget):
    def __init__(self, controller, radius=30, colors=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.radius = radius
        self.hex_height = math.sqrt(3) * self.radius
        self.hex_width = 2 * self.radius

        defaultColors = {
            "player1":  QColor("red"),
            "player2":  QColor("blue"),
            "empty":    QColor("white"),
            "border":   Qt.black,
            "selected1": QColor("green"),
            "selected2": QColor("green")
        }
        self.colors = colors if colors else defaultColors

        #Set minimum widget size based on board dimensions
        boardWidth  = int(self.hex_width  * (controller.side + 0.5))
        boardHeight = int(self.hex_height * (controller.side + 0.5))
        self.setMinimumSize(boardWidth, boardHeight)

        #Update board graphics every time a move is made
        if hasattr(self.controller, "moveMade"):
            self.controller.moveMade.connect(self.update)

        self.selected_piece = None
        self.hovered_hex = None
        self.setMouseTracking(True)

    # --- Coordinate transforms ---

    def screen_to_board(self, sx, sy):
        """
        Converts a raw screen position to board-space coordinates by translating
        to the widget centre and then rotating by -30 degrees to undo the painter rotation.
        """
        cx = self.width()  / 2.0
        cy = self.height() / 2.0
        px = sx - cx
        py = sy - cy
        angle = math.radians(-30)
        cosA = math.cos(angle)
        sinA = math.sin(angle)
        bx = px * cosA - py * sinA
        by = px * sinA + py * cosA
        return bx, by

    def pixel_to_hex(self, x, y, center_x=0, center_y=0):
        #Converts a pixel position to fractional axial hex coordinates, then rounds
        px = x - center_x
        py = y - center_y
        q = (4 / 3 * px) / self.hex_width
        r = (py / self.hex_height) - (q / 2)
        return self.hex_round(q, r)

    def hex_to_pixel(self, q, r, center_x=0, center_y=0):
        #Converts axial hex coordinates to pixel coordinates relative to the given centre
        x = self.hex_width  * (3 / 4 * q)
        y = self.hex_height * (r + q / 2)
        return center_x + x, center_y + y

    def hex_round(self, q, r):
        """
        Rounds fractional axial coordinates to the nearest valid hex cell using
        cube coordinate rounding. Ensures the axis with the largest rounding error
        is recalculated from the other two to maintain the cube constraint x+y+z=0.
        """
        x = q
        z = r
        y = -x - z
        rx = round(x)
        ry = round(y)
        rz = round(z)
        xDiff = abs(rx - x)
        yDiff = abs(ry - y)
        zDiff = abs(rz - z)
        if xDiff > yDiff and xDiff > zDiff:
            rx = -ry - rz
        elif yDiff > zDiff:
            ry = -rx - rz
        else:
            rz = -rx - ry
        return (rx, rz)

    # --- Painting ---

    def paintEvent(self, event):
        """
        Main paint handler. Translates and rotates the painter to align the hex grid,
        then draws each cell, the hover overlay, the movement arrow, and the winning line.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() // 2, self.height() // 2)
        painter.rotate(30)

        #Retrieve the last move and winning line from the controller
        lastMove = None
        if hasattr(self.controller, "game_state") and getattr(self.controller.game_state, "move_history", None):
            lastMove = self.controller.game_state.move_history[-1] if self.controller.game_state.move_history else None
        terminalLine = getattr(self.controller, "winning_line", [])

        #Draw all board cells
        for (q, r), value in self.controller.game_state.board.items():
            x, y = self.hex_to_pixel(q, r, 0, 0)
            isLast   = (q, r) == lastMove
            selected = (self.selected_piece == (q, r))
            self.draw_hex(painter, x, y, value, isLast, selected)

        #Darken the hovered empty cell to indicate a valid placement target
        if self.hovered_hex and self.hovered_hex in self.controller.game_state.board:
            value = self.controller.game_state.board.get(self.hovered_hex, 0)
            if value == 0 or (self.selected_piece and self.is_adjacent(self.selected_piece, self.hovered_hex)):
                x, y = self.hex_to_pixel(*self.hovered_hex, 0, 0)
                painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
                painter.setPen(Qt.NoPen)
                pts = []
                for i in range(6):
                    angleRad = math.radians(60 * i)
                    px = x + self.radius * math.cos(angleRad)
                    py = y + self.radius * math.sin(angleRad)
                    pts.append(QPointF(px, py))
                painter.drawPolygon(QPolygonF(pts))

        #Draw movement arrow between the selected piece and the hovered adjacent cell
        if self.selected_piece and self.hovered_hex and self.is_adjacent(self.selected_piece, self.hovered_hex):
            startX, startY = self.hex_to_pixel(*self.selected_piece, 0, 0)
            endX,   endY   = self.hex_to_pixel(*self.hovered_hex,    0, 0)
            self.draw_arrow(painter, QPointF(startX, startY), QPointF(endX, endY))

        #Draw the winning line overlay when the game has ended
        if getattr(self.controller, "game_over", False) and terminalLine and len(terminalLine) >= 2:
            pen = QPen(QColor("red"), max(1, self.standardised(4)))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            points = [QPointF(*self.hex_to_pixel(pos[0], pos[1], 0, 0)) for pos in terminalLine]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

    def draw_hex(self, painter, x, y, value, is_last_move=False, selected=False):
        """
        Draws a single hexagonal cell at pixel position (x, y).
        Fills with the appropriate player colour or the empty colour,
        and draws a small grey circle at the centre if this was the last move made.
        """
        pen = QPen(self.colors.get("border", Qt.black), max(1, self.standardised(1)))
        painter.setPen(pen)

        #Choose fill colour based on occupant and selection state
        if value == 1:
            baseColor = self.colors.get("player1", QColor("red"))
        elif value == 2:
            baseColor = self.colors.get("player2", QColor("blue"))
        else:
            baseColor = self.colors.get("empty", QColor("white"))

        fillColor = self.colors.get("selected", QColor("green")) if selected else baseColor
        painter.setBrush(QBrush(fillColor))

        #Build and draw the six-sided polygon
        pts = []
        for i in range(6):
            angleRad = math.radians(60 * i)
            px = x + self.radius * math.cos(angleRad)
            py = y + self.radius * math.sin(angleRad)
            pts.append(QPointF(px, py))
        painter.drawPolygon(QPolygonF(pts))

        #Last-move marker: small grey dot at the cell centre
        if is_last_move:
            circleRadius = self.radius / 4.0
            painter.setBrush(QBrush(QColor("gray")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), circleRadius, circleRadius)

    def draw_arrow(self, painter, start_point, end_point):
        """
        Draws a directional arrow from start_point to end_point.
        The line is shortened at both ends by a margin so it does not overlap
        the hex centres. An arrowhead triangle is drawn at the destination.
        """
        pen = QPen(QColor("black"), max(1, self.standardised(3)))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("black")))

        #Calculate the unit direction vector
        lineVec = end_point - start_point
        length  = math.hypot(lineVec.x(), lineVec.y())
        if length == 0:
            return

        unitX = lineVec.x() / length
        unitY = lineVec.y() / length

        #Shorten both ends so the arrow does not overlap the hex centres
        margin = self.radius * 0.3
        adjustedStart = QPointF(
            start_point.x() + unitX * margin,
            start_point.y() + unitY * margin
        )
        adjustedEnd = QPointF(
            end_point.x() - unitX * margin,
            end_point.y() - unitY * margin
        )

        #Draw the shaft
        painter.drawLine(adjustedStart, adjustedEnd)

        #Build and draw the arrowhead triangle
        arrowSize = max(8, int(self.radius * 0.4))
        perpX, perpY = -unitY, unitX

        p1 = adjustedEnd
        p2 = QPointF(
            adjustedEnd.x() - unitX * arrowSize + perpX * (arrowSize / 2.0),
            adjustedEnd.y() - unitY * arrowSize + perpY * (arrowSize / 2.0)
        )
        p3 = QPointF(
            adjustedEnd.x() - unitX * arrowSize - perpX * (arrowSize / 2.0),
            adjustedEnd.y() - unitY * arrowSize - perpY * (arrowSize / 2.0)
        )

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()
        painter.drawPath(path)

    # --- Interaction ---

    def mousePressEvent(self, event):
        """
        Handles left-click input. If no piece is selected, clicking an own piece
        selects it for movement; clicking an empty cell places a new piece.
        If a piece is already selected, clicking an adjacent empty cell moves it there.
        """
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        bx, by = self.screen_to_board(event.pos().x(), event.pos().y())
        q, r   = self.pixel_to_hex(bx, by, 0, 0)
        value  = self.controller.game_state.board.get((q, r), 0)

        if self.selected_piece is None:
            if value == self.controller.current_player:
                #Select this piece for movement
                self.selected_piece = (q, r)
            elif value == 0:
                #Place a new piece on the empty cell
                self.controller.make_human_move((q, r))
        else:
            #Attempt to move the selected piece to an adjacent empty cell
            if value == 0 and self.is_adjacent(self.selected_piece, (q, r)):
                self.controller.make_human_move((q, r), from_pos=self.selected_piece)
            #Deselect regardless of whether the move succeeded
            self.selected_piece = None

        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Updates the hovered cell for visual feedback. When a piece is selected,
        finds the neighbour most aligned with the mouse direction using cosine similarity.
        When no piece is selected, highlights the empty cell under the cursor.
        """
        if self.selected_piece:
            bx, by   = self.screen_to_board(event.pos().x(), event.pos().y())
            startX, startY = self.hex_to_pixel(*self.selected_piece, 0, 0)

            #Mouse vector relative to the selected hex in board coordinates
            dx = bx - startX
            dy = by - startY

            length = math.hypot(dx, dy)
            if length == 0:
                self.hovered_hex = None
                self.update()
                return

            #Normalise mouse direction vector
            dx /= length
            dy /= length

            #Find the neighbour whose direction best matches the mouse vector
            bestNeighbor = None
            bestCos = -2  #Below minimum possible cosine (-1)

            for dq, dr in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]:
                neighborPos = (self.selected_piece[0] + dq, self.selected_piece[1] + dr)
                if neighborPos not in self.controller.game_state.board:
                    continue

                nx, ny = self.hex_to_pixel(neighborPos[0], neighborPos[1], 0, 0)
                vnx = nx - startX
                vny = ny - startY

                #Normalise the neighbour direction vector
                nLen = math.hypot(vnx, vny)
                if nLen == 0:
                    continue
                vnx /= nLen
                vny /= nLen

                #Cosine similarity measures alignment between mouse and neighbour directions
                cosSim = dx * vnx + dy * vny
                if cosSim > bestCos:
                    bestCos = cosSim
                    bestNeighbor = neighborPos

            #Only highlight if the mouse is reasonably aligned with the neighbour direction
            self.hovered_hex = bestNeighbor if (bestNeighbor and bestCos > 0.5) else None

        else:
            #Fallback hover for placement: highlight the empty cell under the cursor
            bx, by = self.screen_to_board(event.pos().x(), event.pos().y())
            q, r   = self.pixel_to_hex(bx, by, 0, 0)
            if (q, r) in self.controller.game_state.board:
                value = self.controller.game_state.board.get((q, r), 0)
                self.hovered_hex = (q, r) if value == 0 else None
            else:
                self.hovered_hex = None

        self.update()
        super().mouseMoveEvent(event)

    def is_adjacent(self, a, b):
        #Returns True if b is exactly one hex step away from a in any axial direction
        aq, ar = a
        bq, br = b
        return (bq - aq, br - ar) in [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

    def standardised(self, value):
        #Scales a pixel value proportionally to the primary screen height for DPI consistency
        screen   = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        return int(value * geometry.height() / 1600)