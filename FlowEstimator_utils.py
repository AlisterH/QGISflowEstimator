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

from qgis.core import QgsRaster, QgsMapLayer

try:
    from qgis.core import QgsPointXY, QgsProject
except:
    from qgis.core import QgsPoint as QgsPointXY, QgsMapLayerRegistry as QgsProject

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

def valMesh(x, y, mLayer):
    """Sample elevation value from mesh layer at point (x, y) using barycentric interpolation"""
    try:
        mesh = mLayer.nativeMesh()
        if mesh is None:
            return None
        
        # Get vertices and faces
        vertices = mesh.vertices()
        faces = mesh.faces()
        
        if not vertices or not faces:
            return None
        
        # Try to get the elevation dataset (usually the first one)
        try:
            datasets = mLayer.dataProvider().datasets()
            if not datasets:
                # If no datasets, try to use vertex z-coordinates
                return _interpolateFromVertices(x, y, vertices, faces, use_z_coords=True)
            
            # Get the first dataset group
            dataset_group = datasets[0]
            
            # Find the best face containing or closest to the point
            best_face_idx = -1
            best_distance = float('inf')
            
            for face_idx, face in enumerate(faces):
                # Get vertices of this face
                face_vertices = [vertices[v_idx] for v_idx in face if v_idx >= 0]
                
                if len(face_vertices) < 3:
                    continue
                
                # Check if point is inside face using barycentric coordinates
                inside, bary_coords = _pointInTriangle(x, y, face_vertices)
                
                if inside:
                    best_face_idx = face_idx
                    break
                else:
                    # Find closest point on face
                    dist = _pointToFaceDistance(x, y, face_vertices)
                    if dist < best_distance:
                        best_distance = dist
                        best_face_idx = face_idx
            
            if best_face_idx < 0:
                return None
            
            # Get face vertices
            face = faces[best_face_idx]
            face_vertices = [vertices[v_idx] for v_idx in face if v_idx >= 0]
            
            if len(face_vertices) < 3:
                return None
            
            # Interpolate elevation value using barycentric coordinates
            inside, bary_coords = _pointInTriangle(x, y, face_vertices)
            
            # Get elevation values from dataset at face vertices
            try:
                # Try to get values from the first dataset (vertex-based)
                face_indices = [v_idx for v_idx in face if v_idx >= 0]
                if len(face_indices) >= 3:
                    # Use first three vertices for interpolation
                    z_vals = []
                    for v_idx in face_indices[:3]:
                        # Try to get value from dataset
                        try:
                            # Access the dataset values
                            val = dataset_group[0][v_idx] if isinstance(dataset_group[0], (list, tuple)) else face_vertices[face_indices.index(v_idx)].z()
                            z_vals.append(float(val) if val is not None else face_vertices[face_indices.index(v_idx)].z())
                        except:
                            z_vals.append(face_vertices[face_indices.index(v_idx)].z())
                    
                    if len(z_vals) >= 3 and all(z is not None for z in z_vals):
                        # Interpolate using barycentric coordinates
                        z_interp = bary_coords[0] * z_vals[0] + bary_coords[1] * z_vals[1] + bary_coords[2] * z_vals[2]
                        return z_interp
            except:
                pass
            
            # Fallback: interpolate from vertex z-coordinates
            return _interpolateFromVertices(x, y, face_vertices, use_z_coords=True, bary_coords=bary_coords)
                
        except Exception as e:
            # Fallback to simple z-coordinate interpolation
            vertices_list = list(vertices)
            return _interpolateFromVertices(x, y, vertices_list, faces, use_z_coords=True)
            
    except Exception as e:
        return None

def _pointInTriangle(px, py, vertices):
    """Check if point is in triangle and return barycentric coordinates"""
    if len(vertices) < 3:
        return False, [0, 0, 0]
    
    # Use first three vertices
    v0 = vertices[0]
    v1 = vertices[1]
    v2 = vertices[2]
    
    # Calculate barycentric coordinates
    denom = ((v1.y() - v2.y()) * (v0.x() - v2.x()) + (v2.x() - v1.x()) * (v0.y() - v2.y()))
    
    if abs(denom) < 1e-10:
        return False, [0, 0, 0]
    
    a = ((v1.y() - v2.y()) * (px - v2.x()) + (v2.x() - v1.x()) * (py - v2.y())) / denom
    b = ((v2.y() - v0.y()) * (px - v2.x()) + (v0.x() - v2.x()) * (py - v2.y())) / denom
    c = 1 - a - b
    
    inside = (a >= -1e-10 and b >= -1e-10 and c >= -1e-10)
    return inside, [a, b, c]

def _pointToFaceDistance(px, py, vertices):
    """Calculate minimum distance from point to face"""
    if len(vertices) < 3:
        return float('inf')
    
    min_dist = float('inf')
    
    # Check distance to each edge
    for i in range(len(vertices)):
        v1 = vertices[i]
        v2 = vertices[(i + 1) % len(vertices)]
        
        dist = _pointToLineSegmentDistance(px, py, v1.x(), v1.y(), v2.x(), v2.y())
        min_dist = min(min_dist, dist)
    
    return min_dist

def _pointToLineSegmentDistance(px, py, x1, y1, x2, y2):
    """Calculate distance from point to line segment"""
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)))
    
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    return math.sqrt((px - closest_x)**2 + (py - closest_y)**2)

def _interpolateFromVertices(px, py, vertices, faces=None, use_z_coords=False, bary_coords=None):
    """Interpolate value from nearest vertex"""
    if not vertices:
        return None
    
    min_dist = float('inf')
    closest_z = None
    
    for vertex in vertices:
        dx = vertex.x() - px
        dy = vertex.y() - py
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < min_dist:
            min_dist = dist
            closest_z = vertex.z() if use_z_coords else None
    
    return closest_z

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
    is_mesh = layer.type() == QgsMapLayer.MeshLayer
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
            z.append(None)
        dist.append(currentDist)
    
    xyzdList = [x, y, z, dist]
    return xyzdList
