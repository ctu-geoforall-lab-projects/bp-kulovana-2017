import os
import tempfile

from osgeo import ogr

from .exception import RadiationError

class RadiationPolygonizer:
    def __init__(self, lines, generalizer=None):
        self.input_lines = lines
        self.generalizer = generalizer

    def destination(self, dst_filename=None, overwrite=True):
        """Generate layer to save polygons in.

        If output file exists and overwrite argument is False than
        RadiationError is raised.

        :param dst_filename: name for output file
        :param overwrite: True for overwriting output files
        """
        # Get the spatial reference
        self.output_srs = self.input_lines.output_srs

        # Check if destination exists
        if dst_filename and os.path.exists(dst_filename) and not overwrite:
            raise RadiationError("File {} already exists".format(dst_filename))

        if not dst_filename:
            dst_filename = tempfile.NamedTemporaryFile().name

        # Generate layer
        self.output_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(dst_filename)
        layer_name = os.path.splitext(os.path.basename(dst_filename))[0]
        self.output_layer = self.output_ds.CreateLayer(layer_name, self.output_srs)

        self.output_layer.CreateField(ogr.FieldDefn("ID", ogr.OFTInteger))

    def _close_line(self, geom, box):
        """Close lines.

        If start point differs from end point than line is close by
        region box geometry. Intersection with region box is computed
        in 2D.

        :param lines: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)

        :return: closed geometry
        """
        print (geom.IsRing())

    def _create_polygon(self, geom):
        """Create polygon from closed linestring geometry.

        If input geometry is not closed linestring that PolygonError
        is raised.

        :param geom: input linestring geometry

        :return: polygon geometry
        """
        pass

    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 0. create region box geometry from input raster
        region_box = self.input_lines.box()
        print (region_box)

        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            # 1. close open isolines (based on bbox)
            # print warning if isolines cannot be closed
            geom_closed = self._close_line(geom, region_box)

            # 2. perform generalization if defined
            #
            # if generalizer:
            #     geom_simplified = generalizer.perform(geom_closed)
            # else:
            #     geom_simlified = geom_closed
            #
            # 3. create polygons from closed lines
            # polygon = self._create_polygon(geom_simplied)
            #
            # 4. write polygons to output
            # self._write_output(polygon, value)
            #
            # print (self.input_lines.layer().GetFeatureCount())
