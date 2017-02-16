from osgeo import gdal

from .exception import RadiationError

class RadiationContour:
    def __init__(self, raster):
        self.ds = gdal.Open(raster)
        if self.ds is None:
            raise RadiationError("Unable to open '{}'".format(raster))

        print("Number of bands: {}".format(self.ds.RasterCount))
        
    def __del__(self):
        self.ds = None

    def generate(self, levels):
        print("Level count: {}".format(levels))
    
