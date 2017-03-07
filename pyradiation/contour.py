from osgeo import gdal, ogr

from .exception import RadiationError

class RadiationIsolines:
    def __init__(self, raster):
        self.ds = gdal.Open(raster)
        if self.ds is None:
            raise RadiationError("Unable to open '{}'".format(raster))

        print("Number of bands: {}".format(self.ds.RasterCount))

    def __del__(self):
        self.ds = None

    def destination(self, dst_filename):
        # Generate layer to save isolines in
        self.ogr_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
        self.contour_shp = self.ogr_ds.CreateLayer('contour')

        self.field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
        self.contour_shp.CreateField(self.field_defn)
        self.field_defn = ogr.FieldDefn("elev", ogr.OFTReal)
        self.contour_shp.CreateField(self.field_defn)

    def generate(self, levels):
        # Generate isolines with fixed levels
        print("Level count: {}".format(levels))
        self.band = self.ds.GetRasterBand(1)
        gdal.ContourGenerate(self.band, 0, 0, levels, 0, 0, self.contour_shp, 0, 1)