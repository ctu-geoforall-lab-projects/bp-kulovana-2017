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
        return []

    def _create_polygons(self, geoms):
        # [ (geom1, value1), (geom2, value2), ...]
        return []

    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 1. close open isolines (based on bbox)
        # print warning if isolines cannot be closed
        # lines = self._close_lines()

        # 2. perform generalization if defined
        if generalizer:
            lines = generalizer.perform(lines)

        # 3. create polygons from closed lines
        polygons = self._polygonize(lines)

        # 4. write polygons to output
        self._write_output()

        print (self.input_lines.layer().GetFeatureCount())
