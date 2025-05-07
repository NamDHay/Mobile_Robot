#!/usr/bin/env python3

"""
Author: Your Name
Date: January 2025

This node subscribes to the odometry data from the DeadReckoningOdom node
and plots the x and y positions, as well as the linear and angular velocities.

"""

###############################################################################
# START: import the necessary libraries, modules, and packages
###############################################################################

import rospy
from nav_msgs.msg import Odometry
import matplotlib.pyplot as plt
from collections import deque

###############################################################################
# END: import the necessary libraries, modules, and packages
###############################################################################


class PlotOdometry:
    def __init__(self):
        # Initialize the node
        rospy.init_node("OdometryPlotter", anonymous=True)

        # Create a subscriber to the odometry topic
        rospy.Subscriber("odom", Odometry, self.callback)

        # Deques to store position and velocity data
        self.x_positions = deque(maxlen=100)
        self.y_positions = deque(maxlen=100)
        self.linear_velocities = deque(maxlen=100)
        self.angular_velocities = deque(maxlen=100)

        # Initialize the plot
        plt.ion()  # Set interactive mode on
        self.fig, self.axs = plt.subplots(4, 1, figsize=(10, 10))
        plt.show()

    def callback(self, msg):
        # Append new data to the deques
        self.x_positions.append(msg.pose.pose.position.x)
        self.y_positions.append(msg.pose.pose.position.y)
        self.linear_velocities.append(msg.twist.twist.linear.x)
        self.angular_velocities.append(msg.twist.twist.angular.z)

        # Update the plots
        self.update_plots()

    def update_plots(self):
        # Clear current plots
        for ax in self.axs:
            ax.clear()

        # Plot x position
        self.axs[0].plot(self.x_positions, label="X Position", color="blue")
        self.axs[0].set_title("X Position Over Time")
        self.axs[0].set_ylabel("X Position (m)")
        self.axs[0].grid()
        self.axs[0].legend()

        # Plot y position
        self.axs[1].plot(self.y_positions, label="Y Position", color="green")
        self.axs[1].set_title("Y Position Over Time")
        self.axs[1].set_ylabel("Y Position (m)")
        self.axs[1].grid()
        self.axs[1].legend()

        # Plot linear velocity
        self.axs[2].plot(
            self.linear_velocities, label="Linear Velocity", color="orange"
        )
        self.axs[2].set_title("Linear Velocity Over Time")
        self.axs[2].set_ylabel("Linear Velocity (m/s)")
        self.axs[2].grid()
        self.axs[2].legend()

        # Plot angular velocity
        self.axs[3].plot(self.angular_velocities, label="Angular Velocity", color="red")
        self.axs[3].set_title("Angular Velocity Over Time")
        self.axs[3].set_ylabel("Angular Velocity (rad/s)")
        self.axs[3].grid()
        self.axs[3].legend()

        # Refresh the plot
        plt.pause(0.01)

    def mainLoop(self):
        rospy.spin()  # Keep the node running


if __name__ == "__main__":
    plotter = PlotOdometry()
    plotter.mainLoop()
