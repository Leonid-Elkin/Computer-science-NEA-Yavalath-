from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QSize, QRect
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPolygon,
    QFont,
    QBrush,
    QLinearGradient,
    QPen,
    QIcon,
    QGuiApplication,
)
from PyQt5.Qt import QStyle




class IconButton(QWidget):
    #Base class for all icon-style buttons - subclasses override paintEvent to draw their shape

    clicked = pyqtSignal()

    #Default and hover colors shared across all icon buttons
    normalColor = QColor(0, 150, 255)
    hoverColor = QColor(0, 200, 255)

    def __init__(self, parent=None):
        super().__init__(parent)
        #Fixed size because all icon buttons are the same dimensions
        self.setFixedSize(60, 60)

        self.isMouseHovering = False

        #Needed to receive enter/leave hover events
        self.setAttribute(Qt.WA_Hover)


    def paintEvent(self, event):
        #Placeholder - subclasses must override this to draw their icon
        return


    def enterEvent(self, event):
        #Mark hover state and repaint so the color change is visible
        self.isMouseHovering = True
        self.update()


    def leaveEvent(self, event):
        #Clear hover state and repaint to restore normal color
        self.isMouseHovering = False
        self.update()


    def mouseReleaseEvent(self, event):
        #Only emit on left click to avoid reacting to right-click or middle-click
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


    def currentColor(self):
        #Returns the appropriate color depending on whether the mouse is over the button
        if self.isMouseHovering:
            return self.hoverColor
        else:
            return self.normalColor



class PlayButton(IconButton):
    #Draws a right-pointing triangle to represent play/start

    def paintEvent(self, event):
        #Set up the painter with the current hover-aware color
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        #No outline - just the filled triangle
        painter.setPen(Qt.NoPen)

        buttonWidth = self.width()
        buttonHeight = self.height()

        #Triangle spans 30%-70% horizontally and 20%-80% vertically to stay centred
        leftX = int(buttonWidth * 0.3)
        middleX = int(buttonWidth * 0.7)

        topY = int(buttonHeight * 0.2)
        centerY = int(buttonHeight * 0.5)
        bottomY = int(buttonHeight * 0.8)

        #Three points define the triangle: top-left, middle-right, bottom-left
        pointOne = QPoint(leftX, topY)
        pointTwo = QPoint(middleX, centerY)
        pointThree = QPoint(leftX, bottomY)

        trianglePoints = QPolygon()
        trianglePoints.append(pointOne)
        trianglePoints.append(pointTwo)
        trianglePoints.append(pointThree)

        painter.drawPolygon(trianglePoints)



class PauseButton(IconButton):
    #Draws two vertical rounded bars to represent pause

    def paintEvent(self, event):
        #Set up the painter with the current hover-aware color
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        #No outline on the bars
        painter.setPen(Qt.NoPen)

        buttonWidth = self.width()
        buttonHeight = self.height()

        #Bar dimensions - kept narrow and centred to match standard pause icon proportions
        barWidth = int(buttonWidth * 0.15)
        spacingBetweenBars = int(buttonWidth * 0.1)

        barHeight = int(buttonHeight * 0.6)
        barY = int(buttonHeight * 0.2)

        firstBarX = int(buttonWidth * 0.3)

        #Second bar placed immediately after the first with the gap in between
        secondBarX = firstBarX + barWidth + spacingBetweenBars

        cornerRadiusX = 6
        cornerRadiusY = 6

        #Draw first bar on the left
        painter.drawRoundedRect(
            firstBarX,
            barY,
            barWidth,
            barHeight,
            cornerRadiusX,
            cornerRadiusY
        )

        #Draw second bar to the right of the first
        painter.drawRoundedRect(
            secondBarX,
            barY,
            barWidth,
            barHeight,
            cornerRadiusX,
            cornerRadiusY
        )


class SkipButton(IconButton):
    # Draws two triangles and a bar to represent skip forward or skip back

    def __init__(self, direction="right", parent=None):
        super().__init__(parent)
        # Direction controls whether the triangles and bar are mirrored
        self.direction = direction


    def paintEvent(self, event):
        # Set up the painter with the current hover-aware color
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        # No outline on the shapes
        painter.setPen(Qt.NoPen)

        buttonWidth = self.width()
        buttonHeight = self.height()

        # Triangle dimensions derived from button size so the icon scales properly
        triangleWidth = int(buttonWidth * 0.2)
        triangleHeight = int(buttonHeight * 0.4)

        offset = int(buttonWidth * 0.1)

        # Thin bar placed at the far end to complete the skip symbol
        barWidth = int(buttonWidth * 0.05)
        barHeight = int(buttonHeight * 0.5)
        barY = int(buttonHeight * 0.25)

        topY = int(buttonHeight * 0.3)
        centerY = int(buttonHeight * 0.5)
        bottomY = int(buttonHeight * 0.7)

        smallGap = int(offset * 0.5)
        largeGap = int(offset * 0.7)

        if self.direction == "right":

            # First triangle starts from the left edge with a small offset
            firstTriangleLeftX = offset
            firstTriangleRightX = offset + triangleWidth

            # Second triangle placed immediately after the first
            secondTriangleLeftX = firstTriangleRightX + smallGap
            secondTriangleRightX = secondTriangleLeftX + triangleWidth

            # Three points define each triangle: top-left, middle-right, bottom-left
            pointOne = QPoint(firstTriangleLeftX, topY)
            pointTwo = QPoint(firstTriangleRightX, centerY)
            pointThree = QPoint(firstTriangleLeftX, bottomY)

            firstTriangle = QPolygon()
            firstTriangle.append(pointOne)
            firstTriangle.append(pointTwo)
            firstTriangle.append(pointThree)

            pointFour = QPoint(secondTriangleLeftX, topY)
            pointFive = QPoint(secondTriangleRightX, centerY)
            pointSix = QPoint(secondTriangleLeftX, bottomY)

            secondTriangle = QPolygon()
            secondTriangle.append(pointFour)
            secondTriangle.append(pointFive)
            secondTriangle.append(pointSix)

            # Draw both triangles then the bar
            painter.drawPolygon(firstTriangle)
            painter.drawPolygon(secondTriangle)

            # Bar sits just past the second triangle tip
            barX = secondTriangleRightX + largeGap

            cornerRadiusX = 3
            cornerRadiusY = 3
            painter.drawRoundedRect(
                barX,
                barY,
                barWidth,
                barHeight,
                cornerRadiusX,
                cornerRadiusY
            )


        else:
            # Mirror of the right layout - triangles point left, bar on the left edge

            firstTriangleRightX = buttonWidth - offset
            firstTriangleLeftX = firstTriangleRightX - triangleWidth

            secondTriangleRightX = firstTriangleLeftX - smallGap
            secondTriangleLeftX = secondTriangleRightX - triangleWidth

            # Three points define each triangle: top-right, middle-left, bottom-right
            pointOne = QPoint(firstTriangleRightX, topY)
            pointTwo = QPoint(firstTriangleLeftX, centerY)
            pointThree = QPoint(firstTriangleRightX, bottomY)

            firstTriangle = QPolygon()
            firstTriangle.append(pointOne)
            firstTriangle.append(pointTwo)
            firstTriangle.append(pointThree)

            pointFour = QPoint(secondTriangleRightX, topY)
            pointFive = QPoint(secondTriangleLeftX, centerY)
            pointSix = QPoint(secondTriangleRightX, bottomY)

            secondTriangle = QPolygon()
            secondTriangle.append(pointFour)
            secondTriangle.append(pointFive)
            secondTriangle.append(pointSix)

            # Draw both triangles then the bar
            painter.drawPolygon(firstTriangle)
            painter.drawPolygon(secondTriangle)

            # Bar sits just to the left of the second triangle tip
            barX = secondTriangleLeftX - largeGap - barWidth

            cornerRadiusX = 3
            cornerRadiusY = 3
            painter.drawRoundedRect(
                barX,
                barY,
                barWidth,
                barHeight,
                cornerRadiusX,
                cornerRadiusY
            )



class TextButton(QWidget):
    # Rounded rectangle button with a text label, supporting optional checked and disabled states

    clicked = pyqtSignal()
    checkedChanged = pyqtSignal(bool)


    def __init__(
        self,
        text,
        parent=None,
        checkable=False,
        x=0,
        y=0,
        clickable=True,
        opacity=1.0
    ):
        super().__init__(parent)

        self.label = text

        self.checkable = checkable
        self.checked = False

        self.isHovering = False

        self.clickable = clickable
        self.opacity = opacity

        self.setFixedSize(160, 48)

        # Needed to receive enter/leave hover events
        self.setAttribute(Qt.WA_Hover)

        self.setMouseTracking(True)

        self.move(x, y)

        # Color scheme - dark background with cyan border and text
        self.normalBackgroundColor = QColor(0, 0, 0)
        self.hoverBackgroundColor = QColor(10, 30, 40)
        self.checkedBackgroundColor = QColor(0, 50, 70)

        self.edgeColor = QColor(0, 255, 255)
        self.textColor = QColor(0, 255, 255)

        self.borderRadius = 4

        fontSize = self.standardised(12)
        self.font = QFont("Segoe UI", fontSize, QFont.Bold)


    def text(self):
        # Returns the display label so callers can read the button text without accessing the attribute directly
        return self.label


    def setOpacity(self, opacity: float):
        # Clamp to valid range before storing
        clampedOpacity = opacity

        if clampedOpacity < 0.0:
            clampedOpacity = 0.0

        if clampedOpacity > 1.0:
            clampedOpacity = 1.0

        self.opacity = clampedOpacity

        self.update()


    def standardised(self, value):
        # Scales a value proportionally to the screen height so the UI looks consistent across resolutions
        screen = QGuiApplication.primaryScreen()

        geometry = screen.geometry()

        screenWidth = geometry.width()
        screenHeight = geometry.height()

        scaledValue = value * screenHeight / 1600

        return int(scaledValue)


    def setClickable(self, clickable: bool):

        self.clickable = clickable

        self.setEnabled(clickable)

        if clickable:
            # Clear hover state when re-enabled to avoid stale visual
            self.isHovering = False

            if self.checkable:
                if self.checked:
                    self.checked = False
                    self.checkedChanged.emit(False)

        self.update()


    def enterEvent(self, event):
        # Only show hover highlight if the button is currently interactable
        if self.clickable:
            self.isHovering = True
            self.update()


    def leaveEvent(self, event):
        # Clear the hover highlight when the cursor leaves the button area
        if self.clickable:
            self.isHovering = False
            self.update()


    def mouseReleaseEvent(self, event):

        # Ignore all clicks when the button has been disabled
        if not self.clickable:
            return

        mouseButton = event.button()

        if mouseButton == Qt.LeftButton:

            # Checkable buttons can only be checked, not unchecked by clicking
            if self.checkable:
                if not self.checked:
                    self.setChecked(True)

            self.clicked.emit()

            self.update()


    def setChecked(self, state: bool):
        # Only apply the change if the state is actually different, to avoid unnecessary repaints and signal emissions
        if self.checkable:

            if self.checked != state:

                self.checked = state

                self.checkedChanged.emit(self.checked)

                self.update()


    def currentBackgroundColor(self):
        # Priority: disabled -> checked -> hovering -> normal
        if not self.clickable:
            return self.normalBackgroundColor

        if self.checkable:
            if self.checked:
                return self.checkedBackgroundColor

        if self.isHovering:
            return self.hoverBackgroundColor

        return self.normalBackgroundColor


    def paintEvent(self, event):
        # Set up the painter ready to draw the button background and label
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        # Opacity is used to dim the button when it is not yet interactable
        painter.setOpacity(self.opacity)

        backgroundColor = self.currentBackgroundColor()

        brush = QBrush(backgroundColor)

        # Cyan border gives the button a visible boundary against dark backgrounds
        pen = QPen(self.edgeColor, 2)

        painter.setBrush(brush)
        painter.setPen(pen)

        rectangle = self.rect()

        # Draw the rounded rectangle background and border
        painter.drawRoundedRect(
            rectangle,
            self.borderRadius,
            self.borderRadius
        )

        painter.setFont(self.font)

        # Switch pen to text color before drawing the label so the border color doesn't bleed through
        painter.setPen(self.textColor)

        painter.drawText(
            rectangle,
            Qt.AlignCenter,
            self.label
        )

class ArrowButton(QPushButton):
    # Simple button that uses Qt's built-in standard arrow icons

    def __init__(self, direction="up", parent=None):

        super().__init__(parent)

        buttonSize = QSize(30, 30)
        self.setFixedSize(buttonSize)

        # Map direction strings to the corresponding Qt standard icon
        arrowMap = {}

        arrowMap["up"] = QStyle.SP_ArrowUp
        arrowMap["down"] = QStyle.SP_ArrowDown
        arrowMap["left"] = QStyle.SP_ArrowLeft
        arrowMap["right"] = QStyle.SP_ArrowRight

        directionText = direction.lower()

        # Default to up arrow if an unrecognised direction is passed
        if directionText in arrowMap:
            arrowType = arrowMap[directionText]
        else:
            arrowType = QStyle.SP_ArrowUp

        # Fetch the icon from Qt's style so it respects the system theme
        icon = self.style().standardIcon(arrowType)

        self.setIcon(icon)

        # Icon is slightly smaller than the button to leave a small margin around the edge
        iconSize = QSize(20, 20)
        self.setIconSize(iconSize)



class TickBoxButton(QWidget):
    # Checkbox-style button that draws its own tick box and label rather than using the native widget

    clicked = pyqtSignal()
    checkedChanged = pyqtSignal(bool)


    def __init__(self, parent=None, text="", checkable=True):

        super().__init__(parent)

        self.text = text
        self.checkable = checkable
        self.checked = False

        self.isHovering = False

        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)

        # Color scheme matches the rest of the UI
        self.normalBackgroundColor = QColor(0, 0, 0)
        self.hoverBackgroundColor = QColor(10, 30, 40)
        self.checkedBackgroundColor = QColor(0, 50, 70)

        self.borderColor = QColor(0, 255, 255)
        self.tickColor = QColor(0, 255, 255)
        self.textColor = QColor(0, 255, 255)

        buttonHeight = self.standardised(40)
        self.setFixedHeight(buttonHeight)

        self.boxSize = self.standardised(20)
        self.borderRadius = self.standardised(4)
        self.spacing = self.standardised(12)

        fontSize = self.standardised(12)
        self.font = QFont("Segoe UI", fontSize, QFont.Bold)

        # Width is calculated from the actual text so the widget is never wider than necessary
        fontMetrics = self.fontMetrics()

        textWidth = fontMetrics.width(self.text)

        padding = self.standardised(24)

        totalWidth = self.boxSize + self.spacing + textWidth + padding

        self.setFixedWidth(totalWidth)


    def enterEvent(self, event):
        # Show hover highlight when the mouse moves over the widget
        self.isHovering = True

        self.update()


    def leaveEvent(self, event):
        # Clear hover highlight when the mouse leaves the widget
        self.isHovering = False

        self.update()


    def mouseReleaseEvent(self, event):

        mouseButton = event.button()

        if mouseButton == Qt.LeftButton:

            # Toggle checked state on each click if the button is checkable
            if self.checkable:
                self.checked = not self.checked
                self.checkedChanged.emit(self.checked)

            self.clicked.emit()

            self.update()


    def isChecked(self):
        # Simple getter so external code doesn't need to access the attribute directly
        return self.checked


    def setChecked(self, state):
        # Only update if the state is actually changing to avoid unnecessary signal emissions
        if self.checked != state:

            self.checked = state

            self.checkedChanged.emit(self.checked)

            self.update()


    def currentBackgroundColor(self):
        # Checked state takes visual priority over hover
        if self.checked:
            return self.checkedBackgroundColor

        if self.isHovering:
            return self.hoverBackgroundColor

        return self.normalBackgroundColor


    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        # Start with no brush so the background isn't accidentally filled before the box is drawn
        painter.setBrush(Qt.NoBrush)

        widgetRect = self.rect()

        widgetWidth = self.width()
        widgetHeight = self.height()

        leftPadding = 12

        # Box sits at the left edge, inset by the padding constant
        boxX = leftPadding

        # Centre the box vertically within the widget
        verticalOffset = (widgetHeight - self.boxSize) // 2

        boxY = verticalOffset

        boxWidth = self.boxSize
        boxHeight = self.boxSize

        boxRect = QRect(boxX, boxY, boxWidth, boxHeight)

        backgroundColor = self.currentBackgroundColor()

        brush = QBrush(backgroundColor)
        pen = QPen(self.borderColor, 2)

        painter.setBrush(brush)
        painter.setPen(pen)

        # Draw the rounded checkbox square
        painter.drawRoundedRect(boxRect, self.borderRadius, self.borderRadius)

        if self.checked:

            # Draw a tick as a two-segment polyline: left-mid -> bottom-mid -> top-right
            tickPen = QPen(self.tickColor, 3)
            painter.setPen(tickPen)

            offset = 4

            pointOneX = boxRect.left() + offset
            pointOneY = boxRect.center().y()

            pointTwoX = boxRect.center().x() - offset // 2
            pointTwoY = boxRect.bottom() - offset

            pointThreeX = boxRect.right() - offset
            pointThreeY = boxRect.top() + offset

            pointOne = QPoint(pointOneX, pointOneY)
            pointTwo = QPoint(pointTwoX, pointTwoY)
            pointThree = QPoint(pointThreeX, pointThreeY)

            painter.drawPolyline(pointOne, pointTwo, pointThree)

        # Text starts after the box and the spacing gap
        textStartX = self.boxSize + self.spacing + leftPadding

        textRectWidth = widgetWidth - textStartX

        textRect = QRect(
            textStartX,
            0,
            textRectWidth,
            widgetHeight
        )

        painter.setFont(self.font)

        # Switch pen to text color so the tick color set above doesn't carry over to the label
        painter.setPen(self.textColor)

        painter.drawText(
            textRect,
            Qt.AlignVCenter,
            self.text
        )


    def standardised(self, value):
        # Scales a value proportionally to the screen height so the UI looks consistent across resolutions
        screen = QGuiApplication.primaryScreen()

        geometry = screen.geometry()

        screenHeight = geometry.height()

        scaledValue = value * screenHeight / 1600

        return int(scaledValue)