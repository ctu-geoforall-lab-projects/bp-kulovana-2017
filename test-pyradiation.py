#!/usr/bin/env python
import sys
#import os
#sys.path.insert(0, os.path.dirname(os.path.realpath('__file__')))
#print(os.path.dirname(os.path.realpath('__file__')))
sys.path.insert(0, 'c:\\Users\\Terka\\.qgis2\\python\\plugins\\bp-kulovana-2017\\')
#print(sys.path)

from pyradiation.contour import RadiationIsolines

def main(raster):
    rc = RadiationIsolines(raster)
    rc.destination('c:\\Users\\Terka\\Documents\\BAKALARKA\\ACR\\podklady_ACR_terenni_pruzkum\\contour_pokus.shp')
    rc.generate([0.1, 1, 5, 10, 100, 1000])

print(__name__)
if __name__ == "__main__":
    print(len(sys.argv))
    if len(sys.argv) < 2:
        sys.exit("Input raster must be given")

    main(sys.argv[1])
elif __name__ == "__console__":
    main('c:\\Users\\Terka\\Documents\\BAKALARKA\\ACR\\podklady_ACR_terenni_pruzkum\\CBRN_fictional_points_locality2_spline_doserate_cGyh_reclass.sdat')