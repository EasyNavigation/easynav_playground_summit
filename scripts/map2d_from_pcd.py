#!/usr/bin/env python3
# Copyright 2026 Intelligent Robotics Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Build a 2D occupancy grid (for a flat NavMap) from a 3D point cloud (.pcd, ascii).

Points in the robot's height band are obstacles. Free space is flood-filled from a seed inside
the walls, never past the walls' extent; the rest is unknown. Writes <output>.pgm and
<output>.yaml (map_server format), e.g.:
  ros2 run easynav_playground_summit map2d_from_pcd.py maps/warehouse.pcd maps/warehouse
"""

import argparse
import math
import os

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pcd', help='input cloud (.pcd, ascii, x y z)')
    parser.add_argument('output', help='output prefix: writes <output>.pgm and <output>.yaml')
    parser.add_argument('--seed', nargs=2, type=float, default=(0.0, 0.0), metavar=('X', 'Y'),
                        help='a free point inside the walls')
    parser.add_argument('--resolution', type=float, default=0.05, help='cell size (m)')
    parser.add_argument('--z-min', type=float, default=0.1, help='obstacle band bottom (m)')
    parser.add_argument('--z-max', type=float, default=1.2, help='obstacle band top (m)')
    args = parser.parse_args()
    res = args.resolution

    with open(args.pcd) as f:
        lines = f.read().split('\n')
    start = next(i for i, line in enumerate(lines) if line.startswith('DATA')) + 1
    cloud = np.array([line.split() for line in lines[start:] if line.strip()], dtype=float)
    obst = cloud[(cloud[:, 2] > args.z_min) & (cloud[:, 2] < args.z_max)]

    x0, y0 = math.floor(obst[:, 0].min()) - 1, math.floor(obst[:, 1].min()) - 1
    w = int(math.ceil((obst[:, 0].max() + 1 - x0) / res))
    h = int(math.ceil((obst[:, 1].max() + 1 - y0) / res))
    blocked = np.zeros((h, w), bool)
    rows = ((obst[:, 1] - y0) / res).astype(int)
    cols = ((obst[:, 0] - x0) / res).astype(int)
    blocked[rows, cols] = True
    grown = blocked.copy()  # close one-cell gaps between obstacle points
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grown |= np.roll(blocked, d, axis=(0, 1))
    rmin, rmax, cmin, cmax = rows.min(), rows.max(), cols.min(), cols.max()  # walls' extent

    free = np.zeros((h, w), bool)
    stack = [(int((args.seed[1] - y0) / res), int((args.seed[0] - x0) / res))]
    while stack:
        r, c = stack.pop()
        if r < rmin or c < cmin or r > rmax or c > cmax or free[r, c] or grown[r, c]:
            continue
        free[r, c] = True
        stack.extend(((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)))

    grid = np.full((h, w), 205, np.uint8)  # unknown
    grid[free] = 254
    grid[blocked] = 0
    with open(args.output + '.pgm', 'wb') as f:
        f.write(f'P5\n{w} {h}\n255\n'.encode())
        f.write(np.flipud(grid).tobytes())  # PGM rows go top-down
    name = os.path.basename(args.output)
    with open(args.output + '.yaml', 'w') as f:
        f.write(f'image: {name}.pgm\nmode: trinary\nresolution: {res}\n'
                f'origin: [{x0}, {y0}, 0]\n'
                'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n')
    print(f'{w}x{h} at {res} m, origin ({x0}, {y0}): free {free.sum()}, '
          f'occupied {blocked.sum()}')


if __name__ == '__main__':
    main()
