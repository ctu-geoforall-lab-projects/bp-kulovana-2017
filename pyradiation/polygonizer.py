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
            # print("neuzavrena")
            return []
        else:
            return geom

    def _count_intersection(self, geom, box, intersection):
        """
        Count intersection of  input geometry and region_box. Add intersection point to a list.

        :param geom: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)
        :param intersection: list of intersection points

        :return: list of intersection points between region_box and unclosed lines
        """

        if not geom.IsRing():
            if not geom.Intersects(box):
                print ("Non-ring feature!!")
            else:
                intersection_point = geom.Intersection(box)
                for point in intersection_point:
                    intersection.append([point.GetX(), point.GetY()])

        return intersection

    def _sort_intersection(self, intersection, intersection_sorted, sort_coor, a, b, ascending):
        """
        Sort intersection points and save them to a new list in anticlockwise order.
        Remove sorted points from unsorted list.

        :param intersection: input unsorted intersection points (defined as List)
        :param intersection_sorted: input sorted intersection points (defined as List)
        :param sort_coor: coordinate for comparison
        :param a: coordinate by which a list should be sorted (X=0, Y=1)
        :param b: coordinate by which a list should be compared (X=0, Y=1)
        :param ascending: order of sorting (ascending=1, descending=0)

        :return: list of unsorted intersection points, list of sorted intersection points
        """

        if ascending == 1:
            intersection_sort = sorted(intersection, key=lambda p: p[a])
        elif ascending == 0:
            intersection_sort = sorted(intersection, key=lambda p: p[a], reverse=True)

        for p in intersection_sort:
            if p[b] == sort_coor:
                intersection_sorted.append(p)
                intersection.remove(p)

        return intersection, intersection_sorted

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
            ring = ogr.ForceToMultiLineString(geom)
            poly = ogr.BuildPolygonFromEdges(ring, 0, 1)
            # print poly

            # Put geometry inside a feature
            layerDefinition = self.output_layer.GetLayerDefn()
            featureIndex = 0
            feature = ogr.Feature(layerDefinition)
            feature.SetGeometry(poly)
            feature.SetFID(featureIndex)

            # Create the feature in the layer (shapefile)
            self.output_layer.CreateFeature(feature)

        # return poly

    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 0. create region box geometry from input raster
        region_box, region_point = self.input_lines.box()
        # region_point = (leftX, rightX, topY, bottomY)
        print (region_box)

        # poly = ogr.Geometry(ogr.wkbPolygon)
        # for keyName in inspect.getmembers(poly):
        #     print keyName

        # create intersection points (lines x box) and add them to intersection list (unsorted)
        intersection = []
        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            intersection = self._count_intersection(geom, region_box, intersection)

        # Sort intersection points in anticlockwise order
        intersection_sorted = []
        intersection_sorted.append([region_point[0], region_point[2]])  # add top left corner
        # sort points on the left side
        intersection, intersection_sorted = self._sort_intersection(intersection, intersection_sorted, region_point[0], 1, 0, 0)
        intersection_sorted.append([region_point[0], region_point[3]])  # add bottom left corner
        # sort points on the bottom side
        intersection, intersection_sorted = self._sort_intersection(intersection, intersection_sorted, region_point[3], 0, 1, 1)
        intersection_sorted.append([region_point[1], region_point[3]])  # add bottom right corner
        # sort points on the right side
        intersection, intersection_sorted = self._sort_intersection(intersection, intersection_sorted, region_point[1], 1, 0, 1)
        intersection_sorted.append([region_point[1], region_point[2]])  # add top right corner
        # sort points on the top side
        intersection, intersection_sorted = self._sort_intersection(intersection, intersection_sorted, region_point[2], 0, 1, 0)

        print ("serazene pruseciky: ", intersection_sorted)
        
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