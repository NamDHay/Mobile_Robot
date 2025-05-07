#!/usr/bin/env python3
import rospy
import serial
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32
import math

# Initialize serial communication
StmData = serial.Serial(
    "/dev/robot_uart",
    115200,
    timeout=1,
)
StmData.setDTR(False)
rospy.sleep(1)
StmData.setDTR(True)
d = 0.14  # Distance between wheels
a = 0.05  # Wheel radius


def pose_callback(msg=Twist()):
    print(msg)

    r_val = (1 / a) * (msg.linear.x - msg.angular.z * d / 2) * (60 / (math.pi * 2))
    l_val = (1 / a) * (msg.linear.x + msg.angular.z * d / 2) * (60 / (math.pi * 2))
    message = f"({int(r_val)};{int(l_val)})"
    try:
        StmData.write(message.encode("utf-8"))
        StmData.flush()
        print(message)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    rospy.init_node("robot")
    rospy.loginfo("Robot Controller start!")

    # Subscribers and publishers
    sub = rospy.Subscriber("/cmd_vel", Twist, callback=pose_callback)
    pub1 = rospy.Publisher("left_encoder_pulses", Int32, queue_size=10)
    pub2 = rospy.Publisher("right_encoder_pulses", Int32, queue_size=10)
    pub3 = rospy.Publisher("theta", Int32, queue_size=10)

    while not rospy.is_shutdown():
        if StmData.in_waiting > 0:
            line = StmData.readline().decode("utf-8").rstrip()
            print(line)
            # Assuming the line format is "value_r;value_l;value_theta"
            if line:
                parts = line.split(";")
                if len(parts) == 3:
                    a_t, b_t, c_t = map(str, parts)
                    cleaned_a_t = a_t.replace("\x00", "").strip()
                    cleaned_b_t = b_t.replace("\x00", "").strip()
                    cleaned_c_t = c_t.replace("\x00", "").strip()

                    msgR = Int32(data=int(cleaned_a_t))  # Right encoder value
                    msgL = Int32(data=int(cleaned_b_t))  # Left encoder value
                    msgTheta = Int32(data=int(cleaned_c_t))  # Theta value

                    # Publish the encoder values
                    pub1.publish(msgL)
                    pub2.publish(msgR)
                    pub3.publish(msgTheta)
                else:
                    rospy.logwarn(
                        "Invalid data format in line '%s': expected 3 values, got %d",
                        line.strip(),
                        len(parts),
                    )
            else:
                rospy.logwarn("Data empty")
