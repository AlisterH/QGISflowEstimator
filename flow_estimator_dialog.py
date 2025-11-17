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

# try:
    # from matplotlib.backends.qt_compat import is_pyqt5
# except ImportError:
    # # won't this break it on QGIS 2?
	# def is_pyqt5():
		# from matplotlib.backends.qt_compat import QT_API
		# return QT_API == u'PyQt5'
# can this ever be false?
# if is_pyqt5():
    # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# else:
    # from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
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

# better than print(), although the docs suggest we should use QgsLogger for logging
def log(message):
    return QgsMessageLog.logMessage(message,'Flow Estimator', 0) # 0 is level=Qgis.Info in QGIS3`
# I saw it as a lambda, but find that less comprehensible:
#def log(): = lambda m: QgsMessageLog.logMessage(m,'Flow Estimator', 0)

# log the versions we are running, because why not?
from qgis.utils import pluginMetadata
log("QGIS " + Qgis.QGIS_VERSION)
log('Flow Estimator version ' + pluginMetadata('FlowEstimator','Version'))

if Qgis.QGIS_VERSION_INT > 29000: # Hide and show works on QGIS3, mostly... although occasionally not!
# Disabling Nov 2025 as it often doesn't work now (due to newer QGIS? QT? Windows 11?)
    HIDE_ENABLED='False' # Change to false if you can't cope with the show failing every now and then.
else: # Don't change this - hide works on QGIS2, but not show!
    HIDE_ENABLED='False'

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'flow_estimator_dialog_base.ui'))

# Will use resource.py rather than resources_rc.py, which causes a problem if the resources file is referenced in the .ui file
# But the main resources import doesn't work with plain "resources"!  I thought it must have been an issue with the plugin builder when FlowEstimator was created, which must be fixed by now...
# But it seems the plugin reloader unloads and loads things slightly differently, so that might be the problem instead. 
# FORM_CLASS, _ = uic.loadUiType(os.path.join(
    # os.path.dirname(__file__), 'flow_estimator_dialog_base.ui'), resource_suffix='')

class FlowEstimatorDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(FlowEstimatorDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        #QDialog.__init__(self, None, Qt.WindowStaysOnTopHint)
        self.iface = iface
        self.setupUi(self)
        
        self.btnOk = self.buttonBox.button(QDialogButtonBox.Save)
        #ajh: it seems this wasn't working, so I have changed from a stock OK button to a stock Save button
        #self.btnOk.setText("Save Data")
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close) 
        self.btnBrowse.clicked.connect(self.writeDirName)
        self.btnLoadTXT.clicked.connect(self.loadTxt)
        # ajh trying to make it work
        #self.inputFile.textChanged.connect(self.run)
        self.btnSampleLine.setEnabled(False)
        self.btnSampleSlope.setEnabled(False)
        self.calcType = 'Trap'
        
        # add shortcut keys to zoom in the documentation tab, because why not?
        # pinch zoom and crtl+scroll already work by default, although zooming is impossible if a font size is set
        # I guess it would be nice to add zooming to the context menu too, or provide buttons
        QShortcut(QKeySequence('Ctrl++'), self.textBrowser, self.textBrowser.zoomIn)
        QShortcut(QKeySequence('Ctrl+-'), self.textBrowser, self.textBrowser.zoomOut)
      
        # add matplotlib figure to dialog
        self.figure = Figure()
        # this controls the size of the whole dialog; if we get resizing working again I guess we need to add `, forward=True`
        self.figure.set_size_inches(6, 2.8)
        self.axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.12, bottom=0.15, right=.75, top=.9, wspace=None, hspace=.2) # It would be nice to change this when plotting slope or rating curve, so there isn't a blank space to the right of the graph.
        self.mplCanvas = FigureCanvas(self.figure)
        
        
        #self.widgetPlotToolbar = NavigationToolbar(self.mplCanvas, self.widgetPlot)
        #lstActions = self.widgetPlotToolbar.actions()
        #self.widgetPlotToolbar.removeAction(lstActions[7])
        self.vLayout.addWidget(self.mplCanvas)
        #log(str(self.vLayout.minimumSize()))
        #self.vLayout.addWidget(self.widgetPlotToolbar)

        # ajh: change the colours; perhaps we could use a stylesheet instead
        # ajh: can change the colour outside the actual graph like this
        #self.figure.patch.set_facecolor("blue")
        # ajh: default transparency is 1.0; good since otherwise the exported graphs have illegible axes in Windows explorer preview due to being fully transparent, and in QGIS if using a dark theme.
        #self.figure.patch.set_alpha(0.5)
        # ajh: patch (fill) is shown by default; good as per comment above
        #self.figure.patch.set_visible(False)
        # ajh: can change the background colour of the main plot like this:
        #self.axes.set_facecolor("#eafff5")
        # ajh: these don't seem to do anything
        #self.axes.patch.set_facecolor("#eafff5")
        #self.axes.patch.set_visible(True)
        #self.axes.patch.set_alpha(0.0)
        
        
        # and configure matplotlib params
#        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
#        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
#        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
#        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
#        rcParams["font.monospace"] = "Courier New, Liberation Mono"
#        
        #print self.cbDEM.changeEvent
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
        # ajh: this doesn't fix it
        #self.btnRefresh.clicked.connect(self.run)
		
        self.manageGui() 
        # ajh: I thought this would work around the crashes, but it doesn't work properly - it only sets a maximum size (almost - it can still be made slightly taller!)
        #self.setFixedSize(self.size())
        # even this doesn't help
        #self.setMinimumSize(self.size())
        self.btnSampleLine.clicked.connect(self.sampleLine)
        self.btnSampleSlope.clicked.connect(self.sampleSlope)
       
        # initialise cross-section station-elevation table
        # must initialise it properly (not as None) to allow testing it when saving)
        self.staElev = np.array([])
        
	    # it seems nothing has the keyboard focus initially unless we set it manually
        self.tabWidget.setFocus()

    # need this to make sure map tool is disconnected if the dialog is closed while it is in use
    def closeEvent(self, event):
        self.deactivate()

    def manageGui(self):
        log('manageGui')
        self.cbDEM.clear()
        if utils.getRasterLayerNames():
            self.cbDEM.addItems(utils.getRasterLayerNames())
            self.btnSampleLine.setEnabled(True)
            self.btnSampleSlope.setEnabled(True)           
        self.run()
        
#    def refreshPlot(self):
#        self.axes.clear()

    def plotter(self):

        R, P, area, topWidth, Q, v, depth, xGround, yGround, yGround0, xWater, yWater, yWater0 = self.args
        self.axes.clear()
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)
        ground = self.axes.plot(xGround, yGround, 'k')
        #self.axes.fill_between(xGround, yGround, yGround0, where=yGround>yGround0, facecolor='0.9', interpolate=True)
        if Q != 0:
            water = self.axes.plot(xWater, yWater, 'blue')
            self.axes.fill_between(xWater, yWater, yWater0, where=yWater>=yWater0, facecolor='blue', interpolate=True, alpha = 0.1)
        if self.calcType == 'DEM': # ajh: only difference between this and UD channel (below) is using self.cbWSE.value vs self.cbUDwse.value
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nWSE: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}$^2$\nWetted P: {9:,.2f} {5}\nR: {0:.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), P, self.cbWSE.value()) 
        elif self.calcType == 'UD': # ajh: only difference between this and DEM channel (above) is using self.cbWSE.value vs self.cbUDwse.value
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nWSE: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}\nWetted P: {9:,.2f} {5}$^2$\nR: {0:.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), P, self.cbUDwse.value()) 
        else: # self.calcType == 'trap'
            self.outText = 'INPUT\n\nSlope: {7:.4f}\nRoughness: {8:.3f}\nDepth: {10:.2f} {5}\n\nCALCULATED\n\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nArea: {1:,.2f} {5}$^2$\nWetted P: {9:,.2f} {5}\nR: {0:.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), P, self.depth.value()) 
        self.axes.set_xlabel('Station, '+self.units)
        self.axes.set_ylabel('Elevation, '+self.units)
        self.axes.set_title('Cross Section')
        #self.axes.set_ylim(bottom=0)
        #self.axes.show() 
        
        #print self.outText
# ajh: we currently have no reason to use a separate function for this
        #self.refreshPlotText()

    
#    def refreshPlotText(self):

        self.axes.annotate(self.outText, xy=(.76,0.02), xycoords='figure fraction')
        
        # enable mouseover coordinate display if mplcursors is available
        # using click coordinate display instead could be desirable, to output it when saving results, but we currently recalculate when saving, which clears it
  #      if MPLCURSORS == "installed":
        #	disabling as it is causing constant crashes
  #          mplcursors.cursor(ground, hover=mplcursors.HoverMode.Transient)
            # we can do this as well, but it is a bit weird interacting with both of them
            # mplcursors.cursor(water, hover=True)
        
        #at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
        #self.axes.add_artist(at)
        self.mplCanvas.draw()
        
    def run(self):
        if self.ft.isChecked():
            self.units = 'ft'
        else:
            self.units = 'm'
            
        if self.tabWidget.currentIndex() == 0:
            log('calc trap channel')
            self.calcType = 'Trap'
            self.args = flowEstimator(self.depth.value(), self.n.value(), self.slope.value(), widthBottom = self.botWidth.value(), rightSS = self.rightSS.value(), leftSS = self.leftSS.value(), units = self.units)
            self.figure.patch.set_facecolor("white")
            self.plotter()
        elif self.tabWidget.currentIndex() == 1: # ajh: only difference between this and UD channel (below) is using self.cbWSE.value vs self.cbUDwse.value
            log('calc DEM channel')
            try:
                self.calcType = 'DEM'																										          # ajh: TODO combine with DEM channel below
#                print self.cbWSE.value(), self.n.value(), self.slope.value(), self.staElev, self.units
                self.args = flowEstimator(self.cbWSE.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                QgsMessageLog.logMessage('could not solve; is the cross-section very unusual?','Flow Estimator', 2) # 2 is level=Qgis.Critical in QGIS3
                #doesn't seem to do anything: #self.mplCanvas.setEnabled(False)
                #this doesn't help #self.plotter()
                self.figure.patch.set_facecolor("red")
                #self.axes.clear()
                self.mplCanvas.draw()
        else: # ajh: only difference between this and DEM channel (above) is using self.cbWSE.value vs self.cbUDwse.value
            log('calc UD channel')
            try:
                self.calcType = 'UD'																										          # ajh: TODO combine with DEM channel above
                #log(str(self.staElev))
                #print 'self.cbUDwse.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units'
                self.args = flowEstimator(self.cbUDwse.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                QgsMessageLog.logMessage('could not solve; is the cross-section very unusual?','Flow Estimator', 2) # 2 is level=Qgis.Critical in QGIS3
                #doesn't seem to do anything: #self.mplCanvas.setEnabled(False)
                #this doesn't help #self.plotter()
                self.figure.patch.set_facecolor("red")
                #self.axes.clear()
                self.mplCanvas.draw()
                
            
   
    def sampleLine(self):
        if HIDE_ENABLED == 'True':
            log('hide sampleLine')
            self.hide() # stops everything from working in QGIS2
        else:
            #ajh don't need this if we are doing hide and show
            self.btnSampleSlope.setEnabled(False) #simplest to do both
            self.btnSampleLine.setEnabled(False)
        self.iface.mainWindow().activateWindow()
        self.sampleBtnCode = 'sampleLine'
        self.rubberBand()

 
        
    def sampleSlope(self):
        if HIDE_ENABLED == 'True':
            log('hide sampleSlope')
            self.hide() # stops everything from working in QGIS2
        else:
            #ajh don't need this if we are doing hide and show; and it is a problem if the tool is deactivated
            self.btnSampleSlope.setEnabled(False) 
            self.btnSampleLine.setEnabled(False) #simplest to do both
        self.iface.mainWindow().activateWindow()
        self.sampleBtnCode = 'sampleSlope'
        self.rubberBand()
#==============================================================================
# START rubberband and related functions from
#       https://github.com/etiennesky/profiletool
#==============================================================================
    def rubberBand(self):
     
        log('rubberband')
        self.canvas = self.iface.mapCanvas()
        #Init class variables
        if self.sampleBtnCode=='sampleLine':
            self.tool = ProfiletoolMapTool(self.canvas, self.btnSampleLine)        #the mouselistener
        else:
            self.tool = ProfiletoolMapTool(self.canvas, self.btnSampleSlope)        #the mouselistener
        self.pointstoDraw = None    #Polyline in mapcanvas CRS analysed
        self.dblclktemp = False        #enable distinction between leftclick and doubleclick
        # ajh: we would need to do more work to support selectionmethod = 1
        self.selectionmethod = 0                        #The selection method defined in option
        # ajh: if we restore the savetool on deactivate it receives a click after our double-click; very annoying, so we won't use it
        #self.saveTool = self.canvas.mapTool()            #Save the standard maptool for restoring it at the end
        self.textquit0 = "Click for polyline and double click to end (right click to cancel)"
        self.textquit1 = "Select the polyline in a vector layer (Right click to quit)"
        #Listeners of mouse
        self.connectTool()
        #init the mouse listener comportement and save the classic to restore it on quit
        self.canvas.setMapTool(self.tool)
        #init the temp layer where the polyline is draw
        self.polygon = QgsWkbTypes.LineGeometry
        self.rubberband = QgsRubberBand(self.canvas, self.polygon)
        self.rubberband.setWidth(2)
        if self.sampleBtnCode == 'sampleLine':
            color = Qt.red
        else:
            color = Qt.blue
        self.rubberband.setColor(QColor(color))
        #init the table where is saved the polyline
        self.pointstoDraw = []
        self.pointstoCal = []
        self.lastClicked = [[-9999999999.9,9999999999.9]]
        # The last valid line we drew to create a free-hand profile
        self.lastFreeHandPoints = []
        #Help about what doing
        if self.selectionmethod == 0:
            self.iface.mainWindow().statusBar().showMessage(self.textquit0)
        elif self.selectionmethod == 1:
            self.iface.mainWindow().statusBar().showMessage(self.textquit1)

    #************************************* Mouse listener actions ***********************************************
    
    def moved(self,position):            #draw the polyline on the temp layer (rubberband)
        #print 'moved'
        if self.selectionmethod == 0:
            if len(self.pointstoDraw) > 0:
                #Get mouse coords
                mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
                try:
                    self.rubberband.reset(QgsWkbTypes.LineGeometry) #should perhaps do something like `if is_pyqt5()` instead of try
                except:
                    self.rubberband.reset(Qgis.Line)
                for i in range(0,len(self.pointstoDraw)):
                     self.rubberband.addPoint(QgsPointXY(self.pointstoDraw[i][0],self.pointstoDraw[i][1]))
                self.rubberband.addPoint(QgsPointXY(mapPos.x(),mapPos.y()))
#        if self.selectionmethod == 1:
#            return


    def tooldeactivated(self):
        log('show deactivated')
        # self.rubberband.reset(self.polygon) # don't think we need this here
        self.tool.moved.disconnect(self.moved)
        self.tool.rightClicked.disconnect(self.rightClicked)
        self.tool.leftClicked.disconnect(self.leftClicked)
        self.tool.doubleClicked.disconnect(self.doubleClicked)
        self.tool.deactivated.disconnect(self.tooldeactivated)
        self.canvas.unsetMapTool(self.tool) # ajh: don't seem to need this elsewhere, so maybe not here too
        self.iface.mainWindow().statusBar().showMessage( "" )
        if HIDE_ENABLED == 'False':
            # ajh2: don't actually need this if we are doing hide and show instead of deactivating the button
            # ajh: need this otherwise the plugin needs to be restarted to reenable the button
            self.btnSampleLine.setEnabled(True)
            self.btnSampleSlope.setEnabled(True) 
            # ajh2: don't seem to need this now
            # ajh: need to raise the window
            self.activateWindow()
        self.show()


    def rightClicked(self,position):    #used to quit the current action
        log('rightclicked')
        if self.selectionmethod == 0:
            if len(self.pointstoDraw) > 0:
                self.pointstoDraw = []
                self.pointstoCal = []
                self.rubberband.reset(self.polygon)
            else:
                self.tooldeactivated()


    def leftClicked(self,position):        #Add point to analyse
        log('leftclicked')
        mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
        newPoints = [[mapPos.x(), mapPos.y()]]
        if self.selectionmethod == 0:
            if newPoints == self.dblclktemp:
                self.dblclktemp = None
                return
            else :
                if len(self.pointstoDraw) == 0:
                    self.rubberband.reset(self.polygon)
                self.pointstoDraw += newPoints


    def doubleClicked(self,position):
        log('doubleclicked')
        # ajh: doing show first avoids problems with dialog not showing in some cases after running slope estimator
        # and it also means the user can see the graph before deciding whether to accept the slope
        self.show()
        if HIDE_ENABLED == 'False':
            # ajh: trying to make something like this work:
            #self.iface.mainWindow.setWindowState(self.iface.mainWindow.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            #self.iface.mainWindow.raise_()
            #self.iface.mainWindow.show()
            
            # ajh: thought this just wasn't working on windows as per
            # https://stackoverflow.com/questions/22815608/how-to-find-the-active-pyqt-window-and-bring-it-to-the-front
            # see https://forum.qt.io/topic/1939/activatewindow-does-not-send-window-to-front/11
            #self.iface.mainWindow.activateWindow()
            
            # but actually, this is the solution:
            self.activateWindow()
        if self.selectionmethod == 0: #ajh: TODO investigate  this check
            #Validation of line
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
            newPoints = [[mapPos.x(), mapPos.y()]]
            log('newPoints ' + str(newPoints))
            self.pointstoDraw += newPoints
            log('self.pointstoDraw ' + str(self.pointstoDraw))
            log('len(self.pointstoDraw) ' + str(len(self.pointstoDraw)))
            #launch analyses
            self.iface.mainWindow().statusBar().showMessage(str(self.pointstoDraw))
            if len(self.pointstoDraw) < 3: # double-click has two identical points; perhaps can delete this if we change from using double clicks 
                QMessageBox.warning(self,'Error',
                                         'Draw a section with more than one point')
            else:
                if self.sampleBtnCode == 'sampleLine':
                    staElevPrev = self.staElev
                    staElev, error = self.doRubberbandProfile()
                    if error:
                        pass
                        #ajh it would be good to restart the selection again after an error
                    else:
                        self.staElev = np.pad(staElev, ((0,0), (0,1)), mode='constant', constant_values=0) # Could we move all this logic for the third column to openChannel.py?
                        d = np.diff(staElev, axis=0)
                        self.staElev[1:,2] = np.cumsum(np.sqrt(np.sum(d*d, axis = 1)))
                        self.doIrregularProfileFlowEstimator(staElevPrev)
                        #log('self.staElev' + str(self.staElev))
                        #log('staElevPrev' + str(staElevPrev))
                else:
                    staElev, error = self.doRubberbandProfile()
                    if error:
                        pass
                        #ajh it would be good to restart the selection again after an error
                    else:
                        self.doRubberbandSlopeEstimator(staElev)

            #Reset
            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            #temp point to distinct leftclick and dbleclick
            self.dblclktemp = newPoints
            self.iface.mainWindow().statusBar().showMessage( "" )
            #ajh don't need this if we are doing hide and show
            if HIDE_ENABLED == 'False':
                self.btnSampleLine.setEnabled(True)
                self.btnSampleSlope.setEnabled(True)
            self.deactivate()

            return


###***********************************************
            
    def connectTool(self):
        log('connecting')
        self.tool.moved.connect(self.moved)
        self.tool.rightClicked.connect(self.rightClicked)
        self.tool.leftClicked.connect(self.leftClicked)
        self.tool.doubleClicked.connect(self.doubleClicked)
        self.tool.deactivated.connect(self.tooldeactivated)

    def deactivate(self):        #enable clean exit of the plugin
                                 #? not sure that comment was right as this is for deactivating the map tool, not the plugin
        log('deactivated')
        try:
            self.rubberband.reset(self.polygon)
            self.tool.moved.disconnect(self.moved)
            self.tool.rightClicked.disconnect(self.rightClicked)
            self.tool.leftClicked.disconnect(self.leftClicked)
            self.tool.doubleClicked.disconnect(self.doubleClicked)
            self.tool.deactivated.disconnect(self.tooldeactivated)
            self.canvas.unsetMapTool(self.tool) # ajh: don't seem to need this
            self.iface.mainWindow().statusBar().showMessage( "" ) # ajh: I guess there might have been a statusBar message associated with the saveTool which we should restore if we reenable it.
            # self.canvas.setMapTool(self.saveTool) # ajh: after we do this for some reason it sends a click to the saveTool; we don't want that.
        except:
            QgsMessageLog.logMessage('error in deactivate','Flow Estimator', 2)
            pass
#        self.rubberband.reset(self.polygon)
#        self.iface.mainWindow().statusBar().showMessage("")
        
#        self.depth.setEnabled(True)
#        self.botWidth.setEnabled(True)
#        self.leftSS.setEnabled(True)
#        self.rightSS.setEnabled(True)
#        self.n.setEnabled(True)
#        self.slope.setEnabled(True)
#        self.cbWSE.setEnabled(True)
#        self.ft.setEnabled(True)
#        self.m.setEnabled(True)
#        self.cbDEM.setEnabled(True)
    
    def doRubberbandProfile(self):
        layerString = self.cbDEM.currentText()
        log('sampling ' + layerString)
        layer = utils.getRasterLayerByName(' '.join(layerString.split(' ')[:-1]))
        try:
            if layer.isValid():
                self.xRes = layer.rasterUnitsPerPixelX()
        except:
            QMessageBox.warning(self,'Error',
                                'Selected DEM layer is missing')
            return [None, 'error']
        line = LineString(self.pointstoDraw[:-1]) 
#        log('xyzdList start')
#        QApplication.processEvents()
        # ajh: TODO this line is the slow part, expecially if we accidentally sample an aerial photo or something.
        # we actually only need a zdlist.
        # we may be able to optimise it by only returning what we need, creating the x y d values with numpy, and other optimisations
        # but I suspect in reality it all comes down to the provider speed
        xyzdList = utils.elevationSampler(line,self.xRes, layer)
#        log('xyzdList end')
#        QApplication.processEvents()
        sta = xyzdList[-1]
        #log(str(sta))
        elev = xyzdList[-2]
        #log(str(elev))
        # ajh: I understand np.column_stack is more efficient
        staElev = np.column_stack((sta, elev))
        # we can just do this if we change the input to just d z
        #staElev = np.column_stack(dzList)
        #staElev = np.array(list(zip(sta, elev)))
        log(str(staElev))
        try:
            np.isnan(np.sum(staElev[:,1]))
            return [staElev, None]
        except:
            # ajh: sometimes this is not true; I think it is some kind of error communicating with the provider
            # (I am testing with files on a network drive, over a VPN)
            # or perhaps somehow due to suspending the machine and then waking it up again
            QMessageBox.warning(self,'Error',
                                'Sampled line not within bounds of DEM (perhaps layer CRS is different from project CRS)')
            #log(str(staElev))
            # ajh: don't think we need this
            #self.cleaning()
            
            return [staElev, 'error']
            
            
        
    def doIrregularProfileFlowEstimator(self, staElevPrev):
        # ajh: should review this code, given changes to openChannel.py (use the median?)
        thalweig = self.staElev[np.where(self.staElev[:,1] == np.min(self.staElev[:,1]))] 
        thalweigX = thalweig[:,0][0]
        minElev = thalweig[:,1][0]+.01
        try:
            lbMaxEl = self.staElev[np.where(self.staElev[:,0]>thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            # ajh: don't think we need this
            #self.deactivate()
            self.staElev = staElevPrev
            return
        try:
            rbMaxEl = self.staElev[np.where(self.staElev[:,0]<thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            # ajh: don't think we need this
            #self.deactivate()
            self.staElev = staElevPrev
            return 
        maxElev = np.array([lbMaxEl,rbMaxEl]).min()-0.001 # ajh: let the user set WSE up to 1mm (if units in m) below the crest; I think if we remove this restriction it can cause a rounding error # can change to e.g. +0.001 for testing
        WSE = maxElev
        WSE = (self.staElev[:,1].max() - self.staElev[:,1].min())/2. + self.staElev[:,1].min()
        self.cbWSE.setValue(WSE)# calls self.run, which calls flowEstimator
        self.cbWSE.setMinimum(minElev)
        self.cbWSE.setMaximum(maxElev)
        self.cbUDwse.setValue(WSE)# calls self.run, which calls flowEstimator
        self.cbUDwse.setMinimum(minElev)
        self.cbUDwse.setMaximum(maxElev)
        # ajh: doing it like this might be beneficial if switch from WSE to UD (or vice versa) and then fail to load a section succcessfully 
        # as it was it just meant we had a section with the wrong minimum and maximum values if we switched, loaded a section successfully, and then switched back
        # if we are going to do it this way we should store two different sections (one for each tab) and reload when we switch tabs
        # if self.tabWidget.currentIndex() == 1:
            # self.cbWSE.setValue(WSE)
            # self.cbWSE.setMinimum(minElev)
            # self.cbWSE.setMaximum(maxElev)
        # elif self.tabWidget.currentIndex() == 2:
            # self.cbUDwse.setValue(WSE)
            # self.cbUDwse.setMinimum(minElev)
            # self.cbUDwse.setMaximum(maxElev)
        # else:
            # return

        # ajh: I don't think this was doing anything
        #self.run()

        
    def doRubberbandSlopeEstimator(self, staElev):
         
        slope = -(staElev[:,1][-1] - staElev[:,1][0])/staElev[:,0][-1]
        #log(str(slope))

        self.axes.clear()
        
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)
        self.axes.plot(staElev[:,0],staElev[:,1], 'k',label = 'Sampled DEM')
        x = np.array([staElev[0,0], staElev[-1,0]])
        y = np.array([staElev[0,1], staElev[-1,1]])
        self.axes.plot(x,y, label = 'Slope')
        self.axes.set_xlabel('Station, '+self.units)
        self.axes.set_ylabel('Elevation, '+self.units)
        #self.axes.set_title('DEM Derived Slope = '+str(slope))
        self.axes.set_title('DEM Derived Slope = '+str(slope.astype('U8')))
        self.axes.legend()
        self.mplCanvas.draw()
        if slope<=0:
            QMessageBox.warning(self,'Error',
                                'Negative or zero slope\nPlease check sampled area\n\nWater flows downhill you know!')
            QgsMessageLog.logMessage('error: negative slope', 'Flow Estimator') # default is warning (1)
        else:
            reply = QMessageBox.question(self,'Message',
            'DEM Derived Slope is {}\nWould you like to use this value?'.format(str(slope.astype('U8'))), QMessageBox.Yes| 
            QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.slope.setValue(slope)

            else:
                pass
            
    def writeDirName(self):
        self.outputDir.clear()
        self.dirName = QFileDialog.getExistingDirectory(self, 'Select Output Directory')
        self.outputDir.setText(self.dirName)
        
    def loadTxt(self):
        try:
           filePath, __ = QFileDialog.getOpenFileNameAndFilter(self, 'Select tab or space delimited text file containing station and elevation data') # QGIS2 (using this rather than getOpenFileName will avoid opening a dialog twice)
        except:
           filePath, __ = QFileDialog.getOpenFileName(self, 'Select tab or space delimited text file containing station and elevation data')
        self.inputFile.setText(filePath)
        log('filePath: ' + filePath)
        staElevPrev = self.staElev
        try:
            # ajh: np.loadtxt sends a normal warning for an empty file; we want most messages tagged and sent via QgsMessageLog, but QMessageBox below is sufficient in this case
            # we should be able to do this, but it doesn't seem to work.
            # we could alternatively test for an empty file ourselves
            #with warnings.catch_warnings():
            #    warnings.simplefilter("ignore")
            self.staElev = np.pad(np.loadtxt(filePath, usecols=(0, 1)), ((0,0), (0,1)), mode='constant', constant_values=0)
            d = np.diff(self.staElev[:,:2], axis=0)
            self.staElev[1:,2] = np.cumsum(np.sqrt(np.sum(d*d, axis = 1)))
            #log(str(self.staElev))
            self.calcType = 'UD' 
            self.doIrregularProfileFlowEstimator(staElevPrev)
        except:
            self.staElev = staElevPrev
            if (filePath == ('')): # null string for cancel
                return
            QMessageBox.warning(self,'Error',
                                'Please check that the text file is space or tab delimited and does not contain header information')
        
        
    def accept(self):
        # recalculate in case save has been hit twice (otherwise instead of saving the cross-section png it saves a second copy of the rating curve).
        self.run()
        outPath = self.outputDir.text()
        home = os.path.expanduser("~")
        if outPath == '':
            outPath = os.path.join(home,'Desktop','QGISFlowEstimatorFiles')
            self.outputDir.setText(outPath)
        # Note that in Python 3.2+ we can just do: os.makedirs("path/to/directory", exist_ok=True)                    
        if not os.path.exists(outPath):
            os.makedirs(outPath)
        fileName = outPath + '/FlowEstimatorResults.txt'
        fileName2 = outPath + '/FlowEstimatorXS.txt'
        # ajh I think we've fixed the file/folder locking problem on windows by not doing chdir to outPath
        # keeping these old comments just in case:
        # one way to prevent it may be to open like this:
        # outFile = open(fileName, 'w', False)
        # another way may be to do outFile = None after closing
        with open(fileName,'w') as outFile, open(fileName2,'w') as inFile:
            outHeader = '*'*20 + '\nFlow Estimator - A QGIS plugin\nEstimates uniform, steady flow in a channel using Mannings equation\n' + '*'*20
            if self.calcType == 'DEM' or self.calcType == 'UD':
                if self.staElev.size == 0:
                    QgsMessageLog.logMessage("No DEM/UD section", 'Flow Estimator') # default is warning (1)
                    # we could use the message bar, but I think it is quite good to make the user click through an error like this
                    QMessageBox.warning(self,'Error',
                                    'Try cutting a section from DEM, or loading a UD section from file.')
                    return
                try:
                   proj4 = utils.getRasterLayerByName(self.cbDEM.currentText().split(' EPSG')[0]).crs().toProj4()
                except:
                   proj4 = "Unknown"
                # For a UD section this will still list whatever layer is selected on the DEM tab, and its projection
                # Ideally we should track whether a DEM or UD section has been successfully loaded most recently, so we can tell the truth
                # Also, if you cut a section from one DEM, fail to cut a section from another DEM, and then save, the results will refer to the wrong file
                outHeader += '\n'*5 + 'Type:\tDEM/UD Cross Section\nUnits:\t{0}\nDEM Layer:\t{1}\nProjection (Proj4 format):\t{2}\nChannel Slope:\t{3:.06f}\nMannings n:\t{4:.02f}\n\n\n\nstation\televation\n'.format(self.units,self.cbDEM.currentText(), proj4, self.slope.value(), self.n.value())
                outFile.write(outHeader)
                np.savetxt(outFile, self.staElev[:,:2], fmt = '%.3f', delimiter = '\t')
                # the first time I ran after adding this it crashed...
                np.savetxt(inFile, self.staElev[:,:2], fmt = '%.3f', delimiter = '\t')
                # ajh: it is more useful to plot the full rating curve, rather than stopping at the specified WSE
                #wseMax = self.cbWSE.value()
                wseMax = self.cbWSE.maximum()
                wseMin = self.cbWSE.minimum()
            
            else:
                outHeader += '\n'*5 + 'Type:\tTrapezoidal Channel\nUnits:\t{0}\nChannel Slope:\t{1:.06f}\nMannings n:\t{2:.02f}\nBottom Width:\t{3:.02f}\nRight Side Slope:\t{4:.02f}\nLeft Side Slope:\t{5:.02f}\n'.format(self.units, self.slope.value(), self.n.value(), self.botWidth.value(), self.rightSS.value(), self.leftSS.value())
                outFile.write(outHeader)
                wseMax = self.depth.value()
                wseMin = 0.001
            self.mplCanvas.print_figure(outPath + '/FlowEstimatorResultsXSFigure')
            outHeader = '\n\n\n\n\n\n\nwater surface elevation\tflow\tvelocity\tR\tarea\ttop width\tdepth\n'
            outFile.write(outHeader)
            ###do loop here 
            step = 0.05 # ajh: 50mm steps allow us to produce a sane graph for reasonably shallow sections
            wseList = []
            qList = []
            #log("wseMax " + str(wseMax))
            #log("wseMin " + str(wseMin))
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
        
        # Using a with statement takes care of closing the file automatically
        #outFile.close()
        # ajh this may help force the file lock to be released
        #outFile = None
        
        self.iface.messageBar().pushMessage("Flow Estimator", 'Output files saved to {}'.format(outPath),duration=30)

