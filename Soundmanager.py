import os
import random
import vlc
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

from ElkUtils.DataStructures import CircularQueue


class AudioManager(QObject):

    #Signal connections
    positionChanged = pyqtSignal(int)
    durationChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        """
        Loads mp3 files from a designated folder onto a circular queue and offers an interface through which to play them
        Audio is controlled by VLC and the user must have it installed to access playlist creation
        """

        #Set up VLC (Needs preenstalled vlc player on device)
        self.vlcInstance = vlc.Instance()

        #Make different music players for different tasks
        self.introPlayer = self.vlcInstance.media_player_new()
        self.musicPlayer = self.vlcInstance.media_player_new()
        self.musicListPlayer = self.vlcInstance.media_list_player_new()
        self.musicListPlayer.set_media_player(self.musicPlayer)

        #Param declaration
        self.mediaList = self.vlcInstance.media_list_new()
        self.trackQueue = None
        self.queueSize = 0

        #Timer creation (for displaying elapsed time on UI)
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._pollPosition)
        self.timer.start()

    @property
    def musicPlaylist(self):
        #Getter method of object
        return self

    def next(self):
        #Play next track
        self.nextTrack()

    def previous(self):
        #Play previous track
        self.prevTrack()

    def playIntroSound(self):
        #Special method for playing the intro sound - has special path
        introPath = os.path.abspath("Audio/Intro/intro.mp3")
        if not os.path.exists(introPath): #For it to not throw an error if file not found
            return

        #Plays file if found
        media = self.vlcInstance.media_new(introPath)
        self.introPlayer.set_media(media)
        self.introPlayer.audio_set_volume(70)
        self.introPlayer.play()

    def stopIntroSound(self):
        #Stops inro sound if intro ends before the sound has completed
        self.introPlayer.stop()


    def loadSoundtrack(self, folder="Audio/Soundtrack"):
        """
        Turns folder of mp3s into a playlist
        Playlist stored on a circular queue
        """
        if not os.path.exists(folder): #Check if folder exists
            return

        files = []

        #Runs only if file exists
        for f in os.listdir(folder):
            if f.lower().endswith(".mp3"):
                files.append(f)

        #if files empty dont play
        if not files:
            return

        random.shuffle(files)

        #Circular queue setup
        self.queueSize = len(files)
        self.trackQueue = CircularQueue(self.queueSize)
        self.mediaList = self.vlcInstance.media_list_new()


        #Load every file into circular queue
        for file in files:
            fullPath = os.path.abspath(os.path.join(folder, file))
            self.trackQueue.enqueue(fullPath)
            self.mediaList.add_media(self.vlcInstance.media_new(fullPath))

        #Start music player
        self.musicListPlayer.set_media_list(self.mediaList)
        self.musicListPlayer.set_playback_mode(vlc.PlaybackMode.loop)
        self.musicListPlayer.play()

    def reshuffleSoundtrack(self):
        """
        Randomly shuffles playlist
        Currently only used right after music playlist creation
        """

        #Doesnt run if no music present
        if self.queueSize == 0:
            return

        #Load all tracks into list from queue and shuffle it using built in method
        tracks = [self.trackQueue.dequeue() for i in range(self.queueSize)]
        random.shuffle(tracks)

        #Create new circular queue
        self.trackQueue = CircularQueue(self.queueSize)
        self.mediaList = self.vlcInstance.media_list_new()

        for fullPath in tracks:
            self.trackQueue.enqueue(fullPath)
            self.mediaList.add_media(self.vlcInstance.media_new(fullPath))

        wasPlaying = self.musicPlayer.is_playing()
        self.musicListPlayer.set_media_list(self.mediaList)
        #Play song that was playing before shuffling
        if wasPlaying:
            self.musicListPlayer.play()

    def nextTrack(self):
        #Fetches past track from queue
        if self.queueSize > 0:
            self.trackQueue.dequeue()
            self.musicListPlayer.next()

    def prevTrack(self):
        #Fetches next track from queue
        if self.queueSize > 0:
            self.trackQueue.front = (self.trackQueue.front - 1) % self.queueSize
            self.musicListPlayer.previous()

    def playSoundtrack(self):
        #Plays soundtrack
        self.musicListPlayer.play()

    def pauseSoundtrack(self):
        #Pauses current file
        self.musicListPlayer.pause()

    def stopSoundtrack(self):
        #Stops current file (Difference between this and pause is that pause stores the time on which the file was stored)
        #Currently unused
        self.musicListPlayer.stop()

    def togglePlayPause(self):
        #Starts/stops music based on what button pressed
        if self.musicPlayer.is_playing():
            self.musicListPlayer.pause()
        else:
            self.musicListPlayer.play()

    def setVolume(self, volume: int):
        #Volume setter
        self.musicPlayer.audio_set_volume(volume)

    def seek(self, seconds: int):
        #Seeker
        self.musicPlayer.set_time(seconds * 1000)

    def _pollPosition(self):
        #Exception handler if file not in player somehow
        if not self.musicPlayer:
            return

        #Gets current file that is playing
        isPlaying = self.musicPlayer.is_playing()

        if isPlaying:
            #Get details about file length
            posMs = self.musicPlayer.get_time()
            durMs = self.musicPlayer.get_length()

            #Emits signal for the musicWidget with the time left and total time
            if posMs != -1:
                self.positionChanged.emit(posMs // 1000)
            if durMs != -1:
                self.durationChanged.emit(durMs // 1000)

        self.stateChanged.emit(isPlaying)
