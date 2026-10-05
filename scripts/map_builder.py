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
Build a 3D point cloud map (Bonxai .pcd) of a simulated world.

The robot is teleported (gz set_pose) to free positions found as it goes, and the lidar scans
taken there are put together at the ground-truth poses. A candidate position is taken when
ground was already seen around it and no obstacle is within --clearance.

Run it with the simulation up (gazebo_sim.launch.yaml), e.g.:
  ros2 run easynav_playground_summit map_builder.py /tmp/warehouse --world warehouse
"""

import argparse
import math
import subprocess
import time

from nav_msgs.msg import Odometry
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
import tf2_ros

GROUND_Z = 0.05      # points within this height are ground
OBST_Z = (0.1, 1.2)  # height band that blocks the robot


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def voxel(points, res):
    keys = np.floor(points / res).astype(np.int64)
    _, idx = np.unique(keys, axis=0, return_index=True)
    return points[idx]


class MapBuilder(Node):

    def __init__(self, args):
        super().__init__('map_builder', parameter_overrides=[
            rclpy.parameter.Parameter('use_sim_time', value=True)])
        self.args = args
        self.last = {}
        self.buf = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buf, self)
        self.create_subscription(PointCloud2, args.cloud_topic,
                                 lambda m: self.last.__setitem__('cloud', m),
                                 qos_profile_sensor_data)
        self.create_subscription(Odometry, args.ground_truth_topic,
                                 lambda m: self.last.__setitem__('gt', m), 10)

    def spin_for(self, sec):
        t0 = time.time()
        while time.time() - t0 < sec:
            rclpy.spin_once(self, timeout_sec=0.05)

    def teleport(self, x, y):
        req = (f'name: "{self.args.model}", position: {{x: {x}, y: {y}, z: 0.15}}, '
               'orientation: {w: 1}')
        subprocess.run(['gz', 'service', '-s', f'/world/{self.args.world}/set_pose',
                        '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
                        '--timeout', '2000', '--req', req], capture_output=True, timeout=10)

    def capture(self):
        """Return one lidar cloud in world coordinates (floor at z = 0) and the robot xy."""
        self.spin_for(self.args.settle)
        m = self.last.get('cloud')
        g = self.last.get('gt')
        if m is None or g is None:
            return None, None
        pts = point_cloud2.read_points_numpy(m, field_names=('x', 'y', 'z'), skip_nans=True)
        pts = pts[np.isfinite(pts).all(axis=1)]
        tr = self.buf.lookup_transform(self.args.robot_frame, m.header.frame_id, Time())
        q = tr.transform.rotation
        t = tr.transform.translation
        pb = pts @ quat_to_mat((q.x, q.y, q.z, q.w)).T + [t.x, t.y, t.z]
        pb = pb[np.hypot(pb[:, 0], pb[:, 1]) > self.args.robot_cut]  # the robot itself
        p = g.pose.pose
        o = p.orientation
        pw = pb @ quat_to_mat((o.x, o.y, o.z, o.w)).T + [p.position.x, p.position.y, 0.0]
        return pw, (p.position.x, p.position.y)

    def run(self):
        a = self.args
        t0 = time.time()
        while ('cloud' not in self.last or 'gt' not in self.last) and time.time() - t0 < 30:
            rclpy.spin_once(self, timeout_sec=0.1)

        cloud = np.zeros((0, 3))
        visited = 0
        start = (float(a.start[0]), float(a.start[1]))
        queue = [start]
        tried = set()
        while queue:
            x, y = queue.pop(0)
            key = (round(x / a.grid), round(y / a.grid))
            if key in tried:
                continue
            tried.add(key)
            if (x, y) != start:
                self.teleport(x, y)
            pw, at = self.capture()
            if pw is None or math.hypot(at[0] - x, at[1] - y) > 0.3:
                print(f'skip ({x:.1f}, {y:.1f}): robot at {at}', flush=True)
                continue
            visited += 1
            cloud = voxel(np.vstack([cloud, pw]), a.voxel)
            print(f'scan {visited:3d} at ({at[0]:6.2f}, {at[1]:6.2f}): {len(cloud)} points',
                  flush=True)
            # New candidates around: ground seen near them, nothing that blocks within clearance
            obst = cloud[(cloud[:, 2] > OBST_Z[0]) & (cloud[:, 2] < OBST_Z[1])]
            ground = cloud[np.abs(cloud[:, 2]) < GROUND_Z]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                cx = round((x + dx * a.grid) / a.grid) * a.grid
                cy = round((y + dy * a.grid) / a.grid) * a.grid
                if (round(cx / a.grid), round(cy / a.grid)) in tried:
                    continue
                if len(obst) and np.min(np.hypot(obst[:, 0] - cx, obst[:, 1] - cy)) < a.clearance:
                    continue
                if not len(ground) or np.sum(
                        np.hypot(ground[:, 0] - cx, ground[:, 1] - cy) < 0.8) < 5:
                    continue
                queue.append((cx, cy))

        self.teleport(*start)
        self.spin_for(2.0)

        with open(a.output + '.pcd', 'w') as f:
            f.write('# .PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\nFIELDS x y z\n'
                    'SIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n'
                    f'WIDTH {len(cloud)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n'
                    f'POINTS {len(cloud)}\nDATA ascii\n')
            np.savetxt(f, cloud, fmt='%.3f')
        print(f'done: {visited} scans, {len(cloud)} points in {a.output}.pcd', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('output', help='output prefix: writes <output>.pcd')
    parser.add_argument('--world', default='warehouse', help='Gazebo world name')
    parser.add_argument('--model', default='summit_xl', help='robot model name in Gazebo')
    parser.add_argument('--start', nargs=2, default=(0.0, 0.0), metavar=('X', 'Y'),
                        help='where the robot is (first scan)')
    parser.add_argument('--grid', type=float, default=1.0, help='candidate spacing (m)')
    parser.add_argument('--clearance', type=float, default=0.8,
                        help='free radius around a candidate (m)')
    parser.add_argument('--robot-cut', type=float, default=0.75,
                        help='points closer than this to the robot are the robot (m)')
    parser.add_argument('--voxel', type=float, default=0.05, help='cloud resolution (m)')
    parser.add_argument('--settle', type=float, default=2.5,
                        help='wait after each teleport (s)')
    parser.add_argument('--cloud-topic', default='/front_laser/points')
    parser.add_argument('--ground-truth-topic', default='/ground_truth')
    parser.add_argument('--robot-frame', default='base_footprint')
    args, _ = parser.parse_known_args()  # ignores --ros-args

    rclpy.init()
    node = MapBuilder(args)
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
