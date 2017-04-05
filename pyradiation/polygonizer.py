import os
import tempfile
import inspect

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

        if not geom.IsRing():
            print("neuzavrena")
            return []
        else:
            return geom

    def _count_intersection(self, geom, box_point, box, left_box, bottom_box, right_box, top_box):
        """
        Count intersection of  input geometry and region_box. Add intersection point to side_box and sort points.

        :param geom: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)

        :return: region box with new points at intersection of unclosed lines
        """

        leftX = box_point[0]
        rightX = box_point[1]
        topY = box_point[2]
        bottomY = box_point[3]

        if not geom.IsRing():
            intersection = geom.Intersection(box)
            print intersection.ExportToWkt()

            for point in intersection:
                if point.GetX() == leftX:
                    left_box = self._add_point(point, left_box, 1)
                if point.GetX() == rightX:
                    right_box = self._add_point(point, right_box, 1)
                if point.GetY() == topY:
                    top_box = self._add_point(point, top_box, 2)
                if point.GetY() == bottomY:
                    bottom_box = self._add_point(point, bottom_box, 2)
                else:
                    print("Non-ring feature.")

        # for i in range(intersection.GetGeometryCount()):

        return left_box, bottom_box, right_box, top_box

    def _add_point(self, point, side_box, C):
        """
        Add intersection point to side_box and sort points.

        :param point: input point
        :param side_box: input points of one side of region_box (defined as MultiPoint)
        :param C: sorting rule (1 -> Y, 2 -> X)
        :return: sorted side_box with new point
        """

        point_to_multi = ogr.Geometry(ogr.wkbPoint)
        point_to_multi.AddPoint(point.GetX(), point.GetY())
        side_box.AddGeometry(point_to_multi)
        if C == 2:
            # for point in side_box:
            sorted(side_box, key=lambda p: p.GetX)
        else:
            # for point in side_box:
            sorted(side_box, key=lambda p: p.GetY)
        # print ('srovnano {}'.format(side_box))
        print ("C: ", C)
        # print side_box.GetGeometryCount()

        return side_box


    def _create_polygon(self, geom):
        """Create polygon from closed linestring geometry.

        If input geometry is not closed linestring that PolygonError
        is raised.

        :param geom: input linestring geometry

        :return: polygon geometry
        """

        if geom  == []:
            pass
        else:
            pass
            # ring = ogr.Geometry(ogr.wkbMultiLineString)
            # ring.ForceToMultiLineString(geom)
            # print ring.ExportToWkt()
            # poly.BuildPolygonFromEdges(ring)


    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 0. create region box geometry from input raster
        region_box, region_point, left_box, bottom_box, right_box, top_box = self.input_lines.box()
        print (region_box)

        # poly = ogr.Geometry(ogr.wkbPolygon)
        # for keyName in inspect.getmembers(poly):
        #     print keyName

        # create intersection points (lines x box) and add them to region_box
        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            left_box, bottom_box, right_box, top_box = self._count_intersection(geom, region_point, region_box, left_box, bottom_box, right_box, top_box)


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

            if self.generalizer:
                geom_simplified = self.generalizer.perform(geom_closed)
            else:
                geom_simplified = geom_closed

            # 3. create polygons from closed lines
            polygon = self._create_polygon(geom_simplified)

            # 4. write polygons to output
            # self._write_output(polygon, value)
            #
            # print (self.input_lines.layer().GetFeatureCount())
