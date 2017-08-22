#!/usr/bin/env python
import sys
import os

# TODO: to be solved
#sys.path.insert(0, os.path.dirname(os.path.realpath('__file__')))
home = os.path.expanduser("~")
sys.path.insert(0, os.path.join(home, '.qgis2', 'python', 'plugins', 'bp-kulovana-2017'))

from pyradiation import isolines
reload(isolines)
from pyradiation import polygonizer
reload(polygonizer)

def main(raster):
    rc = isolines.RadiationIsolines(raster)
    output_dir = os.path.dirname(raster)
    # output_filename = '{}_isolines.shp'.format(
    #     os.path.splitext(os.path.basename(raster))[0]
    #     )
    # output = os.path.join(output_dir, output_filename)
    rc.destination()
    rc.generate([0.1, 1, 5, 10, 100, 1000])
    #print('{} generated'.format(output))

    rp = polygonizer.RadiationPolygonizer(rc)
    output_filename = '{}_polygons.shp'.format(
        os.path.splitext(os.path.basename(raster))[0]
        )
    output = os.path.join(output_dir, output_filename)
    rp.destination(output)
    rp.polygonize()
    print('{} generated'.format(output))
    
if __name__ in ("__main__", "__console__"):
    if len(sys.argv) < 2:
        data_dir = os.path.join(home, 'Documents', 'BAKALARKA', 'ACR',
                                'podklady_ACR_terenni_pruzkum')
        input_raster = os.path.join(data_dir,
                                    'CBRN_fictional_points_locality2_spline_doserate_cGyh_reclass.sdat')
    else:
        input_raster = sys.argv[1]

    main(input_raster)
