#!/usr/bin/env python
import sys

from pyradiation.contour import RadiationIsolines

def main(raster):
    rc = RadiationIsolines(raster)
    rc.generate([0.1, 1, 5, 10, 100, 1000])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Input raster must be given")

    main(sys.argv[1])
