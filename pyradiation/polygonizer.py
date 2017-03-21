import os
import tempfile

from osgeo import ogr

from .exception import RadiationError

class RadiationPolygonizer:
    def __init__(self, lines, generalizer=None):
        self.input_lines = lines
        self.generalizer = generalizer

    def destination(self, dst_filename=None, overwrite=True):
        # Generate layer to save polygons in

        # Get the spatial reference
        self.output_srs = self.input_lines.output_srs

        # Check if destination exists
        if dst_filename and os.path.exists(dst_filename) and not overwrite:
            raise RadiationError("File {} already exists".format(dst_filename))

        if not dst_filename:
            dst_filename = tempfile.NamedTemporaryFile().name

        # Generate layer
        self.output_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
        self.output_layer = self.output_ds.CreateLayer('polygons', self.output_srs)

        self.output_layer.CreateField(ogr.FieldDefn("ID", ogr.OFTInteger))

    def _close_lines(self):
        # self.input_lines.layer()
        # [ (geom1, value1), (geom2, value2), ...]

        # Get raster
        raster = self.input_lines.input_ds
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
        #print region_box.ExportToWkt()

        # Put geometry inside a feature
        layerDefinition = self.output_layer.GetLayerDefn()
        featureIndex = 0
        feature = ogr.Feature(layerDefinition)
        feature.SetGeometry(region_box)
        feature.SetFID(featureIndex)

        # Create the feature in the layer (shapefile)
        self.output_layer.CreateFeature(feature)

    def _create_polygons(self, geoms):
        # [ (geom1, value1), (geom2, value2), ...]
        return []

    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 1. close open isolines (based on bbox)
        # print warning if isolines cannot be closed
        lines = self._close_lines()

        # 2. perform generalization if defined
        # if generalizer:
        #     lines = generalizer.perform(lines)
        #
        # # 3. create polygons from closed lines
        # polygons = self._polygonize(lines)
        #
        # # 4. write polygons to output
        # self._write_output()
        #
        # print (self.input_lines.layer().GetFeatureCount())