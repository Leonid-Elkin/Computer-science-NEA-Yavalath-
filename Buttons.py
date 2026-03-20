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

    clicked = pyqtSignal()

    normalColor = QColor(0, 150, 255)
    hoverColor = QColor(0, 200, 255)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(60, 60)

        self.isMouseHovering = False

        self.setAttribute(Qt.WA_Hover)


    def paintEvent(self, event):
        return


    def enterEvent(self, event):
        self.isMouseHovering = True
        self.update()


    def leaveEvent(self, event):
        self.isMouseHovering = False
        self.update()


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


    def currentColor(self):
        if self.isMouseHovering:
            return self.hoverColor
        else:
            return self.normalColor



class PlayButton(IconButton):

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        painter.setPen(Qt.NoPen)


        buttonWidth = self.width()
        buttonHeight = self.height()


        leftX = int(buttonWidth * 0.3)
        middleX = int(buttonWidth * 0.7)

        topY = int(buttonHeight * 0.2)
        centerY = int(buttonHeight * 0.5)
        bottomY = int(buttonHeight * 0.8)


        pointOne = QPoint(leftX, topY)
        pointTwo = QPoint(middleX, centerY)
        pointThree = QPoint(leftX, bottomY)


        trianglePoints = QPolygon()
        trianglePoints.append(pointOne)
        trianglePoints.append(pointTwo)
        trianglePoints.append(pointThree)


        painter.drawPolygon(trianglePoints)



class PauseButton(IconButton):

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        painter.setPen(Qt.NoPen)


        buttonWidth = self.width()
        buttonHeight = self.height()


        barWidth = int(buttonWidth * 0.15)
        spacingBetweenBars = int(buttonWidth * 0.1)

        barHeight = int(buttonHeight * 0.6)
        barY = int(buttonHeight * 0.2)


        firstBarX = int(buttonWidth * 0.3)

        secondBarX = firstBarX + barWidth + spacingBetweenBars


        cornerRadiusX = 6
        cornerRadiusY = 6


        painter.drawRoundedRect(
            firstBarX,
            barY,
            barWidth,
            barHeight,
            cornerRadiusX,
            cornerRadiusY
        )

        painter.drawRoundedRect(
            secondBarX,
            barY,
            barWidth,
            barHeight,
            cornerRadiusX,
            cornerRadiusY
        )


class SkipButton(IconButton):

    def __init__(self, direction="right", parent=None):
        super().__init__(parent)
        self.direction = direction


    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        buttonColor = self.currentColor()
        painter.setBrush(buttonColor)

        painter.setPen(Qt.NoPen)


        buttonWidth = self.width()
        buttonHeight = self.height()


        triangleWidth = int(buttonWidth * 0.2)
        triangleHeight = int(buttonHeight * 0.4)

        offset = int(buttonWidth * 0.1)

        barWidth = int(buttonWidth * 0.05)
        barHeight = int(buttonHeight * 0.5)
        barY = int(buttonHeight * 0.25)


        topY = int(buttonHeight * 0.3)
        centerY = int(buttonHeight * 0.5)
        bottomY = int(buttonHeight * 0.7)

        smallGap = int(offset * 0.5)
        largeGap = int(offset * 0.7)


        if self.direction == "right":

            firstTriangleLeftX = offset
            firstTriangleRightX = offset + triangleWidth

            secondTriangleLeftX = firstTriangleRightX + smallGap
            secondTriangleRightX = secondTriangleLeftX + triangleWidth


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


            painter.drawPolygon(firstTriangle)
            painter.drawPolygon(secondTriangle)


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

            firstTriangleRightX = buttonWidth - offset
            firstTriangleLeftX = firstTriangleRightX - triangleWidth

            secondTriangleRightX = firstTriangleLeftX - smallGap
            secondTriangleLeftX = secondTriangleRightX - triangleWidth


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


            painter.drawPolygon(firstTriangle)
            painter.drawPolygon(secondTriangle)


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

        self.setAttribute(Qt.WA_Hover)

        self.setMouseTracking(True)

        self.move(x, y)


        self.normalBackgroundColor = QColor(0, 0, 0)
        self.hoverBackgroundColor = QColor(10, 30, 40)
        self.checkedBackgroundColor = QColor(0, 50, 70)

        self.edgeColor = QColor(0, 255, 255)
        self.textColor = QColor(0, 255, 255)

        self.borderRadius = 4

        fontSize = self.standardised(12)
        self.font = QFont("Segoe UI", fontSize, QFont.Bold)


    def text(self):
        return self.label


    def setOpacity(self, opacity: float):

        clampedOpacity = opacity

        if clampedOpacity < 0.0:
            clampedOpacity = 0.0

        if clampedOpacity > 1.0:
            clampedOpacity = 1.0

        self.opacity = clampedOpacity

        self.update()


    def standardised(self, value):

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

            self.isHovering = False

            if self.checkable:
                if self.checked:
                    self.checked = False
                    self.checkedChanged.emit(False)

        self.update()


    def enterEvent(self, event):

        if self.clickable:
            self.isHovering = True
            self.update()


    def leaveEvent(self, event):

        if self.clickable:
            self.isHovering = False
            self.update()


    def mouseReleaseEvent(self, event):

        if not self.clickable:
            return

        mouseButton = event.button()

        if mouseButton == Qt.LeftButton:

            if self.checkable:
                if not self.checked:
                    self.setChecked(True)

            self.clicked.emit()

            self.update()


    def setChecked(self, state: bool):

        if self.checkable:

            if self.checked != state:

                self.checked = state

                self.checkedChanged.emit(self.checked)

                self.update()


    def currentBackgroundColor(self):

        if not self.clickable:
            return self.normalBackgroundColor

        if self.checkable:
            if self.checked:
                return self.checkedBackgroundColor

        if self.isHovering:
            return self.hoverBackgroundColor

        return self.normalBackgroundColor


    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setOpacity(self.opacity)


        backgroundColor = self.currentBackgroundColor()

        brush = QBrush(backgroundColor)

        pen = QPen(self.edgeColor, 2)

        painter.setBrush(brush)
        painter.setPen(pen)


        rectangle = self.rect()

        painter.drawRoundedRect(
            rectangle,
            self.borderRadius,
            self.borderRadius
        )


        painter.setFont(self.font)

        painter.setPen(self.textColor)

        painter.drawText(
            rectangle,
            Qt.AlignCenter,
            self.label
        )

class ArrowButton(QPushButton):

    def __init__(self, direction="up", parent=None):

        super().__init__(parent)

        buttonSize = QSize(30, 30)
        self.setFixedSize(buttonSize)


        arrowMap = {}

        arrowMap["up"] = QStyle.SP_ArrowUp
        arrowMap["down"] = QStyle.SP_ArrowDown
        arrowMap["left"] = QStyle.SP_ArrowLeft
        arrowMap["right"] = QStyle.SP_ArrowRight


        directionText = direction.lower()

        if directionText in arrowMap:
            arrowType = arrowMap[directionText]
        else:
            arrowType = QStyle.SP_ArrowUp


        icon = self.style().standardIcon(arrowType)

        self.setIcon(icon)


        iconSize = QSize(20, 20)
        self.setIconSize(iconSize)



class TickBoxButton(QWidget):

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


        fontMetrics = self.fontMetrics()

        textWidth = fontMetrics.width(self.text)

        padding = self.standardised(24)

        totalWidth = self.boxSize + self.spacing + textWidth + padding

        self.setFixedWidth(totalWidth)


    def enterEvent(self, event):

        self.isHovering = True

        self.update()


    def leaveEvent(self, event):

        self.isHovering = False

        self.update()


    def mouseReleaseEvent(self, event):

        mouseButton = event.button()

        if mouseButton == Qt.LeftButton:

            if self.checkable:
                self.checked = not self.checked
                self.checkedChanged.emit(self.checked)

            self.clicked.emit()

            self.update()


    def isChecked(self):

        return self.checked


    def setChecked(self, state):

        if self.checked != state:

            self.checked = state

            self.checkedChanged.emit(self.checked)

            self.update()


    def currentBackgroundColor(self):

        if self.checked:
            return self.checkedBackgroundColor

        if self.isHovering:
            return self.hoverBackgroundColor

        return self.normalBackgroundColor


    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(Qt.NoBrush)


        widgetRect = self.rect()

        widgetWidth = self.width()
        widgetHeight = self.height()


        leftPadding = 12

        boxX = leftPadding

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

        painter.drawRoundedRect(boxRect, self.borderRadius, self.borderRadius)


        if self.checked:

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


        textStartX = self.boxSize + self.spacing + leftPadding

        textRectWidth = widgetWidth - textStartX

        textRect = QRect(
            textStartX,
            0,
            textRectWidth,
            widgetHeight
        )

        painter.setFont(self.font)

        painter.setPen(self.textColor)

        painter.drawText(
            textRect,
            Qt.AlignVCenter,
            self.text
        )


    def standardised(self, value):

        screen = QGuiApplication.primaryScreen()

        geometry = screen.geometry()

        screenHeight = geometry.height()

        scaledValue = value * screenHeight / 1600

        return int(scaledValue)
