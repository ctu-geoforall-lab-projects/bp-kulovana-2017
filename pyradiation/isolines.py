import os

from osgeo import gdal, ogr, osr

from .exception import RadiationError

class RadiationIsolines:
    def __init__(self, raster):
        self.input_ds = gdal.Open(raster)
        if self.input_ds is None:
            raise RadiationError("Unable to open '{}'".format(raster))

        self.output_ds = None
        # TODO: logging
        # print("Number of bands: {}".format(self.input_ds.RasterCount))

    def __del__(self):
        self.input_ds = None
        if self.output_ds is not None:
            self.output_ds.Destroy()

    def destination(self, dst_filename, overwrite=True):
        # Generate layer to save isolines in

        # Create the spatial reference
        input_srs = self.input_ds.GetProjection()
        output_srs = osr.SpatialReference()
        output_srs.ImportFromWkt(input_srs)

        # Check if destination exists
        if os.path.exists(dst_filename) and not overwrite:
            raise RadiationError("File {} already exists".format(dst_filename))

        # Generate layer to save isolines in
        self.output_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
        self.output_layer = self.output_ds.CreateLayer('isolines', output_srs)

        field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
        self.output_layer.CreateField(field_defn)
        field_defn = ogr.FieldDefn("elev", ogr.OFTReal)
        self.output_layer.CreateField(field_defn)

    def generate(self, levels):
        # Generate isolines with fixed levels
        print("Level count: {}".format(levels))
        if self.output_ds is None:
            raise RadiationError("Output datasource not defined, destination() method must be called.")
        band = self.input_ds.GetRasterBand(1)
        ret = gdal.ContourGenerate(band, 0, 0, levels, 0, 0, self.output_layer, 0, 1)
        if ret != gdal.CE_None:
            raise RadiationError("Isolines generation failed")
