import os
import codecs
import inspect
from .exception import RadiationError
import mgrs


class Report:
    def __init__(self, path, index):

        """
        Create report file. Prints error when report txt file cannot be opened for writing.
        """

        try:
            try:
               # python 3.x
                self.report = open(path, 'w', encoding='utf-8')
            except:
               # python 2.x
                self.report = codecs.open(path, 'w', encoding='utf-8')
        except IOError as e:
            self.computeMessage.emit(u'Error', u'Unable open {} for writing. Reason: {}'.format(path, e),'CRITICAL')

        self.index = index

    def close(self):
        self.report.close()

    def write_polygon(self, poly):
        self.report_point = []
        z = poly.elev
        # print "point count: {}".format(poly.polygon.GetPointCount())
        # print "geometry count: {}".format(poly.polygon.GetGeometryCount())
        # if id == 5:
        #     for keyName in inspect.getmembers(poly.polygon):
        #        print keyName
        # for i in range(0, poly.polygon.GetPointCount()):
        #     point = poly.polygon.GetPoint(i)
        #     point_mgrs = mgrs.toMgrs(point[1], point[0], 5)
        #     print point
        #     # self.report_point.append(point_mgrs)
        #     print "probehlo"

        for ring in poly.polygon:
            for i in range(0, ring.GetPointCount()):
                point = ring.GetPoint(i)
                point_mgrs = mgrs.toMgrs(point[1], point[0], 5)
                # print "point mgrs: {}".format(point_mgrs)
                self.report_point.append(point_mgrs)

        # print len(self.report_point)
        self.createReport(z)

    def createReport(self, z):

        if self.index == 0:
            self. report.write(u'/{}BQM2'.format(z))
        elif self.index == 1:
            self.report.write(u'/{}CGH'.format(z))

        for point in self.report_point:
            self.report.write(u'/MGRS:{}'.format(point))

        self.report.write(u'//{ls}'.format(ls=os.linesep))