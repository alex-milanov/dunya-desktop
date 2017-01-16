import os
import json
import copy

from PyQt5.QtWidgets import QVBoxLayout, QFrame
from PyQt5.QtCore import QSize, QMetaObject, QTimer
from essentia.standard import MonoLoader
import pyqtgraph.dockarea as pgdock
import numpy as np
from pyqtgraph.ptime import time

from waveformwidget import WaveformWidget
from melodywidget import MelodyWidget
from playbackframe import PlaybackFrame
from utilities.playback import Playback
from cultures.makam import utilities
import ui_files.resources_rc


DOCS_PATH = os.path.join(os.path.dirname(__file__), '..', 'cultures',
                         'documents')


def read_audio(audio_path):
    raw_audio = np.array(MonoLoader(filename=audio_path)())
    len_audio = len(raw_audio)
    min_audio = np.min(raw_audio)
    max_audio = np.min(raw_audio)
    return raw_audio, len_audio, min_audio, max_audio


def load_pitch(pitch_path):
    pitch_data = json.load(open(pitch_path))
    pp = np.array(pitch_data['pitch'])

    time_stamps = pp[:, 0]
    pitch_curve = pp[:, 1]
    pitch_plot = copy.copy(pitch_curve)
    pitch_plot[pitch_plot < 20] = np.nan

    samplerate = pitch_data['sampleRate']
    hopsize = pitch_data['hopSize']

    max_pitch = np.max(pitch_curve)
    min_pitch = np.min(pitch_curve)

    return time_stamps, pitch_plot, max_pitch, min_pitch, samplerate, hopsize


def load_pd(pd_path):
    pd = json.load(open(pd_path))
    vals = pd["vals"]
    bins = pd["bins"]
    return vals, bins


def get_feature_paths(recid):
    doc_folder = os.path.join(DOCS_PATH, recid)
    (full_names, folders, names) = \
        utilities.get_filenames_in_dir(dir_name=doc_folder, keyword='*.json')

    paths = {'audio_path': os.path.join(doc_folder, recid + '.mp3')}
    for xx, name in enumerate(names):
        paths[name.split('.json')[0]] = full_names[xx]
    return paths


class PlayerFrame(QFrame):
    samplerate = 44100.
    fps = None
    last_time = time()

    def __init__(self, recid, parent=None):
        QFrame.__init__(self, parent=parent)
        self.__set_design()

        self.feature_paths = get_feature_paths(recid)

        (self.raw_audio, len_audio, min_audio, max_audio) = \
            read_audio(self.feature_paths['audio_path'])
        self._set_slider(len_audio)

        self.waveform_widget.plot_waveform(self.raw_audio, len_audio,
                                           min_audio, max_audio)

        self.playback = Playback()
        self.playback.set_source(self.feature_paths['audio_path'])
        self.frame_playback.toolbutton_pause.setDisabled(True)

        self.playback.player.positionChanged.connect(self.update_vlines)
        self.waveform_widget.region_wf.sigRegionChangeFinished.connect(
            self.wf_region_changed)
        self.frame_playback.toolbutton_play.clicked.connect(self.playback_play)
        self.frame_playback.toolbutton_pause.clicked.connect(self.playback_pause)

    def closeEvent(self, QCloseEvent):
        if hasattr(self, 'waveform_widget'):
            self.waveform_widget.clear()
        if hasattr(self, 'melody_widget'):
            self.melody_widget.clear()
        if hasattr(self, 'playback'):
            self.playback.pause()

    def update_wf_pos(self, samplerate):
        self.waveform_widget.vline_wf.setPos(
            [self.playback_pos * samplerate, 0])

    def __set_design(self):
        self.setWindowTitle('Player')
        self.resize(1200, 550)
        self.setMinimumSize(QSize(850, 500))
        self.setStyleSheet("background-color: rgb(30, 30, 30);")

        self.dock_area = pgdock.DockArea()

        # dock fixed waveform
        self.dock_fixed_waveform = pgdock.Dock("Waveform", area='Top',
                                               hideTitle=True, closable=False,
                                               autoOrientation=False)
        self.dock_fixed_waveform.setFixedHeight(60)
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.setMinimumHeight(60)
        self.dock_fixed_waveform.addWidget(self.waveform_widget)
        self.dock_fixed_waveform.allowedAreas = ['top']
        self.dock_fixed_waveform.setAcceptDrops(False)
        self.dock_area.addDock(self.dock_fixed_waveform, position='top')

        self.dock_playback = pgdock.Dock(name='Playback', area='bottom',
                                         closable=False, autoOrientation=False)
        self.frame_playback = PlaybackFrame(self)
        self.dock_playback.addWidget(self.frame_playback)
        self.dock_playback.setFixedHeight(60)
        self.dock_playback.setAcceptDrops(False)
        self.dock_area.addDock(self.dock_playback, position='bottom')

        layout = QVBoxLayout(self)
        layout.addWidget(self.dock_area)

        QMetaObject.connectSlotsByName(self)

    def _set_slider(self, len_audio):
        self.frame_playback.slider.setMinimum(0)
        self.frame_playback.slider.setMaximum(len_audio)
        self.frame_playback.slider.setTickInterval(10)
        self.frame_playback.slider.setSingleStep(1)

    def playback_play(self):
        self.frame_playback.toolbutton_play.setDisabled(True)
        self.frame_playback.toolbutton_pause.setEnabled(True)
        self.playback.play()

    def playback_pause(self):
        self.frame_playback.toolbutton_play.setEnabled(True)
        self.frame_playback.toolbutton_pause.setDisabled(True)
        self.playback.pause()

    def wf_region_changed(self):
        pos_wf_x_min, pos_wf_x_max = self.waveform_widget.region_wf.getRegion()
        ratio = len(self.raw_audio) / len(self.waveform_widget.visible)
        #x_min = (pos_wf_x_min * ratio) / self.samplerate
        #x_max = (pos_wf_x_max * ratio) / self.samplerate
        #self.melody_widget.updateHDF5Plot(x_min, x_max)
        #self.melody_widget.set_zoom_selection_area(pos_wf_x_min * ratio,
        #                                           pos_wf_x_max * ratio,
        #                                           self.samplerate,
        #                                           self.hopsize)

    def update_vlines(self, playback_pos):
        # print(playback_pos)
        # if self.playback_thread.playback.is_playing():
        # if self.playback_pos_pyglet == \
        #        self.playback_thread.playback.get_pos_seconds():
        #    self.playback_pos += 0.05
        # else:
        #    self.playback_pos = \
        #        self.playback_thread.playback.get_pos_seconds()
        #    self.playback_pos_pyglet = \
        #        self.playback_thread.playback.get_pos_seconds()

        # self.playback_pos = self.playback_thread.playback.get_pos_seconds()
        ratio = len(self.raw_audio) / len(self.waveform_widget.visible)
        playback_pos_sec = playback_pos / 1000.
        playback_pos_sample = playback_pos_sec * self.samplerate
        #self.melody_widget.vline.setPos([playback_pos_sec, 0])
        #self.melody_widget.hline_histogram.setPos(
        #    pos=[0,
        #         self.pitch_plot[np.int(playback_pos_sample / self.hopsize)]])
        self.frame_playback.slider.setValue(playback_pos_sample)
        self.waveform_widget.vline_wf.setPos([playback_pos_sample/ratio,
                                              np.min(self.raw_audio)])

        #now = time()
        #dt = now - self.last_time
        #self.last_time = now
        #if self.fps is None:
        #    self.fps = 1.0 / dt
        #else:
        #    s = np.clip(dt * 3., 0, 1)
        #    self.fps = self.fps * (1 - s) + (1.0 / dt) * s
        #self.melody_widget.zoom_selection.setTitle('%0.2f fps' % self.fps)

        # pos_vline = self.melody_widget.vline.pos()[0]
        # pos_xmin, pos_xmax = \
        #    self.melody_widget.zoom_selection.viewRange()[0]
        # dist = pos_xmax - pos_xmin

        # if pos_xmax * 0.98 <= pos_vline <= pos_xmax * 1.02:
        #    self.waveform_widget.region_wf.setRegion(
        #        [pos_xmax*samplerate+(hopsize/samplerate),
        #         (pos_xmax+dist)*samplerate])
        #    self.melody_widget.zoom_selection.setXRange(
        #        pos_xmax+(hopsize/samplerate), pos_xmax+dist, padding=0)


        # elif pos_vline < pos_xmin * 0.99 or pos_vline > pos_xmax:
        #    self.playback_pause()
        #    pos_xmin, pos_xmax = self.waveform_widget.region_wf.getRegion()
        #    pos = pos_xmin/samplerate

        #    self.playback_pos = pos
        #    self.playback_pos_pyglet = pos
        #    self.playback_thread.playback.seek(pos)

        #    self.waveform_widget.vline_wf.setPos(pos_xmin)
        #    self.melody_widget.vline.setPos(pos_xmin / samplerate)
        #    self.melody_widget.hline_histogram.setPos(
        #        pos=[0,
        #             pitch[int(self.playback_pos*samplerate/hopsize)]])
        #    self.frame_player.slider.setValue(pos_xmin)

        #    self.melody_widget.zoom_selection.setXRange(
        #        pos_xmin/samplerate, pos_xmax/samplerate, padding=0)
        # else:
        # pass
        # else for now playing option
