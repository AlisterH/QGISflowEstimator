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
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import zip
from builtins import range
import os

from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtGui import QColor, QKeySequence
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog, QDialogButtonBox, QShortcut
from qgis.PyQt.QtCore import Qt, QObject
from qgis.gui import QgsRubberBand
try:
    from qgis.core import QgsPointXY, QgsWkbTypes
except:
    from qgis.core import QGis, QgsPoint as QgsPointXY

# ajh: I gather we should code it like this, although for some reason qt4agg seems to work the same in QGIS3
from matplotlib.backends.qt_compat import is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
else:
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter

from . import FlowEstimator_utils as utils
from .openChannel import flowEstimator
from .ptmaptool import ProfiletoolMapTool

from shapely.geometry import LineString
import numpy as np


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'flow_estimator_dialog_base.ui'))


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
        self.figure.subplots_adjust(left=.12, bottom=0.15, right=.75, top=.9, wspace=None, hspace=.2)
        self.mplCanvas = FigureCanvas(self.figure)
        
        
        #self.widgetPlotToolbar = NavigationToolbar(self.mplCanvas, self.widgetPlot)
        #lstActions = self.widgetPlotToolbar.actions()
        #self.widgetPlotToolbar.removeAction(lstActions[7])
        self.vLayout.addWidget(self.mplCanvas)
        self.vLayout.minimumSize() 
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
        
        # it seems nothing has the keyboard focus initially unless we set it manually
        self.tabWidget.setFocus()

        self.manageGui() 
        # ajh: I thought this would work around the crashes, but it doesn't work properly - it only sets a maximum size (almost - it can still be made slightly taller!)
		#self.setFixedSize(self.size())
		# even this doesn't help
        #self.setMinimumSize(self.size())
        self.btnSampleLine.clicked.connect(self.sampleLine)
        self.btnSampleSlope.clicked.connect(self.sampleSlope)



    def manageGui(self):
        # fix_print_with_import
        print('manageGui')
        self.cbDEM.clear()
        if utils.getRasterLayerNames():
            self.cbDEM.addItems(utils.getRasterLayerNames())
            self.btnSampleLine.setEnabled(True)
            self.btnSampleSlope.setEnabled(True)           
        self.run()
        
#    def refreshPlot(self):
#        self.axes.clear()

    def plotter(self):

        R, area, topWidth, Q, v, depth, xGround, yGround, yGround0, xWater, yWater, yWater0 = self.args
        self.axes.clear()
        formatter = ScalarFormatter(useOffset=False)
        self.axes.yaxis.set_major_formatter(formatter)
        self.axes.plot(xGround, yGround, 'k')
        #self.axes.fill_between(xGround, yGround, yGround0, where=yGround>yGround0, facecolor='0.9', interpolate=True)
        if Q != 0:
            self.axes.plot(xWater, yWater, 'blue')
            self.axes.fill_between(xWater, yWater, yWater0, where=yWater>=yWater0, facecolor='blue', interpolate=True, alpha = 0.1)
        if self.calcType == 'DEM':
            self.outText = 'INPUT\n\nSlope: {7:.3f}\nRoughness: {8:.3f}\nWSE: {9:.2f} {5}\n\nCALCULATED\n\nR: {0:.2f} {5}\nArea: {1:,.2f} {5}$^2$\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), self.cbWSE.value()) 
        elif self.calcType == 'UD':
            self.outText = 'INPUT\n\nSlope: {7:.3f}\nRoughness: {8:.3f}\nWSE: {9:.2f} {5}\n\nCALCULATED\n\nR: {0:.2f} {5}\nArea: {1:,.2f} {5}$^2$\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), self.cbUDwse.value()) 
        else:
            self.outText = 'INPUT\n\nSlope: {7:.3f}\nRoughness: {8:.3f}\nDepth: {9:.2f} {5}\n\nCALCULATED\n\nR: {0:.2f} {5}\nArea: {1:,.2f} {5}$^2$\nTop Width: {2:.2f} {5}\nDepth: {6:,.2f} {5}\nQ: {3:,.3f} {5}$^3$/s\nVelocity {4:,.1f} {5}/s'.format(R, area, topWidth, Q, v, self.units, depth, self.slope.value(), self.n.value(), self.depth.value()) 
        self.axes.set_xlabel('Station, '+self.units)
        self.axes.set_ylabel('Elevation, '+self.units)
        self.axes.set_title('Cross Section')
        #self.axes.set_ylim(bottom=0)
        #self.axes.show() 
        
        #print self.outText
        self.refreshPlotText()

    
    def refreshPlotText(self):

        self.axes.annotate(self.outText, xy=(.76,0.17), xycoords='figure fraction')
        #at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
        #self.axes.add_artist(at)
        self.mplCanvas.draw()
        
    def run(self):
        if self.ft.isChecked():
            self.units = 'ft'
        else:
            self.units = 'm'
            
        if self.tabWidget.currentIndex() == 0:
            # fix_print_with_import
            print('calc trap channel')
            self.calcType = 'Trap'
            self.args = flowEstimator(self.depth.value(), self.n.value(), self.slope.value(), widthBottom = self.botWidth.value(), rightSS = self.rightSS.value(), leftSS = self.leftSS.value(), units = self.units)
            self.figure.patch.set_facecolor("white")
            self.plotter()
        elif self.tabWidget.currentIndex() == 1:
            try:
                self.calcType = 'DEM'
#                print self.cbWSE.value(), self.n.value(), self.slope.value(), self.staElev, self.units
                self.args = flowEstimator(self.cbWSE.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                self.figure.patch.set_facecolor("red")
                #doesn't seem to do anything: #self.mplCanvas.setEnabled(False)
                #don't think this does anything?: #self.axes.clear()
                #this doesn't help #self.plotter()
                self.mplCanvas.draw()
        else:
            
            try:
                self.calcType = 'UD'
                #print 'self.cbUDwse.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units'
                self.args = flowEstimator(self.cbUDwse.value(), self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
                self.figure.patch.set_facecolor("white")
                self.plotter()
            except:
                self.figure.patch.set_facecolor("red")
                #doesn't seem to do anything: #self.mplCanvas.setEnabled(False)
                #don't think this does anything?: #self.axes.clear()
                #this doesn't help #self.plotter()
                self.mplCanvas.draw()
                
            
   
    def sampleLine(self):
        self.hide()
        self.iface.mainWindow().activateWindow()
    #ajh don't need this if we are doing hide and show; and it is a problem if the tool is deactivated
        #self.btnSampleLine.setEnabled(False)  
        self.sampleBtnCode = 'sampleLine'
        self.rubberBand()

 
        
    def sampleSlope(self):
        self.hide()
        self.iface.mainWindow().activateWindow()
    #ajh don't need this if we are doing hide and show; and it is a problem if the tool is deactivated
        #self.btnSampleSlope.setEnabled(False) 
        self.sampleBtnCode = 'sampleSlope'
        self.rubberBand()
#==============================================================================
# START rubberband and related functions from
#       https://github.com/etiennesky/profiletool
#==============================================================================
    def rubberBand(self):
     
        # fix_print_with_import
        print('rubberband ') 
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
        self.saveTool = self.canvas.mapTool()            #Save the standard mapttool for restoring it at the end
        self.textquit0 = "Click for polyline and double click to end (right click to cancel)"
        self.textquit1 = "Select the polyline in a vector layer (Right click to quit)"
        #Listeners of mouse
        self.connectTool()
        #init the mouse listener comportement and save the classic to restore it on quit
        self.canvas.setMapTool(self.tool)
        #init the temp layer where the polyline is draw
        self.polygon = False
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
                    self.rubberband.reset(QgsWkbTypes.LineGeometry)
                except:
                    self.rubberband.reset(QGis.Line)
                for i in range(0,len(self.pointstoDraw)):
                     self.rubberband.addPoint(QgsPointXY(self.pointstoDraw[i][0],self.pointstoDraw[i][1]))
                self.rubberband.addPoint(QgsPointXY(mapPos.x(),mapPos.y()))
#        if self.selectionmethod == 1:
#            return

    def tooldeactivated(self):
        self.rubberband.reset(self.polygon)
        self.iface.mainWindow().statusBar().showMessage( "" )
        self.show()

    def rightClicked(self,position):    #used to quit the current action
        # fix_print_with_import
        print('rightclicked')
        if self.selectionmethod == 0:
            if len(self.pointstoDraw) > 0:
                self.pointstoDraw = []
                self.pointstoCal = []
                self.rubberband.reset(self.polygon)
            else:
                self.cleaning()
                # ajh2: don't actually need this now, as we hide the window instead of deactivating the button
                # ajh: need this otherwise the plugin needs to be restarted to reenable the button
                #if self.sampleBtnCode == 'sampleLine':
                #    self.btnSampleLine.setEnabled(True)
                #else :
                #    self.btnSampleSlope.setEnabled(True) 
                # ajh2: don't seem to need this now
                # ajh: need to raise the window
                #self.activateWindow()




    def leftClicked(self,position):        #Add point to analyse
        # fix_print_with_import
        print('leftclicked')
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
        # fix_print_with_import
        print('doubleclicked')
    # ajh: doing show first avoids problems with dialog not showing in some cases after running slope estimator
    # and it also means the user can see the graph before deciding whether to accept the slope
        self.show()
        if self.selectionmethod == 0:
            #Validation of line
            mapPos = self.canvas.getCoordinateTransform().toMapCoordinates(position["x"],position["y"])
            newPoints = [[mapPos.x(), mapPos.y()]]
            self.pointstoDraw += newPoints
            #launch analyses
            self.iface.mainWindow().statusBar().showMessage(str(self.pointstoDraw))
            
            if self.sampleBtnCode == 'sampleLine':
                self.staElev, error = self.doRubberbandProfile()
                if error:
                    pass
                    #ajh it would be good to restart the selection again after an error
                else:
                    self.doIrregularProfileFlowEstimator()
                #ajh don't need this if we are doing hide and show
                #self.btnSampleLine.setEnabled(True) 
                self.deactivate()
            else:
                staElev, error = self.doRubberbandProfile()
                if error:
                    pass
                    #ajh it would be good to restart the selection again after an error
                else:
                    self.doRubberbandSlopeEstimator(staElev)
                #ajh don't need this if we are doing hide and show 
                #self.btnSampleSlope.setEnabled(True) 
                self.deactivate()

            #Reset
            self.lastFreeHandPoints = self.pointstoDraw
            self.pointstoDraw = []
            #temp point to distinct leftclick and dbleclick
            self.dblclktemp = newPoints
            self.iface.mainWindow().statusBar().showMessage( "" )

            # ajh: trying to make something like this work:
            #self.iface.mainWindow.setWindowState(self.iface.mainWindow.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            #self.iface.mainWindow.raise_()
            #self.iface.mainWindow.show()
            # ajh: this is (really) it; needs a hide first... but we are moving it to the start as discussed there
            #self.show()
            
            # ajh: thought this just wasn't working on windows as per
            # https://stackoverflow.com/questions/22815608/how-to-find-the-active-pyqt-window-and-bring-it-to-the-front
            # see https://forum.qt.io/topic/1939/activatewindow-does-not-send-window-to-front/11
            #self.iface.mainWindow.activateWindow()
            
            # but actually, this is the solution:
            #self.activateWindow()
            return


###***********************************************
            
    def connectTool(self):
        # fix_print_with_import
        print('connecting')
        self.tool.moved.connect(self.moved)
        self.tool.rightClicked.connect(self.rightClicked)
        self.tool.leftClicked.connect(self.leftClicked)
        self.tool.doubleClicked.connect(self.doubleClicked)
        self.tool.deactivated.connect(self.tooldeactivated)

    def deactivate(self):        #enable clean exit of the plugin
        self.cleaning()
        try:
            self.tool.moved.disconnect(self.moved)
            self.tool.leftClicked.disconnect(self.leftClicked)
            self.tool.rightClicked.disconnect(self.rightClicked)
            self.tool.doubleClicked.disconnect(self.doubleClicked)
            self.tool.deactivated.disconnect(self.tooldeactivated)
        except:
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

    def cleaning(self):            #used on right click and deactivate
        self.canvas.unsetMapTool(self.tool)
        self.canvas.setMapTool(self.saveTool)
        self.rubberband.reset(self.polygon)
        self.iface.mainWindow().statusBar().showMessage( "" ) # ajh: I guess there might have been a statusBar message associated with the saveTool which we should restore
#==============================================================================
# END rubberband and related functions from
#       https://github.com/etiennesky/profiletool
#==============================================================================
    
    def doRubberbandProfile(self):
        layerString = self.cbDEM.currentText()
        layer = utils.getRasterLayerByName(' '.join(layerString.split(' ')[:-1]))
        try:
            if layer.isValid():
                self.xRes = layer.rasterUnitsPerPixelX()
        except:
            QMessageBox.warning(self,'Error',
                                'Selected DEM layer is missing')
            return [None, 'error']
        line = LineString(self.pointstoDraw[:-1]) 
        xyzdList = utils.elevationSampler(line,self.xRes, layer)
        sta = xyzdList[-1]
        elev = xyzdList[-2]
        staElev = np.array(list(zip(sta, elev)))
        try:
            np.isnan(np.sum(staElev[:,1]))
            return [staElev, None]
        except:
            QMessageBox.warning(self,'Error',
                                'Sampled line not within bounds of DEM')
            # ajh: don't think we need this
            #self.cleaning()
            
            return [staElev, 'error']
            
            
        
    def doIrregularProfileFlowEstimator(self):
        thalweig = self.staElev[np.where(self.staElev[:,1] == np.min(self.staElev[:,1]))] 
        thalweigX = thalweig[:,0][0]
        minElev = thalweig[:,1][0]+.01
        try:
            lbMaxEl = self.staElev[np.where(self.staElev[:,0]>thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            # ajh: don't think we need this
            #self.deactivate()
            return
        try:
            rbMaxEl = self.staElev[np.where(self.staElev[:,0]<thalweigX)][:,1].max()
        except:
            QMessageBox.warning(self,'Error', 'Channel not found')
            # ajh: don't think we need this
            #self.deactivate()
            return 
        maxElev = np.array([lbMaxEl,rbMaxEl]).min()-.001 # ajh: let the user set WSE up to 1mm (if units in m) below the crest
        WSE = maxElev
        WSE = (self.staElev[:,1].max() - self.staElev[:,1].min())/2. + self.staElev[:,1].min()
        self.cbWSE.setValue(WSE)
        self.cbWSE.setMinimum(minElev)
        self.cbWSE.setMaximum(maxElev)
        self.cbUDwse.setValue(WSE)
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
        # fix_print_with_import
        print(slope)

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
            # fix_print_with_import
            print('error: negative slope')
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
        # fix_print_with_import
        print(filePath)
        try:
            self.staElev = np.loadtxt(filePath)
            self.inputFile.setText(filePath)
            self.calcType = 'UD' 
            self.doIrregularProfileFlowEstimator()
        except:
            if (filePath == ('')): # null string for cancel
                return
            QMessageBox.warning(self,'Error',
                                'Please check that the text file is space or tab delimited and does not contain header information')
        
        
    def accept(self):
        # recalculate in case save has been hit twice (otherwise instead of saving the cross-section png it saves a second copy of the rating curve).
        self.run()
        # assign results to numpy array for quick csv dump
        outPath = self.outputDir.text()
        home = os.path.expanduser("~")
        if outPath == '':
            outPath = os.path.join(home,'Desktop','QGISFlowEstimatorFiles')
            self.outputDir.setText(outPath)
        # Note that in Python 3.2+ we will be able to just do: os.makedirs("path/to/directory", exist_ok=True)                    
        if not os.path.exists(outPath):
            os.makedirs(outPath)
        fileName = outPath + '/FlowEstimatorResults.txt'
        # ajh I think we've fixed the file/folder locking problem on windows by not doing chdir to outPath
		# keeping these old comments just in case:
        # one way to prevent it may be to open like this:
        # outFile = open(fileName, 'w', False)
        # another way may be to do outFile = None after closing
        outFile =  open(fileName,'w')
        outHeader = '*'*20 + '\nFlow Estimator - A QGIS plugin\nEstimates uniform, steady flow in a channel using Mannings equation\n' + '*'*20
        if self.calcType == 'DEM':
            try:
               proj4 = utils.getRasterLayerByName(self.cbDEM.currentText().split(' EPSG')[0]).crs().toProj4()
            except:
               proj4 = "Unknown"
            outHeader += '\n'*5 + 'Type:\tCross Section from DEM\nUnits:\t{0}\nDEM Layer:\t{1}\nProjection (Proj4 format):\t{2}\nChannel Slope:\t{3:.06f}\nMannings n:\t{4:.02f}\n\n\n\nstation\televation\n'.format(self.units,self.cbDEM.currentText(), proj4, self.slope.value(), self.n.value())
            outFile.write(outHeader)
            np.savetxt(outFile, self.staElev, fmt = '%.3f', delimiter = '\t')
            wseMax = self.cbWSE.value()
            wseMin = self.cbWSE.minimum()
        elif self.calcType =='UD':
            outHeader += '\n'*5 + 'Type:\tUser Defined Cross Section\nUnits:\t{0}\nChannel Slope:\t{1:.06f}\nMannings n:\t{2:.02f}\n\n\n\nstation\televation\n'.format(self.units, self.slope.value(), self.n.value())
            outFile.write(outHeader)
            np.savetxt(outFile, self.staElev, fmt = '%.3f', delimiter = '\t')
            wseMax = self.cbUDwse.value()
            wseMin = self.cbUDwse.minimum()            
        
        else:
            outHeader += '\n'*5 + 'Type:\tTrapezoidal Channel\nUnits:\t{0}\nChannel Slope:\t{1:.06f}\nMannings n:\t{2:.02f}\nBottom Width:\t{3:.02f}\nRight Side Slope:\t{4:.02f}\nLeft Side Slope:\t{5:.02f}\n'.format(self.units, self.slope.value(), self.n.value(), self.botWidth.value(), self.rightSS.value(), self.leftSS.value())
            outFile.write(outHeader)
            wseMax = self.depth.value()
            wseMin = 0.001
        self.mplCanvas.print_figure(outPath + '/FlowEstimatorResultsXSFigure')
        outHeader = '\n\n\n\n\n\n\nwater surface elevation\tflow\tvelocity\tR\tarea\ttop width\tdepth\n'
        outFile.write(outHeader)
        ###do loop here 
        step = 0.1
        wseList = []
        qList = []
        for wse in utils.frange(wseMin, wseMax, step):
            if self.calcType == 'DEM' or self.calcType == 'UD':
                args = flowEstimator(wse, self.n.value(), self.slope.value(), staElev = self.staElev, units = self.units)
            else:
                args = flowEstimator(wse, self.n.value(), self.slope.value(), widthBottom = self.botWidth.value(), rightSS = self.rightSS.value(), leftSS = self.leftSS.value(), units = self.units)
            R, area, topWidth, Q, v, depth, xGround, yGround, yGround0, xWater, yWater, yWater0 = args
            data = '{0}\t{1:.02f}\t{2:.02f}\t{3:.02f}\t{4:.02f}\t{5:.02f}\t{6:.02f}\n'.format(wse, Q, v, R, area, topWidth, depth)
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
    
    
        outFile.close()
        #ajh this may help force the file lock to be released
        outFile = None
        
        self.iface.messageBar().pushMessage("Flow Estimator", 'Output files saved to {}'.format(outPath),duration=30)

