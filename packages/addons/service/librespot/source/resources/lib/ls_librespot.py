import json
import shlex
import subprocess
import threading
import xbmc
import xbmcgui
import os

from ls_addon import ADDON_ENVT, ADDON_HOME, ADDON_PATH
from ls_addon import get_settings as get_settings
from ls_addon import log as log
from ls_pulseaudio import Pulseaudio as Pulseaudio
from ls_spotify import update_listitem

PIPE_PATH = "/tmp/librespot"
LIBRESPOT = 'librespot' \
            ' --backend pulseaudio' \
            ' --bitrate {bitrate}' \
            ' --cache cache' \
            ' --device {device}' \
            ' --device-type TV' \
            ' --disable-audio-cache' \
            ' --name {name}' \
            ' --onevent=' + ADDON_PATH + "resources/lib/ls_on_event.py"
LIBRESPOT_AUTOPLAY = ' --autoplay'
LIBRESPOT_AUTHENTICATE = ' --disable-discovery' \
                         ' --password {password}' \
                         ' --username {username}'

CODEC = 'pcm_s16be'
MAX_PANICS = 3


class Librespot(xbmc.Player):

    def __init__(self):
        super().__init__()
        settings = get_settings()
        quoted = {k: shlex.quote(v) for (k, v) in settings.items()}
        command = LIBRESPOT
        if settings['autoplay'] == 'true':
            command += LIBRESPOT_AUTOPLAY
        if (settings['discovery'] == 'false' and
                settings['password'] != '' and
                settings['username'] != ''):
            command += LIBRESPOT_AUTHENTICATE
        self.command = shlex.split(command.format(**quoted))
        log(shlex.split(command.format(**dict(quoted, password='*obfuscated*'))))
        self.is_aborted = False
        self.is_dead = False
        self.pulseaudio = Pulseaudio(settings)
        self.listitem = xbmcgui.ListItem()
        self.listitem.addStreamInfo('audio', {'codec': CODEC})
        self.listitem.setPath(path=self.pulseaudio.url)

    def __enter__(self):
        self.pulseaudio.load_modules()
        self.panics = 0
        self.librespot = None
        self.is_playing_librespot = False
        if not self.isPlaying():
            self.start_librespot()

    def __exit__(self, *args):
        self.stop_librespot()
        self.pulseaudio.unload_modules()

    def on_event_error(self):
        self.pulseaudio.suspend_sink(1)
        log("Error detected, restarting...")
        self.stop_librespot(True)

    def on_event_panic(self):
        self.pulseaudio.suspend_sink(1)
        self.panics += 1
        log('event panic {}/{}'.format(self.panics, MAX_PANICS))
        self.is_dead = self.panics >= MAX_PANICS
        self.stop_librespot(True)

    def on_event_playing(self, position_s):
        log('event playing')
        if not self.isPlaying():
            log('starting librespot playback')
            self.pulseaudio.suspend_sink(0)
            self.play(self.pulseaudio.url, self.listitem)
            # TODO seekTime to pos, but it says playback hasn't started (might have to wait?)
        elif self.is_playing_librespot:
            log('updating librespot playback')
            self.updateInfoTag(self.listitem)

    def on_event_stopped(self):
        self.pulseaudio.suspend_sink(1)
        log('event stopped')
        self.panics = 0
        self.stop()

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

    def onPlayBackError(self):
        self.onPlayBackStopped()

    def onPlayBackStarted(self):
        log('Kodi playback started')
        self.is_playing_librespot = self.getPlayingFile() == self.pulseaudio.url
        if not self.is_playing_librespot:
            self.stop_librespot()

    def onPlayBackStopped(self):
        if self.is_playing_librespot:
            log('librespot playback stopped')
            self.is_playing_librespot = False
            self.stop_librespot(True)
        else:
            log('Kodi playback stopped')
            self.start_librespot()

    def run_librespot(self):
        log('librespot thread started')
        self.restart = True
        while self.restart and not self.is_dead:
            self.librespot = subprocess.Popen(
                self.command,
                cwd=ADDON_HOME,
                env=ADDON_ENVT,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                text=True,
                encoding='utf-8')
            log('librespot started')
            with self.librespot.stdout:
                for line in self.librespot.stdout:
                    if 'ERROR' in line:
                        self.on_event_error()
                    log(line.strip())
            #self.pulseaudio.suspend_sink(1)
            #self.stop()
            #self.librespot.wait()
            #log('librespot stopped')
        #self.librespot = None
        #log('librespot thread stopped')

    def start_librespot(self):
        if self.librespot is None:
            self.thread = threading.Thread(target=self.run_librespot)
            self.pipe_listener = threading.Thread(target=self.pipe_listener)
            self.thread.start()
            self.pipe_listener.start()

    def stop(self):
        if self.is_playing_librespot and not self.is_aborted:
            log('stopping librespot playback')
            self.is_playing_librespot = False
            super().stop()

    def stop_librespot(self, restart=False):
        self.restart = restart
        if self.librespot is not None:
            self.librespot.terminate()
            if not restart:
                self.thread.join()
                self.pipe_listener.join()

    def process_event(self, variables):
        processed = json.loads(variables)
        event = processed['PLAYER_EVENT']
        if event == 'track_changed':
            update_listitem(self.listitem, processed)
        elif event == 'playing':
            self.on_event_playing(int(processed['POSITION_MS']) // 1000)
        elif event == 'paused' or event == 'stopped':
            self.on_event_stopped()

    def pipe_listener(self):
        log('Pipe listener started')
        try:
            os.mkfifo(PIPE_PATH)
            log(f'Created pipe')
        except OSError:
            pass

        while self.restart and not self.is_dead:
            with open(PIPE_PATH) as fifo:
                while self.restart and not self.is_dead:
                    data = fifo.read().strip()
                    if len(data) == 0:
                        break
                    log(f'PIPE data: {data}')
                    for line in data.split('\n'):
                        log(f'PIPE data: {line}')
                        self.process_event(line)
