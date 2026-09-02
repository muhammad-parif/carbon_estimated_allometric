# -*- coding: utf-8 -*-
import os
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsMapLayerProxyModel

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'carbon_estimator_dialog_base.ui'))

class CarbonEstimatorDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(CarbonEstimatorDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.cmbLayerPoin.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.cmbLayerAOI.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        
        self.cmbLayerPoin.layerChanged.connect(self.update_fields)
        self.update_fields(self.cmbLayerPoin.currentLayer())
        
    def update_fields(self, layer):
        if layer:
            self.cmbFieldPlot.setLayer(layer)
            self.cmbFieldSpesies.setLayer(layer)
            self.cmbFieldGenus.setLayer(layer)
            self.cmbFieldDBH.setLayer(layer)
