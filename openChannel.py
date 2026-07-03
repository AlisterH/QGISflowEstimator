# -*- coding: utf-8 -*-
"""
Created on Tue May  5 16:26:25 2015

@author: mweier
"""
#note all those commented print lines need to be changed to use this
#from __future__ import print_function
#import matplotlib.pyplot as plt
from builtins import range
import numpy as np

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

def channelBuilder(wsDepth, rightSS, leftSS, widthBottom):
    """
    Builds trapezoidal channel station/elevation array given depth, 
    right side slope, left side slope, and bottom width
    """
    leftToe = wsDepth*1.25*leftSS
    rightToe = wsDepth*1.25*rightSS  
    staElev = np.array([(0.0, wsDepth*1.25), (leftToe, 0.0), (leftToe+widthBottom, 0.0), (leftToe+widthBottom+rightToe, wsDepth*1.25)])
    staElev = np.pad(staElev, ((0,0), (0,1)), mode='constant', constant_values=0)
    d = np.diff(staElev[:,:2], axis=0)
    staElev[1:,2] = np.cumsum(np.sqrt(np.sum(d*d, axis = 1)))
    return staElev


def lineIntersection(line1, line2): # ajh: do we need this or can we use a numpy intersect function?
    #log('line1' + str(line1), LEVEL_INFO)
    #log('line2' + str(line2), LEVEL_INFO)
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
    #log('xdiff' + str(xdiff), LEVEL_INFO)
    #log('ydiff' + str(ydiff), LEVEL_INFO)
    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    #log(str(div), LEVEL_INFO)
    if div == 0:
        x = y = np.nan
        #log('lines do not intersect', LEVEL_WARNING) # but also true for two horizontal lines at the same level!
        return x, y

    #log('det(*line1)' + str(det(*line1)), LEVEL_INFO)
    #log('det(*line2)' + str(det(*line2)), LEVEL_INFO)
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    #log('x' + str(x), LEVEL_INFO)
    #log('y' + str(y), LEVEL_INFO)
    #log('d' + str(d), LEVEL_INFO)
    return x, y

def polygonArea(corners):
    area = 0.0
    for i in range(len(corners)):
        j = (i + 1) % len(corners)
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return area  
    
def channelPerimeter(corners): # ajh should be faster to calculate this from the third column of self.staElev
                               # but I guess in calculating that I have effectively reimplemented this
                               # Would using this logic instead be faster or slower?
    P = 0.0
    for i in range(len(corners)-1):
        P += np.sqrt((np.power((corners[i+1][0]-corners[i][0]),2) + np.power((corners[i+1][1]-corners[i][1]),2)))
    return P
    

def flowEstimator(wsElev, n, channelSlope, **kwargs):
    """
    Estimates uniform flow using the Manning equation for
    a user defined trapezoidal channel or a manually defined channel using
    a station/elevation file 
    """
    # ajh: TODO: I think we could optimise this by assigning variables for things that we are currently looking up repeatedly in the array.  How to confirm if this will improve performance?
    # ajh: TODO: we locate the thalweg when we load the profile in doIrregularProfileFlowEstimator; if we did it properly there we could start with that here instead of recalculating every time we run flowEstimator.
    if kwargs.get("elevFile") is not None:	# ajh TODO: it seems like this isn't being used at the moment, the file is loaded in flow_estimator_dialog.py; cleanup?
        staElev = np.genfromtxt(kwargs.get("elevFile"), delimiter = '\t')
    elif kwargs.get("staElev") is not None:
        staElev = kwargs.get("staElev")
    elif kwargs.get("widthBottom") and kwargs.get("rightSS") and kwargs.get("leftSS") > 0:
        staElev = channelBuilder(wsElev, kwargs.get("rightSS"), kwargs.get("leftSS"), kwargs.get("widthBottom"))
    else:
        log('Whoops, wrong input', LEVEL_CRITICAL)
        return
    if kwargs.get("units") == "m":
        const = 1.0
    else:
        const = 1.4859
    
    minElev = np.min(staElev[:,1]) # could come from doIrregularProfileFlowEstimator, so we would only calculate it once
    
    intersectList = []
    for i in range(1, len(staElev)):
        #alister: used this for testing
        #log('i' + str(i), LEVEL_INFO)
        x, y = lineIntersection((staElev[i-1][:2], staElev[i][:2]), ([staElev[0][0],wsElev], [staElev[-1][0],wsElev]))
        d = staElev[i-1][2] + ( (y-staElev[i-1][1])**2 + (x-staElev[i-1][0])**2 )**0.5
        #log('x1' + str(x), LEVEL_INFO)
        #log('y1' + str(y), LEVEL_INFO)
        #log('d' + str(d), LEVEL_INFO)
        #log('staElev' + str(staElev[i-1][0]), LEVEL_INFO)
        #log('staElev' + str(staElev[i][0]), LEVEL_INFO)
        if staElev[i-1][0] <= x <= staElev[i][0] or staElev[i-1][0] >= x >= staElev[i][0] or abs(x - staElev[i][0]) < 0.001 or abs(x - staElev[i-1][0]) < 0.001: # or np.is_close(x, staElev[i-1][0]) or np.is_close(x, staElev[i][0]): # not sure why it didn't like this method to catch any float error
            #log('yes', LEVEL_INFO)
            if abs(y - wsElev)<0.001: # ajh: was 0.01, but not sure if we need this test; I think it may not have been doing what Mitch intended
                #log('yes', LEVEL_INFO)
                if staElev[i,0] == staElev[i-1,0]:
                    #log('yes', LEVEL_INFO)
                    if min(staElev[i,1], staElev[i-1,1]) <= y <= max(staElev[i,1], staElev[i-1,1]): # ajh: how to know if float error will cause a problem here?
                        intersectList.append((x,y,d))
                        #log('yes', LEVEL_INFO)
                    else:
                        log('line segments do not intersect', LEVEL_WARNING)
                else:
                    #log('no', LEVEL_INFO)
                    intersectList.append((x,y,d))
            log('x' + str(x), LEVEL_INFO)
            log('y' + str(y), LEVEL_INFO)
            log('d' + str(d), LEVEL_INFO)
        else:
            #alister: used this for testing
            #log('line segments do not intersect', LEVEL_WARNING)
            pass
    intersectArray = np.array(intersectList)
    if len(intersectArray) < 2:
        log('Programming Error: less than 2 points intersect; how did the WSE get too high?', LEVEL_CRITICAL)
        log('intersectArray\n ' + str(intersectArray), LEVEL_INFO)
        return
    #log("intersectArray\n" + str(intersectArray), LEVEL_INFO)
    # ajh: why is sorting necessary?
    #intersectArray = intersectArray[intersectArray[:,0].argsort()]
    if len(intersectArray) > 2:
        log('more than two points intersect', LEVEL_WARNING)
        log('intersectArray\n ' + str(intersectArray), LEVEL_INFO)
		# find the start point
        #log(str(staElev[np.where(staElev[:,1]==minElev)][0][2]), LEVEL_INFO)
        #log('staminElev ' + str(staMinElev), LEVEL_INFO)
        #log('intersectArray\n ' + str(intersectArray), LEVEL_INFO)
        #log("002 " + str(intersectArray[:,0]<=staMinElev), LEVEL_INFO)
        #log("002 " + str(np.where(intersectArray[:,0]<=staMinElev)), LEVEL_INFO)
        #log("003 " + str(intersectArray[:,0]>=staMinElev), LEVEL_INFO)
        #log("003 " + str(np.where(intersectArray[:,0]>=staMinElev)), LEVEL_INFO)
    # don't  put this in the if above; if something has gone wrong we could have two points at the same elevation on the same side of the thalweg, so we should still use this logic for only two points.
    staMinElev = np.median(staElev[np.where(staElev[:,1]==minElev)][0][2])
    #log('staminElev ' + str(staMinElev), LEVEL_INFO)
    try:
        startPoint = intersectArray[np.where(intersectArray[:,2]<staMinElev)][-1]
        #log('startPoint ' + str(startPoint), LEVEL_INFO)
		# find the end point
        #log('staminElev ' + str(staMinElev), LEVEL_INFO)
        #log("intersectArray\n" + str(intersectArray), LEVEL_INFO)
        #log("002 " + str(intersectArray[:,0]<=staMinElev), LEVEL_INFO)
        #log("002 " + str(intersectArray[np.where(intersectArray[:,2]<staMinElev)]), LEVEL_INFO)
        #log("003 " + str(intersectArray[:,0]>=staMinElev), LEVEL_INFO)
        #log("003 " + str(np.where(intersectArray[:,0]>=staMinElev)), LEVEL_INFO)
        endPoint = intersectArray[np.where(intersectArray[:,2]>staMinElev)][0]
        #log('endPoint ' + str(endPoint), LEVEL_INFO)
    except:
        log('Programming Error: no intersections on one side of the thalweg; how did the WSE get too high?', LEVEL_CRITICAL)
        log('intersectArray\n' + str(intersectArray), LEVEL_INFO)
        return
    intersectArray = np.vstack([startPoint, endPoint])
    # log('intersectArray\n ' + str(intersectArray), LEVEL_INFO)
    
    # don't really need variables for these, but it might make the code easier to understand
    staMin = intersectArray[0][0]
    #log('staMin' + str(staMin), LEVEL_INFO)
    staMax = intersectArray[1][0]
    #log('staMax' + str(staMax), LEVEL_INFO)
    dMin = intersectArray[0][2]
    dMax = intersectArray[1][2]
    
    # ajh: not actually used for anything; max thalweg also calculated in flow_estimator_dialog.py when the channel is loaded
    #thalweig = staElev[np.where(staElev[:,1] == np.min(staElev[:,1]))] 
    # ajh: already calculated above
    #minElev = thalweig[:,1][0]
    maxDepth = wsElev-minElev
    

    #log("intersectArray[0] " + str(intersectArray[0]), LEVEL_INFO)
    #log("staElev " + str(staElev), LEVEL_INFO)
    #log("intersectArray[1] " + str(intersectArray[1]), LEVEL_INFO)
    staElevTrim = np.vstack([intersectArray[0], staElev, intersectArray[1]])
    #log("staElevTrim " + str(staElevTrim), LEVEL_INFO)
    # ajh: why do we need to sort?
    #staElevTrim = staElevTrim[staElevTrim[:,0].argsort()]
    staElevTrim = staElevTrim[np.where((staElevTrim[:,2]>=dMin) & (staElevTrim[:,2]<=dMax))]
    #log("staElevTrim " + str(staElevTrim), LEVEL_INFO)
  
    area = polygonArea(staElevTrim)
    #log(str(area), LEVEL_INFO)
    # These two give the same answers, effectively validating both sets of code
    P = staElevTrim[-1,2] - staElevTrim[0,2]
    R = area/P
    #log('P ' + str(P), LEVEL_INFO)
    #log('P ' + str(channelPerimeter(staElevTrim)), LEVEL_INFO)
    #R = area/channelPerimeter(staElevTrim)
    # AJH: TODO I think it would be good to output channelPerimeter so that users can quickly confirm in their own minds that we are producing the right answers
    v = (const/n)*np.power(R,(2./3.0))*np.sqrt(channelSlope)
    #log(str(v), LEVEL_INFO)
    Q = v*area
    #log(str(Q), LEVEL_INFO)
    topWidth = staMax-staMin
    xGround = staElev[:,0]
    yGround = staElev[:,1]
    yGround0 = np.ones(len(xGround))*np.min(yGround)     
    xWater = staElevTrim[:,0]
    yWater = np.ones(len(xWater))*wsElev
    yWater0 = staElevTrim[:,1]  
    args = R, P, area, topWidth, Q, v, maxDepth, xGround, yGround, yGround0, xWater, yWater, yWater0
    return args


#def plotter(args):
#    R, area, topWidth, Q, v, xGround, yGround, yGround0, xWater, yWater, yWater0 = args
#    plt.plot(xGround, yGround, '0.9')
#    plt.fill_between(xGround, yGround, yGround0, where=yGround>yGround0, facecolor='0.9', interpolate=True)
#    plt.plot(xWater, yWater, 'blue')
#    plt.fill_between(xWater, yWater, yWater0, where=yWater>=yWater0, facecolor='blue', interpolate=True, alpha = 0.1)
#    plt.xlabel('Station')
#    plt.ylabel('Elevation')
#    plt.show() 
#    print 
#    print 'Hydraulic Radius = ',R
#    print 'Area = ',area, 'sq ft'
#    print 'Top Width = ',topWidth, 'ft'
#    print 'Flow = ',Q, 'cfs'
#    print 'Velocity = ',v, 'ft/s'      
 
#wsElev = 10.
#n = 0.040
#channelSlope = 0.0005
#
#elevFile = '/Users/mweier/Desktop/XScsv.txt'
#
#widthBottom = 40.
#rightSS = 5. #eg 2:1
#leftSS = 5. #eg 2:1
#
#R, area, topWidth, Q, v, xGround, yGround, yGround0, xWater, yWater, yWater0= flowEstimator(wsElev, n, channelSlope, widthBottom = 40., rightSS = 5., leftSS = 5.)
#plotter(R, area, topWidth, Q, v, xGround, yGround, yGround0, xWater, yWater, yWater0)
#    
#    
#R, area, topWidth, Q, v, xGround, yGround, yGround0, xWater, yWater, yWater0 = flowEstimator(1900.25, n, channelSlope, elevFile = elevFile)
#plotter(R, area, topWidth, Q, v, xGround, yGround, yGround0, xWater, yWater, yWater0)