import os
import tempfile

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

    def destination(self, dst_filename=None, overwrite=True):
        # Generate layer to save isolines in

        # Create the spatial reference
        input_srs = self.input_ds.GetProjection()
        self.output_srs = osr.SpatialReference()
        self.output_srs.ImportFromWkt(input_srs)

        # Check if destination exists
        if dst_filename and os.path.exists(dst_filename) and not overwrite:
            raise RadiationError("File {} already exists".format(dst_filename))

        if not dst_filename:
            dst_filename = tempfile.NamedTemporaryFile().name
            
        # Generate layer
        self.output_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
        self.output_layer = self.output_ds.CreateLayer('isolines', self.output_srs)

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

    def layer(self):
        return self.output_layer

    def box(self):
        """Create geometry of region box defined by input raster layer.
        """
        raster = self.input_ds
        # Get size of raster
        cols = raster.RasterXSize
        rows = raster.RasterYSize
        # Get coordinates of top left corner
        geoinformation = raster.GetGeoTransform()
        topLeftX = geoinformation[0]
        topLeftY = geoinformation[3]
        # Count bottom right corner
        x_size = geoinformation[1]*cols
        y_size = geoinformation[5]*rows
        bottomRightX = topLeftX + x_size
        bottomRightY = topLeftY + y_size

        # Create region box geometry
        region_box = ogr.Geometry(ogr.wkbLineString)
        region_box.AddPoint(topLeftX, topLeftY)
        region_box.AddPoint(bottomRightX, topLeftY)
        region_box.AddPoint(bottomRightX, bottomRightY)
        region_box.AddPoint(topLeftX, bottomRightY)
        region_box.AddPoint(topLeftX, topLeftY)

        # region_point = ogr.Geometry(ogr.wkbMultiPoint)
        region_point = (topLeftX, bottomRightX, topLeftY, bottomRightY)

        point1 = ogr.Geometry(ogr.wkbPoint)
        left_box = ogr.Geometry(ogr.wkbMultiPoint)
        point1.AddPoint(topLeftX, topLeftY)
        left_box.AddGeometry(point1)
        point1.AddPoint(topLeftX, bottomRightY)
        left_box.AddGeometry(point1)

        bottom_box = ogr.Geometry(ogr.wkbMultiPoint)
        point1.AddPoint(topLeftX, bottomRightY)
        bottom_box.AddGeometry(point1)
        point1.AddPoint(bottomRightX, bottomRightY)
        bottom_box.AddGeometry(point1)

        right_box = ogr.Geometry(ogr.wkbMultiPoint)
        point1.AddPoint(bottomRightX, bottomRightY)
        right_box.AddGeometry(point1)
        point1.AddPoint(bottomRightX, topLeftY)
        right_box.AddGeometry(point1)

        top_box = ogr.Geometry(ogr.wkbMultiPoint)
        point1.AddPoint(bottomRightX, bottomRightY)
        top_box.AddGeometry(point1)
        point1.AddPoint(bottomRightX, topLeftY)
        top_box.AddGeometry(point1)

        # Put geometry inside a feature
        # layerDefinition = self.output_layer.GetLayerDefn()
        # featureIndex = 0
        # feature = ogr.Feature(layerDefinition)
        # feature.SetGeometry(region_box)
        # feature.SetFID(featureIndex)

        # # Create the feature in the layer (shapefile)
        # self.output_layer.CreateFeature(feature)

        return region_box, region_point, left_box, bottom_box, right_box, top_box
