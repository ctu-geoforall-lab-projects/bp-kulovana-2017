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

    def _count_intersection(self, geom, box_point, box):
        """

        :param geom: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)

        :return: region box with new points at intersection of unclosed lines
        """
        leftX = box_point[0]
        rightX = box_point[1]
        topY = box_point[2]
        bottomY = box_point[3]

        p1 = ogr.Geometry(ogr.wkbPoint)
        p1.AddPoint(100, 100)
        p2 = ogr.Geometry(ogr.wkbPoint)
        p2.AddPoint(1, 50)

        points = [p1, p2]

        # for p in sorted(points, key=lambda point: point.GetX):
        #     print (p.GetX(), p.GetY())

        box_point = ogr.Geometry(ogr.wkbMultiPoint)
        box_point.AddPoint(1, 0)
        box_point.AddPoint(1, 1)
        box_point.AddPoint(1, 3)
        x = 1
        y = 2
        # if x == 1

        left_box = ogr.Geometry(ogr.wkbMultiPoint)
        point1 = ogr.Geometry(ogr.wkbPoint)
        point1.AddPoint(leftX, topY)
        left_box.AddGeometry(point1)
        point1.AddPoint(leftX, bottomY)
        left_box.AddGeometry(point1)

        if not geom.IsRing():
            intersection = geom.Intersection(box)
            print intersection.ExportToWkt()

            for point in intersection:
                # print ("X-ova bodu: ", point.GetX())
                if point.GetX() == leftX:
                    point1.AddPoint(point.GetX(), point.GetY())
                    left_box.AddGeometry(point1)
                    print("probehlo")
            for point in left_box:
                sorted(left_box, key=lambda point: point.GetX)

            print left_box.GetGeometryCount()
            print left_box.ExportToWkt()

            # for point in intersection:
            # box.AddPoint(point.GetX(), point.GetY())

            # for i in range(intersection.GetGeometryCount()):

        return box_point

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
        region_box, region_point = self.input_lines.box()
        print (region_box)

        # poly = ogr.Geometry(ogr.wkbPolygon)
        # for keyName in inspect.getmembers(poly):
        #     print keyName

        # create intersection points (lines x box)
        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            intersection = self._count_intersection(geom, region_point, region_box)

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
