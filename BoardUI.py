import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF


class BoardGraphics(QWidget):
    #Responsible for rendering the hex board and handling all mouse interaction with it

    def __init__(self, controller, radius=30, colors=None, parent=None):
        super().__init__(parent)

        #Store a reference to the game controller so the board can read state and trigger moves
        self.controller = controller
        self.radius = radius

        #Pre-compute hex dimensions from the radius to avoid recalculating them every paint
        self.hexHeight = math.sqrt(3) * self.radius
        self.hexWidth = 2 * self.radius
        self.hexSpacing = 2

        #Winning line is stored here after the game ends so paintEvent can draw it
        self.winningLine = []

        #Recent move messages are displayed in the corner as a short move history
        self.recentMoveMessages = []

        #Hover tracking - stores the axial coords of whichever hex the mouse is over
        self.hoveredHexCoords = None
        self.hoverHighlightEnabled = True

        #Fall back to a basic color scheme if none was provided by the caller
        defaultColors = {
            "player1": QColor("red"),
            "player2": QColor("blue"),
            "empty": QColor("white"),
            "border": Qt.black,
            "hover": QColor(255, 255, 200, 80)
        }

        self.colors = colors if colors else defaultColors

        #Set the minimum widget size based on how many hexes fit across the board
        boardWidth = int(self.hexWidth * (controller.side + 0.5))
        boardHeight = int(self.hexHeight * (controller.side + 0.5))
        self.setMinimumSize(boardWidth, boardHeight)

        #Repaint whenever the controller signals that a move has been made
        self.controller.moveMade.connect(self.update)

        #Mouse tracking must be enabled explicitly for mouseMoveEvent to fire without a button held
        self.setMouseTracking(True)


    def toggleHover(self, enable: bool):
        #Allows the caller to disable hover highlighting, for example during AI turns
        self.hoverHighlightEnabled = enable
        self.hoveredHexCoords = None
        self.update()


    def mouseMoveEvent(self, event):
        #Update the hovered hex as the mouse moves across the board

        if not self.hoverHighlightEnabled:
            return

        #Convert the mouse position to coordinates relative to the board centre
        boardCenterX = self.width() // 2
        boardCenterY = self.height() // 2

        relativeX = event.x() - boardCenterX
        relativeY = event.y() - boardCenterY

        #The board is drawn rotated 30 degrees so we un-rotate the mouse position
        #before doing the pixel-to-hex conversion
        rotationAngle = math.radians(-30)

        rotatedX = (
            relativeX * math.cos(rotationAngle) - relativeY * math.sin(rotationAngle))

        rotatedY = (
            relativeX * math.sin(rotationAngle) + relativeY * math.cos(rotationAngle))

        hoveredHexCoords = self.pixelToHex(rotatedX, rotatedY, 0, 0)

        #Only highlight the hex if it is empty - occupied hexes don't get a hover color
        if self.controller.game_state.board.get(hoveredHexCoords, 0) == 0:
            if self.hoveredHexCoords != hoveredHexCoords:
                #Hex has changed, store the new one and repaint
                self.hoveredHexCoords = hoveredHexCoords
                self.update()
        else:
            if self.hoveredHexCoords is not None:
                #Mouse moved onto an occupied hex so clear the highlight
                self.hoveredHexCoords = None
                self.update()


    def leaveEvent(self, event):
        #Clear the hover highlight when the mouse leaves the widget entirely
        if self.hoveredHexCoords is not None:
            self.hoveredHexCoords = None
            self.update()


    def mousePressEvent(self, event):
        #Handle a human player clicking a hex to place a piece

        #Ignore clicks when not in a human-playable mode or when the game has ended
        if self.controller.mode not in ("human", "ai") or self.controller.game_over:
            return

        #In AI mode, only accept clicks when it is the human player's turn
        if (
            self.controller.mode == "ai"
            and self.controller.current_player != self.controller.human_player
        ):
            return

        #Convert the click position to coordinates relative to the board centre
        boardCenterX = self.width() // 2
        boardCenterY = self.height() // 2

        relativeX = event.x() - boardCenterX
        relativeY = event.y() - boardCenterY

        #Un-rotate the click position to match the un-rotated hex grid
        rotationAngle = math.radians(-30)

        rotatedX = (
            relativeX * math.cos(rotationAngle)
            - relativeY * math.sin(rotationAngle)
        )

        rotatedY = (
            relativeX * math.sin(rotationAngle)
            + relativeY * math.cos(rotationAngle)
        )

        #Convert the pixel position to axial hex coordinates
        clickedHexCoords = self.pixelToHex(rotatedX, rotatedY, 0, 0)

        #Pass the chosen hex to the controller to validate and apply the move
        self.controller.make_human_move(clickedHexCoords)


    def reset(self):
        #Clear the move history display when a new game starts
        self.recentMoveMessages = []


    def addMoveMessage(self, message):
        #Add a message to the recent move log shown in the corner of the board
        self.recentMoveMessages.append(message)

        #Keep the log short so it doesn't overflow the board widget
        if len(self.recentMoveMessages) > 5:
            self.recentMoveMessages.pop(0)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        #Draw the recent move messages in the top-left corner before applying any transforms
        painter.setFont(QFont("Arial", 12))

        textOffsetY = 60
        for message in self.recentMoveMessages:
            painter.drawText(10, textOffsetY, message)
            textOffsetY += 20

        #Translate to the centre of the widget so all hex positions are relative to the middle
        painter.translate(self.width() // 2, self.height() // 2)

        #Rotate the entire board 30 degrees so flat-top hexes appear point-top
        painter.rotate(30)

        #Find the most recent move so it can be marked with a dot
        lastMoveCoords = (
            self.controller.game_state.move_history[-1]
            if self.controller.game_state.move_history
            else None
        )

        #Fetch the winning line if the game has ended with a winner
        terminalWinningLine = self.controller.game_state.get_winning_line()

        #Draw every hex on the board using its stored cell value to determine color
        for (q, r), cellValue in self.controller.game_state.board.items():
            pixelX, pixelY = self.hexToPixel(q, r, 0, 0)

            self.drawHex(
                painter,
                pixelX,
                pixelY,
                cellValue,
                (q, r) == lastMoveCoords
            )

        #Draw the winning line on top of the hex grid once the game is over
        if (
            self.controller.game_over
            and terminalWinningLine
            and len(terminalWinningLine) >= 2
        ):
            winningPen = QPen(QColor("red"), 4)
            winningPen.setCapStyle(Qt.RoundCap)
            painter.setPen(winningPen)

            #Convert each winning hex to a pixel position then connect them with lines
            linePoints = []

            for q, r in terminalWinningLine:
                pointX, pointY = self.hexToPixel(q, r, 0, 0)
                linePoints.append(QPointF(pointX, pointY))

            for i in range(len(linePoints) - 1):
                painter.drawLine(linePoints[i], linePoints[i + 1])


    def hexToPixel(self, q, r, offsetX, offsetY):
        #Convert axial hex coordinates to pixel coordinates using standard flat-top hex math
        pixelX = self.radius * 3 / 2 * q
        pixelY = self.hexHeight * (r + q / 2)

        return offsetX + pixelX, offsetY + pixelY


    def pixelToHex(self, pixelX, pixelY, offsetX, offsetY):
        #Convert a pixel position back to axial hex coordinates
        adjustedX = pixelX - offsetX
        adjustedY = pixelY - offsetY

        #Inverse of the hexToPixel formula
        q = (2 / 3 * adjustedX) / self.radius
        r = (
            (-1 / 3 * adjustedX + math.sqrt(3) / 3 * adjustedY)
            / self.radius
        )

        #Round to the nearest valid hex coordinate
        return self.hexRound(q, r)


    def hexRound(self, fractionalQ, fractionalR):
        #Round fractional axial coordinates to the nearest hex using cube coordinate rounding

        #Convert axial to cube coordinates - the third axis s is derived from q and r
        fractionalX = fractionalQ
        fractionalZ = fractionalR
        fractionalY = -fractionalX - fractionalZ

        #Round all three cube axes independently
        roundedX = round(fractionalX)
        roundedY = round(fractionalY)
        roundedZ = round(fractionalZ)

        #Calculate how much each axis was adjusted by rounding
        diffX = abs(roundedX - fractionalX)
        diffY = abs(roundedY - fractionalY)
        diffZ = abs(roundedZ - fractionalZ)

        #The axis with the largest rounding error is recomputed from the other two
        #to ensure the cube constraint x + y + z = 0 is preserved
        if diffX > diffY and diffX > diffZ:
            roundedX = -roundedY - roundedZ
        elif diffY > diffZ:
            roundedY = -roundedX - roundedZ
        else:
            roundedZ = -roundedX - roundedY

        #Return only the q and r axes since the board uses axial coordinates
        return roundedX, roundedZ


    def drawHex(self, painter, centerX, centerY, cellValue, isLastMove=False):
        #Draw a single hexagon at the given pixel position with the appropriate color

        #All hex vertices are 60 degrees apart
        sideAngleDegrees = 60

        #Border color is the same for all hexes
        painter.setPen(QPen(self.colors.get("border", Qt.black), 2))

        #Choose the fill color based on which player occupies the cell, or hover state if empty
        if cellValue == 1:
            painter.setBrush(QBrush(self.colors.get("player1", QColor("red"))))

        elif cellValue == 2:
            painter.setBrush(QBrush(self.colors.get("player2", QColor("blue"))))

        else:
            #Cell is empty - show a hover highlight if the mouse is over this hex
            if (
                self.hoverHighlightEnabled
                and self.hoveredHexCoords
                and (centerX, centerY)
                == self.hexToPixel(*self.hoveredHexCoords, 0, 0)
            ):
                painter.setBrush(
                    QBrush(self.colors.get("hover", QColor(255, 255, 200, 80)))
                )
            else:
                painter.setBrush(
                    QBrush(self.colors.get("empty", QColor("white")))
                )

        #Build the six vertices of the hexagon by stepping around the centre point
        hexPoints = []

        for i in range(6):
            sideAngleRadians = math.radians(sideAngleDegrees * i)

            vertexX = centerX + self.radius * math.cos(sideAngleRadians)
            vertexY = centerY + self.radius * math.sin(sideAngleRadians)

            hexPoints.append(QPointF(vertexX, vertexY))

        painter.drawPolygon(QPolygonF(hexPoints))

        #Draw a small grey dot at the centre of the most recently played hex
        if isLastMove:
            markerRadius = self.radius / 4

            painter.setBrush(QBrush(QColor("gray")))
            painter.setPen(Qt.NoPen)

            painter.drawEllipse(
                QPointF(centerX, centerY),
                markerRadius,
                markerRadius
            )


    def update(self):
        #Sync the local winning line cache from the controller then trigger a repaint
        self.winningLine = getattr(self.controller, "winningLine", [])
        super().update()