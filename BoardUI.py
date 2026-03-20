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

        default_colors = {
            "player1": QColor("red"),
            "player2": QColor("blue"),
            "empty": QColor("white"),
            "border": Qt.black,
            "selected1": QColor("green"),
            "selected2": QColor("green")
        }
        self.colors = colors if colors else default_colors

        board_width = int(self.hex_width * (controller.side + 0.5))
        board_height = int(self.hex_height * (controller.side + 0.5))
        self.setMinimumSize(board_width, board_height)

        if hasattr(self.controller, "moveMade"):
            self.controller.moveMade.connect(self.update)

        self.selected_piece = None
        self.hovered_hex = None
        self.setMouseTracking(True)

    # Coordinate transforms
    def screen_to_board(self, sx, sy):
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        px = sx - cx
        py = sy - cy
        angle = math.radians(-30)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        bx = px * cos_a - py * sin_a
        by = px * sin_a + py * cos_a
        return bx, by


    def pixel_to_hex(self, x, y, center_x=0, center_y=0):
        px = x - center_x
        py = y - center_y
        q = (4/3 * px) / self.hex_width
        r = (py / self.hex_height) - (q / 2)
        return self.hex_round(q, r)


    def hex_to_pixel(self, q, r, center_x=0, center_y=0):
        x = self.hex_width * (3/4 * q)
        y = self.hex_height * (r + q / 2)
        return center_x + x, center_y + y


    def hex_round(self, q, r):
        x = q
        z = r
        y = -x - z
        rx = round(x)
        ry = round(y)
        rz = round(z)
        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        else:
            rz = -rx - ry
        return (rx, rz)

    # Painting
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() // 2, self.height() // 2)
        painter.rotate(30)

        last_move = None
        if hasattr(self.controller, "game_state") and getattr(self.controller.game_state, "move_history", None):
            last_move = self.controller.game_state.move_history[-1] if self.controller.game_state.move_history else None
        terminal_line = getattr(self.controller, "winning_line", [])

        for (q, r), value in self.controller.game_state.board.items():
            x, y = self.hex_to_pixel(q, r, 0, 0)
            is_last = (q, r) == last_move
            selected = (self.selected_piece == (q, r))
            self.draw_hex(painter, x, y, value, is_last, selected)

        # Darken hovered empty hex
        if self.hovered_hex and self.hovered_hex in self.controller.game_state.board:
            value = self.controller.game_state.board.get(self.hovered_hex, 0)
            if value == 0 or (self.selected_piece and self.is_adjacent(self.selected_piece, self.hovered_hex)):
                x, y = self.hex_to_pixel(*self.hovered_hex, 0, 0)
                painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
                painter.setPen(Qt.NoPen)
                pts = []
                for i in range(6):
                    angle_rad = math.radians(60 * i)
                    px = x + self.radius * math.cos(angle_rad)
                    py = y + self.radius * math.sin(angle_rad)
                    pts.append(QPointF(px, py))
                painter.drawPolygon(QPolygonF(pts))

        # Draw arrow between selected piece and hovered hex
        if self.selected_piece and self.hovered_hex and self.is_adjacent(self.selected_piece, self.hovered_hex):
            start_x, start_y = self.hex_to_pixel(*self.selected_piece, 0, 0)
            end_x, end_y = self.hex_to_pixel(*self.hovered_hex, 0, 0)
            self.draw_arrow(painter, QPointF(start_x, start_y), QPointF(end_x, end_y))

        # Draw winning line
        if getattr(self.controller, "game_over", False) and terminal_line and len(terminal_line) >= 2:
            pen = QPen(QColor("red"), max(1, self.standardised(4)))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            points = [QPointF(*self.hex_to_pixel(pos[0], pos[1], 0, 0)) for pos in terminal_line]
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

    def draw_hex(self, painter, x, y, value, is_last_move=False, selected=False):
        pen = QPen(self.colors.get("border", Qt.black), max(1, self.standardised(1)))
        painter.setPen(pen)
        if value == 1:
            base_color = self.colors.get("player1", QColor("red"))
        elif value == 2:
            base_color = self.colors.get("player2", QColor("blue"))
        else:
            base_color = self.colors.get("empty", QColor("white"))
        fill_color = self.colors.get("selected", QColor("green")) if selected else base_color
        painter.setBrush(QBrush(fill_color))
        pts = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            px = x + self.radius * math.cos(angle_rad)
            py = y + self.radius * math.sin(angle_rad)
            pts.append(QPointF(px, py))
        painter.drawPolygon(QPolygonF(pts))
        if is_last_move:
            circle_radius = self.radius / 4.0
            painter.setBrush(QBrush(QColor("gray")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(x, y), circle_radius, circle_radius)

    def draw_arrow(self, painter, start_point, end_point):
        """Draw an arrow from start_point to end_point"""
        pen = QPen(QColor("black"), max(1, self.standardised(3)))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor("black")))
        
        # Calculate line vector
        line_vec = end_point - start_point
        length = math.hypot(line_vec.x(), line_vec.y())
        if length == 0:
            return
        
        # Normalize
        unit_x = line_vec.x() / length
        unit_y = line_vec.y() / length
        
        # Shorten the line slightly so arrow doesn't overlap hex centers
        margin = self.radius * 0.3
        adjusted_start = QPointF(
            start_point.x() + unit_x * margin,
            start_point.y() + unit_y * margin
        )
        adjusted_end = QPointF(
            end_point.x() - unit_x * margin,
            end_point.y() - unit_y * margin
        )
        
        # Draw main line
        painter.drawLine(adjusted_start, adjusted_end)
        
        # Draw arrowhead at the end
        arrow_size = max(8, int(self.radius * 0.4))
        perp_x, perp_y = -unit_y, unit_x
        
        p1 = adjusted_end
        p2 = QPointF(
            adjusted_end.x() - unit_x * arrow_size + perp_x * (arrow_size / 2.0),
            adjusted_end.y() - unit_y * arrow_size + perp_y * (arrow_size / 2.0)
        )
        p3 = QPointF(
            adjusted_end.x() - unit_x * arrow_size - perp_x * (arrow_size / 2.0),
            adjusted_end.y() - unit_y * arrow_size - perp_y * (arrow_size / 2.0)
        )
        
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        path.closeSubpath()
        painter.drawPath(path)

    # Interaction
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        bx, by = self.screen_to_board(event.pos().x(), event.pos().y())
        q, r = self.pixel_to_hex(bx, by, 0, 0)
        value = self.controller.game_state.board.get((q, r), 0)

        if self.selected_piece is None:
            if value == self.controller.current_player:
                self.selected_piece = (q, r)  # select for movement
            elif value == 0:
                self.controller.make_human_move((q, r))  # place new piece
        else:
            # Attempt move to adjacent empty hex
            if value == 0 and self.is_adjacent(self.selected_piece, (q, r)):
                self.controller.make_human_move((q, r), from_pos=self.selected_piece)
            self.selected_piece = None  # deselect after move
        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.selected_piece:
            # Get mouse position in board coordinates (after rotation)
            bx, by = self.screen_to_board(event.pos().x(), event.pos().y())
            
            # Get the selected piece position in board coordinates
            start_x, start_y = self.hex_to_pixel(*self.selected_piece, 0, 0)

            # Mouse vector relative to selected hex (board coords)
            dx = bx - start_x
            dy = by - start_y

            # Normalize mouse vector
            length = math.hypot(dx, dy)
            if length == 0:
                self.hovered_hex = None
                self.update()
                return
            dx /= length
            dy /= length

            # Find neighbor most aligned with mouse direction
            best_neighbor = None
            best_cos = -2  # smaller than minimum possible cosine (-1)
            for dq, dr in [(1, 0), (0, 1), (-1, 1),
                        (-1, 0), (0, -1), (1, -1)]:
                neighbor_pos = (self.selected_piece[0] + dq, self.selected_piece[1] + dr)
                if neighbor_pos not in self.controller.game_state.board:
                    continue
                    
                nx, ny = self.hex_to_pixel(neighbor_pos[0], neighbor_pos[1], 0, 0)
                vnx = nx - start_x
                vny = ny - start_y

                # Normalize neighbor vector
                nlen = math.hypot(vnx, vny)
                if nlen == 0:
                    continue
                vnx /= nlen
                vny /= nlen

                # Cosine similarity (angle closeness)
                cos_sim = dx * vnx + dy * vny
                if cos_sim > best_cos:
                    best_cos = cos_sim
                    best_neighbor = neighbor_pos

            # Only accept if reasonably aligned (threshold 0.5)
            if best_neighbor and best_cos > 0.5:
                self.hovered_hex = best_neighbor
            else:
                self.hovered_hex = None
        else:
            # fallback hover for placement
            bx, by = self.screen_to_board(event.pos().x(), event.pos().y())
            q, r = self.pixel_to_hex(bx, by, 0, 0)
            if (q, r) in self.controller.game_state.board:
                value = self.controller.game_state.board.get((q, r), 0)
                self.hovered_hex = (q, r) if value == 0 else None
            else:
                self.hovered_hex = None

        self.update()
        super().mouseMoveEvent(event)



    def is_adjacent(self, a, b):
        aq, ar = a
        bq, br = b
        neighbors = [(1, 0), (0, 1), (-1, 1),
                     (-1, 0), (0, -1), (1, -1)]
        return (bq - aq, br - ar) in neighbors

    def standardised(self, value):
        screen = QGuiApplication.primaryScreen()
        geometry = screen.geometry()
        return int(value * geometry.height() / 1600)