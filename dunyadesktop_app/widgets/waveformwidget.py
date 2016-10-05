from PyQt4 import QtGui, QtCore
from pyqtgraph import GraphicsLayoutWidget
import pyqtgraph as pg


class WaveformWidget(GraphicsLayoutWidget):
    def __init__(self):
        GraphicsLayoutWidget.__init__(self, parent=None)

        self.layout = pg.GraphicsLayout()
        self._set_size_policy()

    def _set_size_policy(self):
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred,
                                       QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        self.setMinimumSize(QtCore.QSize(0, 100))
        self.setMaximumSize(QtCore.QSize(16777215, 100))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setAcceptDrops(False)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def plot_waveform(self, raw_audio):
        self.waveform = self.layout.addPlot(title='Waveform')
        self.waveform.setDownsampling(auto=True)

        self.waveform.hideAxis(axis='bottom')
        self.waveform.hideAxis(axis='left')

        self.waveform.setMaximumHeight(100)
        self.waveform.setMouseEnabled(x=False, y=False)

        self.waveform.plot(y=raw_audio, pen=(20, 170, 100, 20))
