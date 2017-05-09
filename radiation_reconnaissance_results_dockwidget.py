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

        self.doserate_label.setText("Activity [MBq/m^2]")

        self.load_raster.clicked.connect(self.onLoadRaster)
        self.solve_button.setEnabled(True)
        self.solve_button.clicked.connect(self.onSaveButton)
        self.report_button.clicked.connect(self.onReportButton)
        self.type_box.currentIndexChanged.connect(self.onTypeBox)

        # Level checkboxes (Activity checkboxes checked, others disabled)
        self.onTypeBox()
        self.check_001.stateChanged.connect(self.levelsUpdate)
        self.check_01.stateChanged.connect(self.levelsUpdate)
        self.check_1.stateChanged.connect(self.levelsUpdate)
        self.check_5.stateChanged.connect(self.levelsUpdate)
        self.check_10.stateChanged.connect(self.levelsUpdate)
        self.check_50.stateChanged.connect(self.levelsUpdate)
        self.check_100.stateChanged.connect(self.levelsUpdate)
        self.check_1000.stateChanged.connect(self.levelsUpdate)

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

    def onTypeBox(self):
        # Activity = 0, Doserate = 1
        print "zmena indexu"
        index = self.type_box.currentIndex()
        print index
        if index == 0:
            print "Activity chosen"
            self.doserate_label.setText("Activity [MBq/m^2]")
            # Preset levels (rest disabled)
            self.check_001.setEnabled(True)
            self.check_001.setChecked(True)
            self.check_01.setEnabled(False)
            self.check_01.setChecked(False)
            self.check_1.setEnabled(True)
            self.check_1.setChecked(True)
            self.check_5.setEnabled(False)
            self.check_5.setChecked(False)
            self.check_10.setEnabled(True)
            self.check_10.setChecked(True)
            self.check_50.setEnabled(False)
            self.check_50.setChecked(False)
            self.check_100.setEnabled(True)
            self.check_100.setChecked(True)
            self.check_1000.setEnabled(False)
            self.check_1000.setChecked(False)

        elif index == 1:
            print "Doserate chosen"
            self.doserate_label.setText("Doserate [cGy/h]")
            # Preset levels (rest disabled)
            self.check_001.setEnabled(False)
            self.check_001.setChecked(False)
            self.check_01.setEnabled(True)
            self.check_01.setChecked(True)
            self.check_1.setEnabled(True)
            self.check_1.setChecked(True)
            self.check_5.setEnabled(True)
            self.check_5.setChecked(True)
            self.check_10.setEnabled(True)
            self.check_10.setChecked(True)
            self.check_50.setEnabled(True)
            self.check_50.setChecked(True)
            self.check_100.setEnabled(True)
            self.check_100.setChecked(True)
            self.check_1000.setEnabled(True)
            self.check_1000.setChecked(True)

        else:
            print "Problem with choosing type of data"

    def levelsUpdate(self):
        print "Checkbox clicked"
        self.levels = []
        if self.check_001.isChecked():
            self.levels.append(0.01)
        if self.check_01.isChecked():
            self.levels.append(0.1)
        if self.check_1.isChecked():
            self.levels.append(1)
        if self.check_5.isChecked():
            self.levels.append(5)
        if self.check_10.isChecked():
            self.levels.append(10)
        if self.check_50.isChecked():
            self.levels.append(50)
        if self.check_100.isChecked():
            self.levels.append(100)
        if self.check_1000.isChecked():
            self.levels.append(1000)

    def onSaveButton(self):
        print "Save button clicked"
        print "levely"
        self.levelsUpdate()
        print self.levels

        raster = self.raster_box.currentLayer().dataProvider().dataSourceUri()

        rc = isolines.RadiationIsolines(raster)
        output_dir = os.path.dirname(raster)
        output_filename = '{}_isolines.shp'.format(
            os.path.splitext(os.path.basename(raster))[0]
            )
        output = os.path.join(output_dir, output_filename)
        rc.destination(output)
        rc.generate(self.levels)
        print('{} generated'.format(output))

        rp = polygonizer.RadiationPolygonizer(rc)
        output_filename = '{}_polygons.shp'.format(
            os.path.splitext(os.path.basename(raster))[0]
        )
        output = os.path.join(output_dir, output_filename)
        print output
        rp.destination(str(output))
        rp.polygonize()
        print('{} generated'.format(output))
