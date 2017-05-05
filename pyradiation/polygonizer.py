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

    def _close_line(self, geom, intersection, line_list, line_id):
        """Close lines.

        If start point differs from end point than line is close by
        region box geometry. Intersection with region box is computed
        in 2D.

        :param geom: input lines geometry (defined as LineStrings)
        :param intersection:

        :return: closed geometry
        """

        if not geom.IsRing():
            if line_id == 16: # non-ring feature
                return []
            multiline = ogr.Geometry(ogr.wkbMultiLineString)
            multiline.AddGeometry(geom)
            z = geom.GetZ(0)
            for line in line_list:
                if line.id == line_id:
                    start_main = line.start_point
                    end_main = line.end_point
                    print " "
                    print ('Main line: start: {}, end: {}'.format(start_main, end_main))

            multiline, line_id_next, geom_closed = self._find_next_point(intersection, z, end_main, start_main, multiline)

            while geom_closed == 0:
                for line in line_list:
                    if line.start_point == line_id_next:
                        start_line_next = line.start_point
                        end_line_next = line.end_point
                        multiline.AddGeometry(line.geom)
                        print ('Next line: start: {}, end: {}'.format(start_line_next, end_line_next))
                        multiline, line_id_next, geom_closed = self._find_next_point(intersection, z, end_line_next, start_main, multiline)
                        break
                    elif line.end_point == line_id_next:
                        start_line_next = line.end_point
                        end_line_next = line.start_point
                        geom_reverse = ogr.Geometry(ogr.wkbLineString)
                        for i in range(line.geom.GetPointCount(), 0, -1):
                            pt = line.geom.GetPoint(i - 1)
                            geom_reverse.AddPoint(pt[0], pt[1], pt[2])
                        multiline.AddGeometry(geom_reverse)
                        print ('Next line: start: {}, end: {}'.format(start_line_next, end_line_next))
                        multiline, line_id_next, geom_closed = self._find_next_point(intersection, z, end_line_next, start_main, multiline)
                        break
            else:
                print "ukonceny cyklus"
            return multiline
        else:
            return geom

    def _find_next_point(self, intersection, z, id_prev, start_main, multiline):
        flag_inter_found = False
        for inter in intersection:
            if inter.id == id_prev:
                flag_inter_found = True
                end_line_x = inter.x
                end_line_y = inter.y
                continue
            if flag_inter_found:
                # print inter.id
                if inter.z == z:
                    line1 = ogr.Geometry(ogr.wkbLineString)
                    line1.AddPoint(end_line_x, end_line_y)
                    line1.AddPoint(inter.x, inter.y)
                    multiline.AddGeometry(line1)
                    print ('Next line: start: {}, end: {}'.format(id_prev , inter.id))
                    line_id_next = inter.id
                    if inter.id == start_main:
                        print "geometry closed"
                        geom_closed = 1
                        break
                    else:
                        print("nalezen bod dalsi lajny")
                        geom_closed = 0
                        break
                elif inter.z == 0:
                    line1 = ogr.Geometry(ogr.wkbLineString)
                    line1.AddPoint(end_line_x, end_line_y)
                    line1.AddPoint(inter.x, inter.y)
                    multiline.AddGeometry(line1)
                    print("pridan rohovy bod")

        return multiline, line_id_next, geom_closed

    def _count_intersection(self, geom, box, intersection_list, int_id, line_list, line_id):
        """
        Count intersection of  input geometry and region_box. Add intersection point to a list.

        :param geom: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)
        :param intersection: list of intersection points
        :param int_id: ID of an intersection point
        :param line_list: list of isolines info [ID of a line, ID of start point, ID of end point]
        :param line_id: ID of an input geometry

        :return: list of intersection points between region_box and unclosed lines
        """

        if not geom.IsRing():
            if not geom.Intersects(box):
                print ("Non-ring feature!!", line_id)
            else:
                intersection_point = geom.Intersection(box)
                geometry = ogr.Geometry(ogr.wkbLineString)
                for i in range(0, geom.GetPointCount()):
                    pt = geom.GetPoint(i)
                    geometry.AddPoint(pt[0], pt[1], pt[2])
                new_line = MyLine(line_id, int_id, int_id+1, geometry)
                line_list.append(new_line)
                z = geom.GetZ(0)
                for point in intersection_point:
                    new_inter = Intersection(int_id, point.GetX(), point.GetY(), z)
                    intersection_list.append(new_inter)
                    int_id = int_id+1

        line_id = line_id+1
        return intersection_list, int_id, line_list, line_id

    def _sort_intersection(self, intersection_list, intersection_sorted, sort_coor, sort, compare, ascend):
        """
        Sort intersection points and save them to a new list in anticlockwise order.
        Remove sorted points from unsorted list.

        :param intersection_list: input unsorted intersection points (defined as List)
        :param intersection_sorted: input sorted intersection points (defined as List)
        :param sort_coor: coordinate for comparison
        :param sort: coordinate by which a list should be sorted (X=1, Y=2)
        :param compare: coordinate by which a list should be compared (X=1, Y=2)
        :param ascend: order of sorting (ascending=1, descending=0)

        :return: list of unsorted intersection points, list of sorted intersection points
        """

        if ascend == 1 and sort == 1:
            intersection_sort = sorted(intersection_list, key=lambda p: p.x)
        elif ascend == 1 and sort == 2:
            intersection_sort = sorted(intersection_list, key=lambda p: p.y)
        elif ascend == 0 and sort == 1:
            intersection_sort = sorted(intersection_list, key=lambda p: p.x, reverse=True)
        elif ascend == 0 and sort == 2:
            intersection_sort = sorted(intersection_list, key=lambda p: p.y, reverse=True)
        else:
            print "problem s razenim"

        for p in intersection_sort:
            if compare == 1:
                if p.x == sort_coor:
                    intersection_sorted.append(p)
                    intersection_list.remove(p)
            elif compare == 2:
                if p.y == sort_coor:
                    intersection_sorted.append(p)
                    intersection_list.remove(p)

        return intersection_list, intersection_sorted

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

        # create intersection points (lines x box) and add them to intersection list (unsorted)
        intersection_list = []  # [int_id, X, Y, Z]
        int_id = 4  # id 0-3 -> box vertices
        line_list = []
        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        line_id = 0
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            intersection_list, int_id, line_list, line_id = self._count_intersection(geom, region_box, intersection_list, int_id, line_list, line_id)

        # Sort intersection points in anticlockwise order
        intersection_sorted = []
        topLeft = Intersection(0, region_point[0], region_point[2], 0)
        intersection_sorted.append(topLeft)
        # sort points on the left side
        intersection_list, intersection_sorted = self._sort_intersection(intersection_list, intersection_sorted, region_point[0], 2, 1, 0)
        bottomLeft = Intersection(1, region_point[0], region_point[3], 0)
        intersection_sorted.append(bottomLeft)
        # sort points on the bottom side
        intersection_list, intersection_sorted = self._sort_intersection(intersection_list, intersection_sorted, region_point[3], 1, 2, 1)
        bottomRight = Intersection(2, region_point[1], region_point[3], 0)
        intersection_sorted.append(bottomRight)
        # sort points on the right side
        intersection_list, intersection_sorted = self._sort_intersection(intersection_list, intersection_sorted, region_point[1], 2, 1, 1)
        topRight = Intersection(3, region_point[1], region_point[2], 0)
        intersection_sorted.append(topRight)
        # sort points on the top side
        intersection_list, intersection_sorted = self._sort_intersection(intersection_list, intersection_sorted, region_point[2], 1, 2, 0)

        intersection_sorted = intersection_sorted + intersection_sorted # docasne reseni

        line_id = 0
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom = feat.GetGeometryRef()
            # 1. close open isolines (based on bbox)
            # print warning if isolines cannot be closed
            geom_closed = self._close_line(geom, intersection_sorted, line_list, line_id)
            line_id = line_id + 1

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


class MyLine:
    def __init__(self, id, start, end, geom):
        self.id = id
        self.start_point = start
        self.end_point = end
        self.geom = geom


class Intersection:
    def __init__(self, id, x, y, z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z