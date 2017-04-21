# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RadiationReconnaissanceResultsDockWidget
                                 A QGIS plugin
 This plugin generates polygons from grid.
                             -------------------
        begin                : 2017-02-15
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Tereza Kulovana
        email                : teri.kulovana@gmail.com
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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, QSettings, QFileInfo
from PyQt4.QtGui import QFileDialog
from qgis.core import QgsProviderRegistry
from qgis.gui import QgsMapLayerComboBox, QgsMapLayerProxyModel
from qgis.utils import QgsMessageBar, iface
from osgeo import gdal, ogr

from pyradiation import isolines
from pyradiation import polygonizer

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'radiation_reconnaissance_results_dockwidget_base.ui'))


class RadiationReconnaissanceResultsDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(RadiationReconnaissanceResultsDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.settings = QSettings("CTU", "GRMplugin")

        # Save reference to the QGIS interface
        self.iface = iface

        # Set filter for QgsMapLayerComboBox
        self.raster_box.setFilters(QgsMapLayerProxyModel.RasterLayer)

        self.load_raster.clicked.connect(self.onLoadRaster)
        self.solve_button.setEnabled(False)
        self.report_button.clicked.connect(self.onReportButton)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def onLoadRaster(self):
        """Open 'Add raster layer dialog'."""
        sender = u'{}-lastUserFilePath'.format(self.sender().objectName())
        lastUsedFilePath = self.settings.value(sender, '')

        fileName = QFileDialog.getOpenFileName(self,self.tr(u'Open raster'),
                                               self.tr(u'{}').format(lastUsedFilePath),
                                               QgsProviderRegistry.instance().fileRasterFilters())
        if fileName:
            self.iface.addRasterLayer(fileName, QFileInfo(fileName).baseName())
            self.settings.setValue(sender, os.path.dirname(fileName))

    def onReportButton(self):
        pass