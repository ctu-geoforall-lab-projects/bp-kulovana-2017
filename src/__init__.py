# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RadiationReconnaissanceResults
                                 A QGIS plugin
 This plugin generates polygons from grid.
                             -------------------
        begin                : 2017-02-15
        copyright            : (C) 2017 by Tereza Kulovana
        email                : teri.kulovana@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RadiationReconnaissanceResults class from file RadiationReconnaissanceResults.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .radiation_reconnaissance_results import RadiationReconnaissanceResults
    return RadiationReconnaissanceResults(iface)
