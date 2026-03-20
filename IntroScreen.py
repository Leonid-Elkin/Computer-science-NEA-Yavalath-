from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QFont, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from UI.StarLogoWidget import StarLogoWidget


class IntroScreen(QWidget):
    
    #File signals fucking stupid file signals not working half the time
    IntroStarted = pyqtSignal()
    FadeInFinished = pyqtSignal()
    FadeOutStarted = pyqtSignal()
    IntroFinished = pyqtSignal()
    #Never mind its all good

    def __init__(self, displayDuration = 2000, fadeOutDuration = 1000):
        print("DEBUG: INTRO SEQUENCE BEGUN")
        super().__init__()

        self.StarLogo = StarLogoWidget(self)


        self.opacity = 1.0
        self.StarLogo.setOpacity(self.opacity)

        self.showFullScreen()

        #stupid stylesheet 
        self.setStyleSheet("background-color: black;")
        #self.setStyleSheet("background-color: white;")
        #Light mode

        self.DisplayDuration = displayDuration
        self.FadeOutDuration = fadeOutDuration

        #No fade in so just call immediately - Not bothered to fix properly
        self.IntroStarted.emit()
        self.FadeInFinished.emit()  

     
        self.fadeOutTimer = QTimer(self)
        self.fadeOutTimer.timeout.connect(self.fadeOutStep)
        self.fadeOutStepAmount = 30 / self.FadeOutDuration

        #Schedule fade-out to start after the display duration)
        QTimer.singleShot(self.DisplayDuration, self.StartFadeOut)

    def fadeOutStep(self):

        self.opacity -= self.fadeOutStepAmount

        if self.opacity <= 0.0:
            
            #Stop fading and emmit signal that intro stopped
            self.opacity = 0.0
            self.fadeOutTimer.stop()
            print("DEBUG: INTRO FINISHED")
            self.IntroFinished.emit()

        #Star logo opacity change
        self.StarLogo.setOpacity(self.opacity)
        #Force a paint event
        self.update()

    def StartFadeOut(self):
        print("DEBUG: INTRO FADE OUT STARTED")
        #Opacity decreasing step calling every 30ms
        self.FadeOutStarted.emit()
        self.fadeOutTimer.start(30)


    def paintEvent(self, widgetEvent):
        # This is a special QWidget method that is called automatically when the widget is resized or first created

        painter = QPainter(self)  
        painter.setRenderHint(QPainter.Antialiasing)  #I feel so smart  (Copied of google)

        #Background color
        painter.fillRect(self.rect(), Qt.black)
        #painter.fillRect(self.rect(), Qt.white)


        painter.setOpacity(self.opacity)


        SCREEN_WIDTH = self.width()
        self.SCREEN_WIDTH = SCREEN_WIDTH
        SCREEN_HEIGHT = self.height()
        self.SCREEN_HEIGHT = SCREEN_HEIGHT
        CentreY = SCREEN_HEIGHT / 2  



        #Star Logo creation

        starSize = int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.5)
        self.StarLogo.resize(starSize, starSize)


        starX = (SCREEN_WIDTH - starSize) / 2
        starY = (SCREEN_HEIGHT / 1.7) - starSize * 0.8

        self.StarLogo.move(int(starX), int(starY))




        leftMargin = int(SCREEN_WIDTH * -0.1)  
        subtitleLeftMargin = int(SCREEN_HEIGHT * 0.15)


  
        titleSpacing = int(SCREEN_HEIGHT * 0.075) 
        titleOffsetY = int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.05)   

        smallTextOffsetY = int((titleOffsetY + 3 * titleSpacing) * 1.05)  
        subtitleOffsetY = smallTextOffsetY + int(SCREEN_HEIGHT * 0.1)  


        shadowColor = QColor(0, 140, 255, 140)  

     
        fontTitle = QFont("Times New Roman", int(SCREEN_HEIGHT * 0.06), QFont.Bold)
        fontSmall = QFont("Times New Roman", int(SCREEN_HEIGHT * 0.03), QFont.Bold)
        fontSubtitle = QFont("Times New Roman", int(SCREEN_HEIGHT * 0.035), QFont.Bold)

        
        titleRow1 = "SUSAN"
        titleRow2 = "YAVALATH"
        titleRow3 = "PENTALATH"

        smallText = "BY LEONID ELKIN"
        subtitleText = "Hexagonal strategy games"






        painter.translate(SCREEN_WIDTH / 2, 0)
        painter.scale(0.79, 1) #Make font fitting
        painter.translate(-SCREEN_WIDTH / 2, 0)

        # TITLTLTELTELL

        painter.setFont(fontTitle)

        #offsetListForTitles = [(int(SCREEN_WIDTH/2560),int(SCREEN_WIDTH/2560)),(int(SCREEN_WIDTH * 2 / 2560),int(SCREEN_WIDTH * 2 / 2560)),(int(SCREEN_WIDTH * 3 / 2560),int(SCREEN_WIDTH * 3 / 2560)),(int(SCREEN_WIDTH * 4 / 2560), int(SCREEN_WIDTH * 4 / 2560))]
        #print(offsetListForTitles)
        offsetListForTitles = []
        offsetListForSubtitles = []
        
        for i in range (4):
            offsetListForTitles.append((self.normalize(i),self.normalize(i)))

        for i in range (3):
            offsetListForSubtitles.append((self.normalize(i),self.normalize(i)))

        title1Offset = int(CentreY) + titleOffsetY + 0 * titleSpacing
        title2Offset = int(CentreY) + titleOffsetY + 1 * titleSpacing
        title3Offset = int(CentreY) + titleOffsetY + 2 * titleSpacing
# I dont even know why I desided to do this this way its very innefficient but whatever
#Also the autocorrect generative AI thing that VS code has built in im just trying to write comments and it tries to guess so ass.

        offsetList = []
        for offset in range (3):
            offsetList.append(int(CentreY) + titleOffsetY + offset * titleSpacing)

        

        for offsetX, offsetY in offsetListForTitles:

          
            painter.setPen(shadowColor)
            painter.drawText(leftMargin + offsetX, title1Offset + offsetY, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow1)

       
            painter.setPen(shadowColor)
            painter.drawText(leftMargin + offsetX, title2Offset + offsetY, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow2)

            
            painter.setPen(shadowColor)
            painter.drawText(leftMargin + offsetX, title3Offset + offsetY, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow3)

     
        painter.setPen(Qt.white)
        painter.drawText(leftMargin, title1Offset, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow1)

     
        painter.setPen(Qt.white)
        painter.drawText(leftMargin, title2Offset, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow2)

       
        painter.setPen(Qt.white)
        painter.drawText(leftMargin, title3Offset, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, titleRow3)




        #SUBTITLE
        painter.setFont(fontSmall)

        yOffsetSubtitle = int(CentreY) + smallTextOffsetY

        for OffsetX, OffsetY in offsetListForSubtitles:

            painter.setPen(shadowColor)
            painter.drawText(leftMargin + OffsetX, yOffsetSubtitle + OffsetY, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, smallText)

        painter.setPen(Qt.white)
        painter.drawText(leftMargin, yOffsetSubtitle, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.1), Qt.AlignLeft, smallText)



        #FOOTNOTE
        painter.setFont(fontSubtitle)

        yOffsetFootnote = int(CentreY) + subtitleOffsetY

        for OffsetX, OffsetY in offsetListForSubtitles:

            painter.setPen(shadowColor)
            painter.drawText(subtitleLeftMargin + OffsetX, yOffsetFootnote + OffsetY, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.08), Qt.AlignLeft, subtitleText)

        painter.setPen(Qt.white)
        painter.drawText(subtitleLeftMargin, yOffsetFootnote, SCREEN_WIDTH, int(SCREEN_HEIGHT * 0.08), Qt.AlignLeft, subtitleText)

    def normalize(self,x):
        return int(self.SCREEN_HEIGHT * 2 / 2560)




