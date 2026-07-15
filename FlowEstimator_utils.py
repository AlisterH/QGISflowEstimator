# -*- coding: utf-8 -*-
"""
/***************************************************************************
 FlowEstimator
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
from builtins import str
from functools import cmp_to_key
import locale
import math

from qgis.core import QgsRaster, QgsMapLayer, QgsMeshDatasetIndex

try:
    from qgis.core import QgsPointXY, QgsProject
except:
    from qgis.core import QgsPoint as QgsPointXY, QgsMapLayerRegistry as QgsProject

_HAS_MESH_SUPPORT = hasattr(QgsMapLayer, 'MeshLayer')

def frange(start, end, step):
  while start < end:
    yield start
    start += step
  yield end

# let's only list single band rasters
def getRasterLayerNames(single_band_only=True):
    layerMap = QgsProject.instance().mapLayers()
    layerNames = []
    for name, layer in list(layerMap.items()):
        if layer.type() == QgsMapLayer.RasterLayer and layer.providerType() != 'wms':
            # determine band count without broad try/except
            band_count = None
            band_count_method = getattr(layer, 'bandCount', None) # newer QGIS
            if callable(band_count_method):
                band_count = band_count_method()
            else:
                provider = layer.dataProvider()
                provider_band_count = getattr(provider, 'bandCount', None) # older QGIS
                if callable(provider_band_count):
                    band_count = provider_band_count()
            if single_band_only and band_count != 1:
                continue
            srs = layer.crs().authid()
            layerNames.append(str(layer.name()+' '+srs))
    return sorted(layerNames, key=cmp_to_key(locale.strcoll))

# Get mesh layer names
def getMeshLayerNames():
    if not _HAS_MESH_SUPPORT:
        return []
    """Returns list of mesh layer names with their CRS"""
    layerMap = QgsProject.instance().mapLayers()
    layerNames = []
    for name, layer in list(layerMap.items()):
        if layer.type() == QgsMapLayer.MeshLayer:
            srs = layer.crs().authid()
            layerNames.append(str(layer.name()+' '+srs))
    return sorted(layerNames, key=cmp_to_key(locale.strcoll))

# Get all available data source layer names (raster + mesh)
def getDataSourceLayerNames(single_band_only=True):
    """Returns combined list of raster and mesh layer names"""
    raster_names = getRasterLayerNames(single_band_only)
    mesh_names = []
    if _HAS_MESH_SUPPORT:
        mesh_names = getMeshLayerNames()
    return sorted(raster_names + mesh_names, key=cmp_to_key(locale.strcoll))

def getRasterLayerByName(layerName):
    layerMap = QgsProject.instance().mapLayers()
    for name, layer in list(layerMap.items()):
        if layer.type() == QgsMapLayer.RasterLayer and layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None
    return None

def getMeshLayerByName(layerName):
    """Get a mesh layer by name"""
    layerMap = QgsProject.instance().mapLayers()
    for name, layer in list(layerMap.items()):
        if layer.type() == QgsMapLayer.MeshLayer and layer.name() == layerName:
            if layer.isValid():
                return layer
            else:
                return None
    return None

def getLayerByName(layerName):
    """Get a layer (raster or mesh) by name. First tries raster, then mesh."""
    layer = getRasterLayerByName(layerName)
    if layer is not None:
        return layer
    return getMeshLayerByName(layerName)

def valRaster(x, y, rLayer):
    z = rLayer.dataProvider().identify(QgsPointXY(x, y), QgsRaster.IdentifyFormatValue).results()[1]
    return z

import math
from qgis.core import QgsMeshDatasetIndex

def valMesh(x, y, mLayer):
    rs = mLayer.rendererSettings()
    group_index = rs.activeScalarDatasetGroup()
    if group_index < 0:
        return None

    idx = QgsMeshDatasetIndex(group_index, 0)
    value = mLayer.datasetValue(idx, QgsPointXY(x, y))
    scalar = value.scalar()

    if scalar is None or math.isnan(scalar):
        return None
    return scalar

# ajh: note this function is currently unused
def calcElev(self):
  
    features = self.vLayer.getFeatures()
    for f in features:
        geom = f.geometry()
    startPoint = geom.asPolyline()[0]
    endPoint = geom.asPolyline()[-1]
    try:
        startPointZdem = valRaster(startPoint[0],startPoint[1],self.rLayer)
    except:
        startPointZdem =None
        self.labelStartDepth.setText('Start point outside of raster')
        self.btnOk.setEnabled(False)
    try:        
        endPointZdem = valRaster(endPoint[0],endPoint[1],self.rLayer)
    except:
        endPointZdem =None
        self.labelStartDepth.setText('End point outside of raster')
        self.btnOk.setEnabled(False)
    return [startPointZdem, endPointZdem]

def elevationSampler(vectSHP, res, layer):
    """Returns xyz and station distance list from 2d vector and DEM/Mesh at specified resolution"""
    x = []
    y = []
    z = []
    dist = []
    vectLength = vectSHP.length
    
    # Determine if layer is raster or mesh
    is_mesh = _HAS_MESH_SUPPORT and layer.type() == QgsMapLayer.MeshLayer
    val_func = valMesh if is_mesh else valRaster
    
    for currentDist in frange(0, vectLength, res):  
        # creation of the point on the line
        point = vectSHP.interpolate(currentDist)
        xp, yp = point.x, point.y
        x.append(xp)
        y.append(yp)
        # extraction of the elevation value from the point
        try:
            zp = val_func(xp, yp, layer)
            z.append(zp)
        except Exception as e:
            # from qgis.core import QgsMessageLog, Qgis
            # QgsMessageLog.logMessage(
                # 'valMesh/valRaster exception at ({:.2f},{:.2f}): {}: {}'.format(xp, yp, type(e).__name__, e),
                # 'Flow Estimator', Qgis.Warning)
            z.append(None)
        dist.append(currentDist)
    
    # ajh: we actually only need z, dist
    xyzdList = [x, y, z, dist]
    return xyzdList
