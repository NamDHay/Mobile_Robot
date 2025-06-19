#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
import message_filters
from math import degrees, atan2, sin, cos


class IMUYawPublisher:
    def __init__(self):
        rospy.init_node("imu_yaw_publisher")

        self.angle_z = 0.0  # yaw in radians
        self.prev_time = None

        # Publishers
        self.imu_pub = rospy.Publisher("/camera/imu/fused", Imu, queue_size=10)
        self.yaw_pub = rospy.Publisher("/camera/imu/yaw_deg", Float32, queue_size=10)

        # Subscribers with sync
        accel_sub = message_filters.Subscriber("/camera/accel/sample", Imu)
        gyro_sub = message_filters.Subscriber("/camera/gyro/sample", Imu)

        sync = message_filters.ApproximateTimeSynchronizer(
            [accel_sub, gyro_sub], queue_size=10, slop=0.01
        )
        sync.registerCallback(self.imu_callback)

    def imu_callback(self, accel_msg, gyro_msg):
        curr_time = gyro_msg.header.stamp.to_sec()

        if self.prev_time is not None:
            dt = curr_time - self.prev_time
            wz = gyro_msg.angular_velocity.y
            wz = 0 if wz < 0.01 else wz
            self.angle_z += wz * dt

            # Normalize angle to [-pi, pi]
            self.angle_z = atan2(sin(self.angle_z), cos(self.angle_z))
            yaw_deg = degrees(self.angle_z)

            # Log yaw
            rospy.loginfo("Yaw angle: %.2f degrees", yaw_deg)

            # Publish yaw
            self.yaw_pub.publish(yaw_deg)

            # Publish fused IMU
            imu_msg = Imu()
            imu_msg.header.stamp = gyro_msg.header.stamp
            imu_msg.header.frame_id = "camera_link"
            imu_msg.angular_velocity = gyro_msg.angular_velocity
            imu_msg.linear_acceleration = accel_msg.linear_acceleration
            imu_msg.orientation_covariance[0] = -1  # Orientation unknown
            self.imu_pub.publish(imu_msg)

        self.prev_time = curr_time


if __name__ == "__main__":
    try:
        IMUYawPublisher()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
