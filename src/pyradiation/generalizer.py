import ogr
from .exception import RadiationError

class RadiationGeneralizer:
    def __init__(self):
        pass

    def perform(self, geometry, geom_id):
        tolerance = 0.000001
        ring2 = geometry.GetGeometryRef(0)
        while True:

            geom_simplified = geometry.Simplify(tolerance)

            ring3 = geom_simplified.GetGeometryRef(0)
            if ring3.GetPointCount() < 50:
                # print "ring3: {}, id: {}".format(ring3.GetPointCount(), geom_id)
                break
            else:
               tolerance = tolerance * 10

        return geom_simplified