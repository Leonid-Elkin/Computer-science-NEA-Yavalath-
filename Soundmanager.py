import os
import random
import vlc
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

from ElkUtils.DataStructures import CircularQueue


class AudioManager(QObject):
    """
    AudioManager handles music playback, intro sounds, and track navigation
    using python-vlc instead of QtMultimedia.
    """

    # Qt signals for UI integration
    positionChanged = pyqtSignal(int)   # current position (s)
    durationChanged = pyqtSignal(int)   # total duration (s)
    stateChanged = pyqtSignal(bool)     # True if playing, False otherwise

    def __init__(self):
        super().__init__()

        # --- VLC Core ---
        self.vlcInstance = vlc.Instance()

        # Dedicated players
        self.introPlayer = self.vlcInstance.media_player_new()
        self.musicListPlayer = self.vlcInstance.media_list_player_new()
        self.musicPlayer = self.vlcInstance.media_player_new()
        self.musicListPlayer.set_media_player(self.musicPlayer)

        # Playlist + track queue
        self.mediaList = self.vlcInstance.media_list_new()
        self.trackQueue = None
        self.queueSize = 0

        # Poll playback status since VLC doesn't emit Qt signals
        self.timer = QTimer()
        self.timer.setInterval(1000)  # every second
        self.timer.timeout.connect(self._pollPosition)
        self.timer.start()

    # ---------------- Playlist wrapper ----------------
    @property
    def musicPlaylist(self):
        class PlaylistWrapper:
            def __init__(self, manager):
                self.manager = manager

            def next(self):
                self.manager.nextTrack()

            def previous(self):
                self.manager.prevTrack()

        return PlaylistWrapper(self)

    # ---------------- Intro sound ----------------
    def playIntroSound(self):
        introPath = os.path.abspath("Audio/Intro/intro.mp3")
        if not os.path.exists(introPath):
            print("[AudioManager] Intro file not found!")
            return

        media = self.vlcInstance.media_new(introPath)
        self.introPlayer.set_media(media)
        self.introPlayer.audio_set_volume(70)
        self.introPlayer.play()

    def stopIntroSound(self):
        self.introPlayer.stop()

    # ---------------- Soundtrack ----------------
    def loadSoundtrack(self, folder="Audio/Soundtrack"):
        if not os.path.exists(folder):
            print(f"[AudioManager] Folder '{folder}' not found.")
            return

        files = [f for f in os.listdir(folder) if f.lower().endswith(".mp3")]
        if not files:
            print(f"[AudioManager] No MP3 files in {folder}")
            return

        # Shuffle files for random playback order
        random.shuffle(files)
        self.queueSize = len(files)
        self.trackQueue = CircularQueue(self.queueSize)

        # Rebuild VLC media list with shuffled order
        self.mediaList = self.vlcInstance.media_list_new()
        for file in files:
            fullPath = os.path.abspath(os.path.join(folder, file))
            self.trackQueue.enqueue(fullPath)
            media = self.vlcInstance.media_new(fullPath)
            self.mediaList.add_media(media)

        self.musicListPlayer.set_media_list(self.mediaList)
        
        # Set playback mode to normal (not repeat) to ensure shuffle order is followed
        # VLC will play through the shuffled list in order
        self.musicListPlayer.set_playback_mode(vlc.PlaybackMode.loop)
        
        self.musicListPlayer.play()

    def reshuffleSoundtrack(self):
        """Re-shuffle the current soundtrack for a new random order."""
        if self.queueSize == 0:
            print("[AudioManager] No tracks loaded to shuffle.")
            return
        
        # Extract all tracks from current queue
        tracks = []
        for i in range(self.queueSize):
            tracks.append(self.trackQueue.dequeue())
        
        # Shuffle and rebuild
        random.shuffle(tracks)
        
        # Rebuild queue and media list
        self.trackQueue = CircularQueue(self.queueSize)
        self.mediaList = self.vlcInstance.media_list_new()
        
        for fullPath in tracks:
            self.trackQueue.enqueue(fullPath)
            media = self.vlcInstance.media_new(fullPath)
            self.mediaList.add_media(media)
        
        # Update player with new shuffled list
        was_playing = self.musicPlayer.is_playing()
        self.musicListPlayer.set_media_list(self.mediaList)
        
        if was_playing:
            self.musicListPlayer.play()
        
        print("[AudioManager] Soundtrack reshuffled!")

    def nextTrack(self):
        if self.queueSize > 0:
            self.trackQueue.dequeue()
            self.musicListPlayer.next()

    def prevTrack(self):
        if self.queueSize > 0:
            # VLC doesn't track "previous" naturally → adjust manually
            current = self.trackQueue.front
            self.trackQueue.front = (current - 1 + self.queueSize) % self.queueSize
            self.musicListPlayer.previous()

    # ---------------- Playback control ----------------
    def playSoundtrack(self):
        self.musicListPlayer.play()

    def pauseSoundtrack(self):
        self.musicListPlayer.pause()

    def stopSoundtrack(self):
        self.musicListPlayer.stop()

    def togglePlayPause(self):
        if self.musicPlayer.is_playing():
            self.musicListPlayer.pause()
        else:
            self.musicListPlayer.play()

    def setVolume(self, volume: int):
        self.musicPlayer.audio_set_volume(volume)

    def seek(self, seconds: int):
        """Seek to `seconds` in the current track."""
        self.musicPlayer.set_time(seconds * 1000)

    # ---------------- Polling ----------------
    def _pollPosition(self):
        if self.musicPlayer.is_playing():
            pos_ms = self.musicPlayer.get_time()
            dur_ms = self.musicPlayer.get_length()

            if pos_ms != -1:
                self.positionChanged.emit(pos_ms // 1000)
            if dur_ms != -1:
                self.durationChanged.emit(dur_ms // 1000)

            self.stateChanged.emit(True)
        else:
            self.stateChanged.emit(False)