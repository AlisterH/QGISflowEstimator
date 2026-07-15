# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FlowEstimatorDialog
                                  A QGIS plugin
  Estimates steady, uniform flow using the Manning equation for trapezoidal and DEM sampled channels.
                              -------------------
         begin                : 2015-05-21
         git sha              : $Format:%H$
         copyright            : (C) 2015 by M. Weier - North Dakota State Water Commission
         email                : mweier@nd.gov
  ***************************************************************************/

 /***************************************************************************
  *                                                                         *
  *   This program is free software; you can redistribute it and/or modify  *
  *   it under the terms of the GNU General Public License as published by  *
  *   the Free Software Foundation; either version 2 of the License, or     *
  *   (at your option) any later version.                                   *
  *                                                                         *
  ***************************************************************************/
"""
#from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import zip
from builtins import range
import os

from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtGui import QColor, QKeySequence
from qgis.PyQt.QtWidgets import QApplication, QDialog, QMessageBox, QFileDialog, QDialogButtonBox, QShortcut
from qgis.PyQt.QtCore import Qt, QObject
from qgis.gui import QgsRubberBand
try:
    from qgis.utils import metadataParser
except:
	from qgis.utils import plugins_metadata_parser as metadataParser # older versions of QGIS
try:
    from qgis.core import Qgis, QgsMessageLog, QgsPointXY, QgsWkbTypes
except:
    from qgis.core import QGis as Qgis, QgsMessageLog, QgsPoint as QgsPointXY

try:
    import mplcursors
    MPLCURSORS="installed"
except:
    MPLCURSORS="missing"

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter

from . import FlowEstimator_utils as utils
from .openChannel import flowEstimator
from .ptmaptool import ProfiletoolMapTool

from shapely.geometry import LineString
import numpy as np

from .qt_compat import BUTTONBOX_SAVE, BUTTONBOX_CLOSE, MATCH_STARTS_WITH, COLOR_RED, COLOR_BLUE, MSGBOX_YES, MSGBOX_NO

try:
    # QGIS 3.x and 4.x
    from qgis.core import Qgis, QgsMessageLog
    try:
        # Fully-qualified scoped enum — required on QGIS 4 (PyQt6), works on QGIS 3 too
        LEVEL_INFO = Qgis.MessageLevel.Info
        LEVEL_WARNING = Qgis.MessageLevel.Warning
        LEVEL_CRITICAL = Qgis.MessageLevel.Critical
    except AttributeError:
        # Very old 3.x fallback, just in case
        LEVEL_INFO = Qgis.Info
        LEVEL_WARNING = Qgis.Warning
        LEVEL_CRITICAL = Qgis.Critical
except ImportError:
    # QGIS 2.x — module is QGis, not Qgis, and levels live on QgsMessageLog
    from qgis.core import QgsMessageLog
    LEVEL_INFO = QgsMessageLog.INFO
    LEVEL_WARNING = QgsMessageLog.WARNING
    LEVEL_CRITICAL = QgsMessageLog.CRITICAL

def log(message, level=LEVEL_INFO):
    """Cross-version wrapper for QgsMessageLog.logMessage (QGIS 2, 3, and 4)."""
    QgsMessageLog.logMessage(message, 'Flow Estimator', level)

# log the versions we are running, because why not?
from qgis.utils import pluginMetadata
log("QGIS " + Qgis.QGIS_VERSION, LEVEL_INFO)
log('Flow Estimator version ' + pluginMetadata('FlowEstimator','Version'), LEVEL_INFO)

if Qgis.QGIS_VERSION_INT > 29000: # Hide and show works on QGIS3, mostly... although occasionally not!
# Disabling Nov 2025 as it often doesn't work now (due to newer QGIS? QT? Windows 11?)
    HIDE_ENABLED='False' # Change to false if you can't cope with the show failing every now and then.
else: # Don't change this - hide works on QGIS2, but not show!
    HIDE_ENABLED='False'

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'flow_estimator_dialog_base.ui'))

class FlowEstimatorDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(FlowEstimatorDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        self.iface = iface
        self.setupUi(self)
        
        self.btnOk = self.buttonBox.button(BUTTONBOX_SAVE)
        self.btnClose = self.buttonBox.button(BUTTONBOX_CLOSE) 
        self.btnBrowse.clicked.connect(self.writeDirName)
        self.btnClose.clicked.connect(self.close)
        self.btnLoadTXT.clicked.connect(self.loadTxt)
        self.btnSampleLine.setEnabled(False)
        self.btnSampleSlope.setEnabled(False)
        self.calcType = 'Trap'
        
        # add shortcut keys to zoom in the documentation tab, because why not?
        QShortcut(QKeySequence('Ctrl++'), self.textBrowser, self.textBrowser.zoomIn)
        QShortcut(QKeySequence('Ctrl+-'), self.textBrowser, self.textBrowser.zoomOut)
      
        # add matplotlib figure to dialog
        self.figure = Figure()
        self.figure.set_size_inches(6, 2.8)
        self.axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.12, bottom=0.15, right=.75, top=.9, wspace=None, hspace=.2)
        self.mplCanvas = FigureCanvas(self.figure)
        self.vLayout.addWidget(self.mplCanvas)
        
        self.depth.valueChanged.connect(self.run)
        self.botWidth.valueChanged.connect(self.run)
        self.leftSS.valueChanged.connect(self.run)
        self.rightSS.valueChanged.connect(self.run)
        self.n.valueChanged.connect(self.run)
        self.slope.valueChanged.connect(self.run)
        self.cbWSE.valueChanged.connect(self.run)
        self.ft.clicked.connect(self.run)
        self.m.clicked.connect(self.run)
        self.cbUDwse.valueChanged.connect(self.run)

        self.manageGui() 
        self.btnSampleLine.clicked.connect(self.sampleLine)
        self.btnSampleSlope.clicked.connect(self.sampleSlope)
       
        # initialise cross-section station-elevation table
        self.staElev = np.array([])
        
        self.tabWidget.setFocus()

    # need this to make sure map tool is disconnected if the dialog is closed while it is in use
    def closeEvent(self, event):
        if hasattr(self, "rubberband") and self.rubberband is not None:
            self.rubberband.reset(self.polygon)
        self.deactivate()
        super().closeEvent(event)

    # need this to make sure map tool is disconnected if the dialog is closed while it is in use
    def reject(self):
        if hasattr(self, "rubberband") and self.rubberband is not None:
            self.rubberband.reset(self.polygon)
        self.deactivate()
        super().reject()

    def manageGui(self):
        log('manageGui', LEVEL_INFO)
        self.cbDEM.clear()
        # Get both raster and mesh layer names combined
        names = utils.getDataSourceLayerNames()
        if names:
            self.cbDEM.addItems(names)
            self.btnSampleLine.setEnabled(True)
            self.btnSampleSlope.setEnabled(True)

            # If the currently active layer is present in the combo, select it by default.
            active = self.iface.activeLayer()
            if active is not None:
                idx = self.cbDEM.findText(active.name(), MATCH_STARTS_WITH)
                if idx >= 0:
                    self.cbDEM.blockSignals(True)
                    self.cbDEM.setCurrentIndex(idx)
                    self.cbDEM.blockSignals(False)
        self.run()
        
    def plotter(self):
        R, P, area, topWidth, Q, v, depth, xGround, yGround, yGround0, xWater, yWater, yWater0 = self.args
        self.axes.clear()
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)
        ground = self.axes.plot(xGround, yGround, 'k')
        if Q != 0:
            water = self.axes.plot(xWater, yWater, 'blue')
            self.axes.fill_between(xWater, yWater, yWater0, where=yWater>=yWater0, facecolor='blue', interpolate=True, alpha = 0.1)
        if self.calcType == 'DEM':
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nWSE: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}$^2$\nWetted P: {9:,.2f} {5}\nHyd. Radius: {3:.2f} {5}\nVelocity: {4:.2f} {5}/s\nDischarge: {0:.2f} {5}$^3$/s'.format(Q, area, topWidth, R, v, self.units, depth, self.slope.value(), self.n.value(), P, self.cbWSE.value())
        elif self.calcType == 'UD':
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nWSE: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}\nWetted P: {9:,.2f} {5}\nHyd. Radius: {3:.2f} {5}\nVelocity: {4:.2f} {5}/s\nDischarge: {0:.2f} {5}$^3$/s'.format(Q, area, topWidth, R, v, self.units, depth, self.slope.value(), self.n.value(), P, self.cbUDwse.value())
        else: # self.calcType == 'trap'
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nDepth: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}$^2$\nWetted P: {9:,.2f} {5}\nHyd. Radius: {3:.2f} {5}\nVelocity: {4:.2f} {5}/s\nDischarge: {0:.2f} {5}$^3$/s'.format(Q, area, topWidth, R, v, self.units, depth, self.slope.value(), self.n.value(), P, self.depth.value())
        self.axes.set_xlabel('Station, '+self.units)
        self.axes.set_ylabel('Elevation, '+self.units)
        self.axes.set_title('Cross Section')
        self.axes.annotate(self.outText, xy=(.76,0.02), xycoords='figure fraction')
        self.mplCanvas.draw()
        
    def run(self):
        if self.ft.isChecked():
            self.units = 'ft'
        else:
            self.units = 'm'
            
        if self.tabWidget.currentIndex() == 0:
            log('calc trap channel', LEVEL_INFO)
            self.calcType = 'Trap'
            self.args = flowEstimator(self.depth.value(), self.n.value(), self.slope.value(), widthBottom = self.botWidth.value(), rightSS = self.rightSS.value(), leftSS = self.leftSS.value(), units = self.units)
            self.figure.patch.set_facecolor("white")
            self.plotter()
        elif self.tabWidget.currentIndex() == 1:
            log('calc DEM channel', LEVEL_INFO)
            try:
                self.calcType = 'DEM'
                self.args = flowEstimator(self.cbWSE.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                log('could not solve; is the cross-section very unusual?', LEVEL_CRITICAL)
                self.figure.patch.set_facecolor("red")
                self.mplCanvas.draw()
        else:
            log('calc UD channel', LEVEL_INFO)
            try:
                self.calcType = 'UD'
                self.args = flowEstimator(self.cbUDwse.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                log('could not solve; is the cross-section very unusual?', LEVEL_CRITICAL)
                self.figure.patch.set_facecolor("red")
                self.mplCanvas.draw()
                
    def sampleLine(self):
        if HIDE_ENABLED == 'True':
            log('hide at sampleLine', LEVEL_INFO)
            self.hide()
        else:
            self.btnSampleSlope.setEnabled(False)
            self.btnSampleLine.setEnabled(False)
        self.iface.mainWindow().activateWindow()
        self.sampleBtnCode = 'sampleLine'
        if hasattr(self, "rubberband"):
            self.rubberband.reset(self.polygon)
        self.rubberBand()

    def sampleSlope(self):
        if HIDE_ENABLED == 'True':
            log('hide at sampleSlope', LEVEL_INFO)
            self.hide()
        else:
            self.btnSampleSlope.setEnabled(False) 
            self.btnSampleLine.setEnabled(False)
        self.iface.mainWindow().activateWindow()
        self.sampleBtnCode = 'sampleSlope'
        if hasattr(self, "rubberband"):
            self.rubberband.reset(self.polygon)
        self.rubberBand()

    def rubberBand(self):
        log('rubberband', LEVEL_INFO)
        self.canvas = self.iface.mapCanvas()
        if self.sampleBtnCode=='sampleLine':
            self.tool = ProfiletoolMapTool(self.canvas, self.btnSampleLine)
        else:
            self.tool = ProfiletoolMapTool(self.canvas, self.btnSampleSlope)
        self.pointstoDraw = None
        self.dblclktemp = False
        self.selectionmethod = 0
        self.textquit0 = "Click for polyline and double click to end (right click to cancel)"
        self.textquit1 = "Select the polyline in a vector layer (Right click to quit)"
        self.connectTool()
        self.canvas.setMapTool(self.tool)
        self.polygon = QgsWkbTypes.LineGeometry
        self.rubberband = QgsRubberBand(self.canvas, self.polygon)
        self.rubberband.setWidth(2)
        if self.sampleBtnCode == 'sampleLine':
            color = COLOR_RED
        else:
            color = COLOR_BLUE
        self.rubberband.setColor(QColor(color))
        self.pointstoDraw = []
        self.pointstoCal = []
        self.lastClicked = [[-9999999999.9,9999999999.9]]
        self.lastFreeHandPoints = []
        if self.selectionmethod == 0:
            self.iface.mainWindow().statusBar().showMessage(self.textquit0)
        elif self.selectionmethod == 1:
            self.iface.mainWindow().statusBar().showMessage(self.textquit1)

    def moved(self,position):
        if self.selectionmethod == 0:
            if len(self.pointstoDraw) > 0:
                mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
                try:
                    self.rubberband.reset(QgsWkbTypes.LineGeometry)
                except:
                    self.rubberband.reset(Qgis.Line)
                for i in range(0,len(self.pointstoDraw)):
                     self.rubberband.addPoint(QgsPointXY(self.pointstoDraw[i][0],self.pointstoDraw[i][1]))
                self.rubberband.addPoint(QgsPointXY(mapPos.x(),mapPos.y()))

    def tooldeactivated(self):
        log('show deactivated', LEVEL_INFO)
        self.tool.moved.disconnect(self.moved)
        self.tool.rightClicked.disconnect(self.rightClicked)
        self.tool.leftClicked.disconnect(self.leftClicked)
        self.tool.doubleClicked.disconnect(self.doubleClicked)
        self.tool.deactivated.disconnect(self.tooldeactivated)
        self.canvas.unsetMapTool(self.tool)
        self.iface.mainWindow().statusBar().showMessage( "" )
        if HIDE_ENABLED == 'False':
            self.btnSampleLine.setEnabled(True)
            self.btnSampleSlope.setEnabled(True) 
            self.activateWindow()
        self.show()

    def rightClicked(self,position):
        log('rightclicked', LEVEL_INFO)
        if self.selectionmethod == 0:
            if len(self.pointstoDraw) > 0:
                self.pointstoDraw = []
                self.pointstoCal = []
                self.rubberband.reset(self.polygon)
            else:
                self.tooldeactivated()

    def leftClicked(self,position):
        log('leftclicked', LEVEL_INFO)
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        if self.selectionmethod == 0:
            if newPoints == self.dblclktemp:
                self.dblclktemp = None
                return
            else :
                self.pointstoDraw += newPoints

    def doubleClicked(self,position):
        log('doubleclicked', LEVEL_INFO)
        self.show()
        if HIDE_ENABLED == 'False':
            self.activateWindow()
        if self.selectionmethod == 0:
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
            newPoints = [[mapPos.x(), mapPos.y()]]
            log('newPoints ' + str(newPoints), LEVEL_INFO)
            self.pointstoDraw += newPoints
            log('self.pointstoDraw ' + str(self.pointstoDraw), LEVEL_INFO)
            log('len(self.pointstoDraw) ' + str(len(self.pointstoDraw)), LEVEL_INFO)
            self.iface.mainWindow().statusBar().showMessage(str(self.pointstoDraw))
            if len(self.pointstoDraw) < 3:
                QMessageBox.warning(self,'Error',
                                         'Draw a section with more than one point')
            else:
                if self.sampleBtnCode == 'sampleLine':
                    staElevPrev = self.staElev
                    staElev, error = self.doRubberbandProfile()
                    if error:
                        pass
                    else:
                        self.staElev = np.pad(staElev, ((0,0), (0,1)), mode='constant', constant_values=0)
                        d = np.diff(staElev, axis=0)
                        self.staElev[1:,2] = np.cumsum(np.sqrt(np.sum(d*d, axis = 1)))
                        self.doIrregularProfileFlowEstimator(staElevPrev)
                else:
                    staElev, error = self.doRubberbandProfile()
                    if error:
                        pass
                    else:
                        self.doRubberbandSlopeEstimator(staElev)

            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            self.dblclktemp = newPoints
            self.iface.mainWindow().statusBar().showMessage( "" )
            if HIDE_ENABLED == 'False':
                self.btnSampleLine.setEnabled(True)
                self.btnSampleSlope.setEnabled(True)
            self.deactivate()
            return
            
    def connectTool(self):
        log('connecting', LEVEL_INFO)
        self.tool.moved.connect(self.moved)
        self.tool.rightClicked.connect(self.rightClicked)
        self.tool.leftClicked.connect(self.leftClicked)
        self.tool.doubleClicked.connect(self.doubleClicked)
        self.tool.deactivated.connect(self.tooldeactivated)

    def deactivate(self):
        log('deactivated', LEVEL_INFO)
        try:
            self.tool.moved.disconnect(self.moved)
            self.tool.rightClicked.disconnect(self.rightClicked)
            self.tool.leftClicked.disconnect(self.leftClicked)
            self.tool.doubleClicked.disconnect(self.doubleClicked)
            self.tool.deactivated.disconnect(self.tooldeactivated)
            self.canvas.unsetMapTool(self.tool)
            self.iface.mainWindow().statusBar().showMessage( "" )
        except:
            log('deactivate: self.tool probably does not exist', LEVEL_WARNING)
            pass
    
    def doRubberbandProfile(self):
        layerString = self.cbDEM.currentText()
        log('sampling ' + layerString, LEVEL_INFO)
        # Extract layer name (remove CRS suffix)
        layer_name = ' '.join(layerString.split(' ')[:-1])
        layer = utils.getLayerByName(layer_name)
        
        if layer is None:
            QMessageBox.warning(self,'Error',
                                'Selected DEM/Mesh layer is missing')
            return [None, 'error']
        
        try:
            if layer.isValid():
                # For raster layers, get resolution; for mesh layers, use a default resolution
                from qgis.core import QgsMapLayer
                if layer.type() == QgsMapLayer.RasterLayer:
                    self.xRes = layer.rasterUnitsPerPixelX()
                else:
                    # For mesh layers, use a reasonable default resolution
                    self.xRes = 1.0
        except:
            QMessageBox.warning(self,'Error',
                                'Selected DEM/Mesh layer is missing')
            return [None, 'error']
        
        line = LineString(self.pointstoDraw[:-1])
        xyzdList = utils.elevationSampler(line, self.xRes, layer)
        sta = xyzdList[-1]
        elev = xyzdList[-2]
        x_coords = xyzdList[0]
        y_coords = xyzdList[1]

        # --- diagnostic ---
        # for xi, yi, zi, si in zip(x_coords, y_coords, elev, sta):
            # log('station {:.2f}  x={:.2f} y={:.2f}  z={}'.format(si, xi, yi, zi), LEVEL_INFO)
            # log('mesh extent: {}'.format(layer.extent().toString()), LEVEL_INFO)
        # --- end diagnostic ---
        staElev = np.column_stack((sta, elev))
        log(str(staElev), LEVEL_INFO)
        try:
            np.isnan(np.sum(staElev[:,1]))
            return [staElev, None]
        except:
            QMessageBox.warning(self,'Error',
                                'Sampled line not within bounds of DEM/Mesh (perhaps layer CRS is different from project CRS)')
            return [staElev, 'error']
            
    def doIrregularProfileFlowEstimator(self, staElevPrev):
        thalweig = self.staElev[np.where(self.staElev[:,1] == np.min(self.staElev[:,1]))] 
        thalweigX = thalweig[:,0][0]
        minElev = thalweig[:,1][0]+.01
        try:
            lbMaxEl = self.staElev[np.where(self.staElev[:,0]>thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            self.staElev = staElevPrev
            return
        try:
            rbMaxEl = self.staElev[np.where(self.staElev[:,0]<thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            self.staElev = staElevPrev
            return 
        maxElev = np.array([lbMaxEl,rbMaxEl]).min()-0.001
        WSE = maxElev
        WSE = (self.staElev[:,1].max() - self.staElev[:,1].min())/2. + self.staElev[:,1].min()
        self.cbWSE.setValue(WSE)
        self.cbWSE.setMinimum(minElev)
        self.cbWSE.setMaximum(maxElev)
        self.cbUDwse.setValue(WSE)
        self.cbUDwse.setMinimum(minElev)
        self.cbUDwse.setMaximum(maxElev)

    def doRubberbandSlopeEstimator(self, staElev):
        slope = -(staElev[:,1][-1] - staElev[:,1][0])/staElev[:,0][-1]
        self.axes.clear()
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)
        self.axes.plot(staElev[:,0],staElev[:,1], 'k',label = 'Sampled DEM')
        x = np.array([staElev[0,0], staElev[-1,0]])
        y = np.array([staElev[0,1], staElev[-1,1]])
        self.axes.plot(x,y, label = 'Slope')
        self.axes.set_xlabel('Station, '+self.units)
        self.axes.set_ylabel('Elevation, '+self.units)
        self.axes.set_title('DEM Derived Slope = '+str(slope.astype('U8')))
        self.axes.legend()
        self.mplCanvas.draw()
        if slope<=0:
            QMessageBox.warning(self,'Error',
                                'Negative or zero slope\nPlease check sampled area\n\nWater flows downhill you know!')
        else:
            reply = QMessageBox.question(self,'Message',
            'DEM Derived Slope is {}\nWould you like to use this value?'.format(str(slope.astype('U8'))), MSGBOX_YES| 
            MSGBOX_NO, MSGBOX_YES)
            if reply == MSGBOX_YES:
                self.slope.setValue(slope)

    def writeDirName(self):
        self.outputDir.clear()
        self.dirName = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        self.outputDir.setText(self.dirName)
        
    def loadTxt(self):
        try:
           filePath, __ = QFileDialog.getOpenFileNameAndFilter(self, 'Select tab or space delimited text file containing station and elevation data')
        except:
           filePath, __ = QFileDialog.getOpenFileName(self, 'Select tab or space delimited text file containing station and elevation data')
        self.inputFile.setText(filePath)
        log('filePath: ' + filePath, LEVEL_INFO)
        staElevPrev = self.staElev
        try:
            self.staElev = np.pad(np.loadtxt(filePath, usecols=(0, 1)), ((0,0), (0,1)), mode='constant', constant_values=0)
            d = np.diff(self.staElev[:,:2], axis=0)
            self.staElev[1:,2] = np.cumsum(np.sqrt(np.sum(d*d, axis = 1)))
            self.calcType = 'UD' 
            self.doIrregularProfileFlowEstimator(staElevPrev)
        except:
            self.staElev = staElevPrev
            if (filePath == ('')): # null string for cancel
                return
            QMessageBox.warning(self,'Error',
                                'Please check that the text file is space or tab delimited and does not contain header information')
        
    def accept(self):
        self.run()
        outPath = self.outputDir.text()
        home = os.path.expanduser("~")
        if outPath == '':
            outPath = os.path.join(home,'Desktop','QGISFlowEstimatorFiles')
            self.outputDir.setText(outPath)
        if not os.path.exists(outPath):
            os.makedirs(outPath)
        fileName = outPath + '/FlowEstimatorResults.txt'
        fileName2 = outPath + '/FlowEstimatorXS.txt'
        with open(fileName,'w') as outFile, open(fileName2,'w') as inFile:
            outHeader = '*'*20 + '\nFlow Estimator - A QGIS plugin\nEstimates uniform, steady flow in a channel using Mannings equation\n' + '*'*20
            if self.calcType == 'DEM' or self.calcType == 'UD':
                if self.staElev.size == 0:
                    log("No DEM/UD section", LEVEL_WARNING)
                    QMessageBox.warning(self,'Error',
                                    'Try cutting a section from DEM, or loading a UD section from file.')
                    return
                try:
                   proj4 = utils.getLayerByName(self.cbDEM.currentText().split(' EPSG')[0]).crs().toProj4()
                except:
                   proj4 = "Unknown"
                outHeader += '\n'*5 + 'Type:\tDEM/UD Cross Section\nUnits:\t{0}\nDEM Layer:\t{1}\nProjection (Proj4 format):\t{2}\nChannel Slope:\t{3:.06f}\nMannings n:\t{4:.02f}\n\n\n\nstation\televation\n'
                outFile.write(outHeader.format(self.units, self.cbDEM.currentText(), proj4, self.slope.value(), self.n.value()))
                np.savetxt(outFile, self.staElev[:,:2], fmt = '%.3f', delimiter = '\t')
                np.savetxt(inFile, self.staElev[:,:2], fmt = '%.3f', delimiter = '\t')
                wseMax = self.cbWSE.maximum()
                wseMin = self.cbWSE.minimum()
            else:
                outHeader += '\n'*5 + 'Type:\tTrapezoidal Channel\nUnits:\t{0}\nChannel Slope:\t{1:.06f}\nMannings n:\t{2:.02f}\nBottom Width:\t{3:.02f}\nRight Side Slope:\t{4:.02f}\nLeft Side Slope:\t{5:.02f}\n\n\n\n'
                outFile.write(outHeader.format(self.units, self.slope.value(), self.n.value(), self.botWidth.value(), self.rightSS.value(), self.leftSS.value()))
                wseMax = self.depth.value()
                wseMin = 0.001
            self.mplCanvas.print_figure(outPath + '/FlowEstimatorResultsXSFigure')
            outHeader = '\n\n\n\n\n\n\nwater surface elevation\tflow\tvelocity\tR\tarea\ttop width\tdepth\n'
            outFile.write(outHeader)
            step = 0.05
            wseList = []
            qList = []
            for wse in utils.frange(wseMin, wseMax, step):
                if self.calcType == 'DEM' or self.calcType == 'UD':
                    args = flowEstimator(wse, self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                else:
                    args = flowEstimator(wse, self.n.value(), self.slope.value(), widthBottom = self.botWidth.value(), rightSS = self.rightSS.value(), leftSS = self.leftSS.value(), units = self.units)
                R, P, area, topWidth, Q, v, depth, xGround, yGround, yGround0, xWater, yWater, yWater0 = args
                data = '{0:.03f}\t{1:.02f}\t{2:.02f}\t{3:.02f}\t{4:.02f}\t{5:.02f}\t{6:.02f}\n'.format(wse, Q, v, R, area, topWidth, depth)
                outFile.write(data)
                wseList.append(wse)
                qList.append(Q)
            
            self.axes.clear()
            formatter = ScalarFormatter(useOffset=False)
            self.axes.yaxis.set_major_formatter(formatter)
            self.axes.plot(qList, wseList, 'k',label = 'Rating Curve')
            self.axes.set_ylabel('Water Surface Elevation, '+self.units)
            self.axes.set_xlabel('Discharge, {0}$^3$/s'.format(self.units))
            self.axes.set_title('Rating Curve')
            self.axes.grid()
            self.mplCanvas.draw()
            self.mplCanvas.print_figure(outPath + '/FlowEstimatorRatingCurve')          
        
        self.iface.messageBar().pushMessage("Flow Estimator", 'Output files saved to {}'.format(outPath),duration=30)
