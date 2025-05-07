#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import LaserScan

last_scan = None


def lidar_callback(data):
    global last_scan
    ranges = data.ranges
    angle_increment = data.angle_increment
    start_angle = data.angle_min

    min_angle = -180 * (3.14159 / 180)
    max_angle = 0 * (3.14159 / 180)

    min_index = int((min_angle - start_angle) / angle_increment)
    max_index = int((max_angle - start_angle) / angle_increment)

    filtered_ranges = ranges[min_index:max_index]

    filtered_data = LaserScan()
    filtered_data.header = data.header
    filtered_data.angle_min = min_angle
    filtered_data.angle_max = max_angle
    filtered_data.angle_increment = angle_increment
    filtered_data.range_min = data.range_min
    filtered_data.range_max = data.range_max
    filtered_data.ranges = filtered_ranges
    last_scan = filtered_data


def lidar_listener():
    rospy.init_node("lidar_filter", anonymous=True)

    filtered_pub = rospy.Publisher("/filtered_scan", LaserScan, queue_size=10)

    rospy.Subscriber("/scan", LaserScan, lidar_callback)
    rate = rospy.Rate(20)  # Try to publish at 20 Hz (same data)
    while not rospy.is_shutdown():
        if last_scan:
            last_scan.header.stamp = rospy.Time.now()  # Update timestamp
            filtered_pub.publish(last_scan)
        rate.sleep()


if __name__ == "__main__":
    try:
        lidar_listener()
    except rospy.ROSInterruptException:
        pass
