# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
import os

from .carbon_estimator_dialog import CarbonEstimatorDialog
from .process_logic import run_carbon_estimation

class CarbonEstimatorPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'Estimasi Karbon'
        self.first_start = None

    def add_action(self, text, callback, parent=None):
        action = QAction(text, parent)
        action.triggered.connect(callback)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        self.add_action(
            text='Estimasi Karbon & IDW',
            callback=self.run,
            parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg = CarbonEstimatorDialog()

        self.dlg.show()
        result = self.dlg.exec_()
        
        if result:
            self.process()
            
    def process(self):
        layer = self.dlg.cmbLayerPoin.currentLayer()
        aoi = self.dlg.cmbLayerAOI.currentLayer()
        
        if not layer or not aoi:
            QMessageBox.warning(self.iface.mainWindow(), "Error", "Layer Poin dan AOI harus dipilih!")
            return
            
        plot_fld = self.dlg.cmbFieldPlot.currentField()
        sp_fld = self.dlg.cmbFieldSpesies.currentField()
        gen_fld = self.dlg.cmbFieldGenus.currentField()
        dbh_fld = self.dlg.cmbFieldDBH.currentField()
        out_dir = self.dlg.fileWidgetOutput.filePath()
        
        is_mangrove = self.dlg.cmbTipeHutan.currentIndex() == 1
        pixel_size = self.dlg.spinPixelSize.value()
        
        if not out_dir or not os.path.isdir(out_dir):
            QMessageBox.warning(self.iface.mainWindow(), "Error", "Pilih folder output yang valid!")
            return
            
        try:
            run_carbon_estimation(layer, plot_fld, sp_fld, gen_fld, dbh_fld, is_mangrove, aoi, pixel_size, out_dir)
            QMessageBox.information(self.iface.mainWindow(), "Sukses", "Proses selesai! Shapefile, Raster IDW, dan CSV berhasil disimpan di folder output.")
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Error", f"Terjadi kesalahan:\n{str(e)}")
