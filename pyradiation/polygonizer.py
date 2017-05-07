import os
import tempfile

from osgeo import ogr

from .exception import RadiationError


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

    def _close_line(self, geom, line_id, reverse = False):
        """Close lines.

        If start point differs from end point than line is closed by
        region box geometry and if needed by other lines.

        :param geom: input lines geometry (defined as LineStrings)
        :param line_id: ID of an input geometry
        :param reverse: if TRUE iterate over intersection points in reverse order

        :return: closed geometry
        """

        if not geom.IsRing():
            if line_id == 16:  # non-ring feature
                return []
            multiline = ogr.Geometry(ogr.wkbMultiLineString)
            multiline.AddGeometry(geom)
            z = geom.GetZ(0)
            for line in self.line_list:
                if line.id == line_id:
                    start_main = line.start_point
                    end_main = line.end_point
                    print " "
                    print ('Main line: start: {}, end: {}'.format(start_main, end_main))

            multiline, line_last_id, geom_closed = self._find_next_point(z, end_main, start_main, multiline, reverse)

            while geom_closed == 0:
                for line in self.line_list:
                    if line.start_point == line_last_id:
                        start_line_next = line.start_point
                        end_line_next = line.end_point
                        multiline.AddGeometry(line.geom)
                        print ('Next line: start: {}, end: {}'.format(start_line_next, end_line_next))
                        multiline, line_last_id, geom_closed = self._find_next_point(z, end_line_next, start_main,
                                                                                     multiline, reverse)
                        break
                    elif line.end_point == line_last_id:
                        start_line_next = line.end_point
                        end_line_next = line.start_point
                        geom_reverse = ogr.Geometry(ogr.wkbLineString)
                        for i in range(line.geom.GetPointCount(), 0, -1):
                            pt = line.geom.GetPoint(i - 1)
                            geom_reverse.AddPoint(pt[0], pt[1], pt[2])
                        multiline.AddGeometry(geom_reverse)
                        print ('Next line: start: {}, end: {}'.format(start_line_next, end_line_next))
                        multiline, line_last_id, geom_closed = self._find_next_point(z, end_line_next, start_main,
                                                                                     multiline, reverse)
                        break
            else:
                print "ukonceny cyklus"
            return multiline
        else:
            return geom

    def _find_next_point(self, z, id_prev, start_main, multiline, reverse):
        '''
        Find next point with same Z coordinate or with Z == 0.
        If Z is 0 then add new line between last point and box vertex to multiline.
        If Z coordinate of new point is the same as of the multiline then add new line between last point and new
        point to multiline.
        If end point of new line is equal to the start point of multiline then geometry is closed.

        :param z: Z coordinate of multiline
        :param id_prev: ID of last point in multiline
        :param start_main: ID of start point of multiline
        :param multiline: input lines geometry (defined as MultiLineStrings)
        :param reverse: if TRUE iterate over intersection points in reverse order

        :return: multiline geometry, ID of the last point in multiline, info if geometry is closed
        '''
        if not reverse:
            intersection_sorted = self.intersection_sorted
        elif reverse:
            intersection_sorted = reversed(self.intersection_sorted)

        flag_inter_found = False
        for inter in intersection_sorted:
            if inter.id == id_prev:
                flag_inter_found = True
                end_line_x = inter.x
                end_line_y = inter.y
                continue
            if flag_inter_found:
                # print inter.id
                if inter.z == z:
                    line1 = ogr.Geometry(ogr.wkbLineString)
                    line1.AddPoint(end_line_x, end_line_y, z)
                    line1.AddPoint(inter.x, inter.y, inter.z)
                    multiline.AddGeometry(line1)
                    print ('Next line: start: {}, end: {}'.format(id_prev, inter.id))
                    line_last_id = inter.id
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
                    line1.AddPoint(end_line_x, end_line_y, z)
                    line1.AddPoint(inter.x, inter.y, z)
                    multiline.AddGeometry(line1)
                    print("pridan rohovy bod")
                    end_line_x = inter.x
                    end_line_y = inter.y

        return multiline, line_last_id, geom_closed

    def _count_intersection(self, geom, box, line_id):
        """
        Count intersection of input geometry and region_box in 2D.
        Add intersection point to a list in format [ID, X, Y, Z].
        Add info about input geometry to a list in format [ID of geometry, ID of start point, ID of end point, geometry]

        :param geom: input lines geometry (defined as LineStrings)
        :param box: region box geometry (defined as Linestring)
        :param line_id: ID of an input geometry
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
                new_line = MyLine(line_id, self.intersection_id, self.intersection_id + 1, geometry)
                self.line_list.append(new_line)
                z = geom.GetZ(0)
                for point in intersection_point:
                    new_inter = Intersection(self.intersection_id, point.GetX(), point.GetY(), z)
                    self.intersection_list.append(new_inter)
                    self.intersection_id += 1

    def _sort_intersection(self, sort_coor, sort, compare, ascend):
        """
        Sort intersection points and save them to a sorted list in anticlockwise order.
        Remove sorted points from unsorted list.

        :param sort_coor: coordinate for comparison
        :param sort: coordinate by which a list should be sorted (X=1, Y=2)
        :param compare: coordinate by which a list should be compared (X=1, Y=2)
        :param ascend: order of sorting (ascending=1, descending=0)
        """

        if ascend == 1 and sort == 1:
            intersection_sort = sorted(self.intersection_list, key=lambda p: p.x)
        elif ascend == 1 and sort == 2:
            intersection_sort = sorted(self.intersection_list, key=lambda p: p.y)
        elif ascend == 0 and sort == 1:
            intersection_sort = sorted(self.intersection_list, key=lambda p: p.x, reverse=True)
        elif ascend == 0 and sort == 2:
            intersection_sort = sorted(self.intersection_list, key=lambda p: p.y, reverse=True)
        else:
            print "problem s razenim"

        for p in intersection_sort:
            if compare == 1:
                if p.x == sort_coor:
                    self.intersection_sorted.append(p)
                    self.intersection_list.remove(p)
            elif compare == 2:
                if p.y == sort_coor:
                    self.intersection_sorted.append(p)
                    self.intersection_list.remove(p)

    def _create_polygon(self, geom, line_id):
        """Create polygon from closed linestring geometry.

        If input geometry is not closed linestring that PolygonError
        is raised.

        :param geom: input linestring geometry
        :param line_id: ID of an input geometry

        :return: polygon geometry
        """

        if geom == []:
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

            return poly

    def _write_output(self):
        # check if destination is defined
        pass

    def polygonize(self):
        # 0. create region box geometry from input raster
        region_box, region_point = self.input_lines.box()
        # region_point = (leftX, rightX, topY, bottomY)

        # 1. create intersection points (lines x box) and add them to intersection list (unsorted)
        self.intersection_list = []
        self.intersection_id = 0
        # Add region_box corners to intersection_list
        for i in range(0, region_box.GetPointCount() - 1):
            pt = region_box.GetPoint(i)
            new_inter = Intersection(self.intersection_id, pt[0], pt[1], pt[2])
            self.intersection_list.append(new_inter)
            self.intersection_id += 1

        self.line_list = []
        lines_layer = self.input_lines.layer()
        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom_id = feat.id
            geom = feat.GetGeometryRef()

            self._count_intersection(geom, region_box, geom_id)

        # 2. sort intersection points in anticlockwise order
        self.intersection_sorted = []
        # sort points on the left side
        self._sort_intersection(region_point[0], 2, 1, 0)
        # sort points on the bottom side
        self._sort_intersection(region_point[3], 1, 2, 1)
        # sort points on the right side
        self._sort_intersection(region_point[1], 2, 1, 1)
        # sort points on the top side
        self._sort_intersection(region_point[2], 1, 2, 0)

        self.intersection_sorted = self.intersection_sorted + self.intersection_sorted  # docasne reseni

        lines_layer.ResetReading()
        while True:
            feat = lines_layer.GetNextFeature()
            if feat is None:
                break

            geom_id = feat.id
            geom = feat.GetGeometryRef()
            # 3. close open isolines (based on bbox)
            # print warning if isolines cannot be closed
            geom_closed = self._close_line(geom, geom_id)
            geom_closed2 = self._close_line(geom, geom_id, reverse = True)

            # 4. perform generalization if defined
            if self.generalizer:
                geom_simplified = self.generalizer.perform(geom_closed)
                geom_simplified2 = self.generalizer.perform(geom_closed2)
            else:
                geom_simplified = geom_closed
                geom_simplified2 = geom_closed2

            # 5. create polygons from closed lines
            polygon = self._create_polygon(geom_simplified, geom_id)
            polygon2 = self._create_polygon(geom_simplified2, geom_id)

            # 6. write polygons to output
            # self._write_output(polygon, value)
            #
            # print (self.input_lines.layer().GetFeatureCount())
