from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QRadialGradient, QPolygonF
from PyQt5.QtCore import Qt, QPointF
import math

class StarLogoWidget(QWidget):
    def __init__(self, parent=None, glowIntensity=0.4):
        super().__init__(parent)
        self.opacity = 1.0
        self.glowIntensity = glowIntensity

    def setOpacity(self, value):

        #Opacity setter
        if value < 0: 
            value = 0
        elif value > 1:
            value = 1
        self.opacity = value

        #Update force
        self.update()

    def paintEvent(self, widgetEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # Big brain


        painter.setOpacity(self.opacity) # may be a bit redundant as long as there is no fade in

        #var setup
        SCREEN_WIDTH = self.width()
        SCREEN_HEIGHT = self.height()
        size = min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.9
        centreX = SCREEN_WIDTH / 2
        centreY = SCREEN_HEIGHT / 2

        glowRadius = size / 3

        #Draw outer hexagon
        pen = QPen(QColor(0, 200, 255))
        pen.setWidthF(2 * self.glowIntensity)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        hexagon = self.makeHex(centreX, centreY, size / 2)
        painter.drawPolygon(hexagon)

        #Draw glow circle
        gradient = QRadialGradient(QPointF(centreX, centreY), glowRadius)
        glowColor = QColor(0, 220, 255, int(255 * self.glowIntensity))
        gradient.setColorAt(0.0, glowColor)
        gradient.setColorAt(1.0, QColor(0, 220, 255, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(centreX, centreY), size / 2, size / 2)

        #Draw star ridges
        star = self.makeStar(centreX, centreY, size / 4, size / 11)
        self.drawRidges(painter, star, QPointF(centreX, centreY), QColor(0, 220, 255), 2)

        #Draw star fill
        painter.setPen(QPen(QColor(0, 220, 255), 2))
        painter.setBrush(QColor(0, 80, 140, 180))
        painter.drawPolygon(star)

        #Techy lines
        painter.setPen(QPen(QColor(0, 150, 255, 180), 1.5))
        self.drawRadiiLines(painter, centreX, centreY, size / 2)

        #dots on corners
        painter.setBrush(QColor(0, 220, 255))
        painter.setPen(Qt.NoPen)
        for point in hexagon:
            painter.drawEllipse(point, 5, 5)
        painter.drawEllipse(QPointF(centreX, centreY), 5, 5)

    def makeHex(self, centreX, centreY, hexRadius):

        #Circle points every 60 degrees
        points = []
        for i in range(6):

            angle = math.radians(60 * i)
            pointX = centreX + hexRadius * math.cos(angle)
            pointY = centreY + hexRadius * math.sin(angle)
            points.append(QPointF(pointX, pointY))

        return QPolygonF(points)

    def makeStar(self, centreX, centreY, bigRadius, smallRadius):

        points = []
        for i in range(12):
            angle = math.radians(i * 30 - 90)

            #Record points via two different circles
            if i % 2 == 0:
                pointRadius = bigRadius
            else:
                pointRadius = smallRadius

            pointX = centreX + pointRadius * math.cos(angle)
            pointY = centreY + pointRadius * math.sin(angle)
            points.append(QPointF(pointX, pointY))
        return QPolygonF(points)

    def drawRadiiLines(self, painter, centreX, centreY, radius):
        hexPoints = self.makeHex(centreX, centreY, radius)
        center = QPointF(centreX, centreY)

        #big lines
        for pointId in [1, 3, 5]:
            painter.drawLine(hexPoints[pointId], center)

        #small lines
        for pointId in [0, 2, 4]:
            point = hexPoints[pointId]
            distanceX = center.x() - point.x()
            distanceY = center.y() - point.y()

            starSizeRatio = 47 / 58

            stopX = point.x() + distanceX * (starSizeRatio)
            stopY = point.y() + distanceY * (starSizeRatio)
            painter.drawLine(point, QPointF(stopX, stopY))

    def drawRidges(self, painter, starPoints, center, ridgeColor, lineWidth):
        for pointID in range(len(starPoints)):

            #Pointgen
            point1 = starPoints[pointID]
            point2 = starPoints[(pointID + 1) % len(starPoints)] # I just learnt that I could be doing this lmao

            #Triangle drawer and filler
            ridge = QPolygonF([center, point1, point2])

            if pointID % 2 == 0:
                fill = ridgeColor.darker(130)
            else:
                fill = ridgeColor.lighter(130)
            fill.setAlpha(150)

            #Ridge drawer
            painter.setPen(QPen(ridgeColor, lineWidth))
            painter.setBrush(fill)
            painter.drawPolygon(ridge)
