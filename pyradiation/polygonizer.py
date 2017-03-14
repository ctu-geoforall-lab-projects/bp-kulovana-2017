from .exception import RadiationError

class RadiationPolygonizer:
    def __init__(self, lines, generalizer=None):
        self.input_lines = lines
        self.generalizer = generalizer

    def destination(self, dst_filename=None, overwrite=True):
        pass

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
        lines = self._close_lines()

        # 2. perform generalization if defined
        if generalizer:
            lines = generalizer.perform(lines)

        # 3. create polygons from closed lines
        polygons = self._polygonize(lines)

        # 4. write polygons to output
        self._write_output()

        print (self.input_lines.layer().GetFeatureCount())
