#!/usr/bin/env python3
"""

Author: Aleksandar Haber
Date: January -May 2024

This is the subscriber node that receives encoder readings from Arduino
and that calculates position x and y of the center of the robot as well as the
robot orientation angle (angle theta). These values are calculated from the encoder readings
by first calculating the velocity, and then x,y, and theta. That is, this code performs
dead reckoning. After calculating x,y, and theta, we create a quaternion and create an Odometry ROS object.
The odometry is then published. RViz uses the published odometry to graph and track the position and orientation of the robot in space

For more details on dead reckoning, see


https://aleksandarhaber.com/what-is-dead-reckoning-clear-explanation-with-python-simulation-part-i/

READ THE LICENSE!

"""
###############################################################################
# START: import the necessary libraries, modules and packages
###############################################################################

# ROS imports
import rospy

# we expect to receive Int32 from the left and right encoders
from std_msgs.msg import Int32

# this is the odometry data structure that this code
# will continiously update
from nav_msgs.msg import Odometry

# we need quaternions
from geometry_msgs.msg import Quaternion

# see this later on
from tf.broadcaster import TransformBroadcaster

# Python imports
from math import cos, sin, pi
import matplotlib.pyplot as plt
###############################################################################
# END: import the necessary libraries, modules and packages
###############################################################################

###############################################################################
# START: dead reckoning class
###############################################################################


class DeadReckoningOdom:
    ###############################################################################
    # START: Constructor function
    ###############################################################################

    def __init__(self):
        ###############################################################################
        # START: Definition of the variables, constants, parameters, names, etc.
        ###############################################################################
        # this is the node name that corresponds to this class
        # Node and topic configuration

        self.x_positions = []
        self.y_positions = []
        self.thetas = []
        self.linear_velocities = []
        self.angular_velocities = []
        self.timestamps = []

        self.nodeName = "DeadReckoningOdom"
        self.ready = 1
        self.ready2 = 1
        self.veloc_fil = 0
        self.vel_pre = 0
        self.theta_pre = 0

        self.angu_fil = 0
        self.angu_pre = 0
        self.theta_pre = 0
        self.angularVelocity = 0
        self.velocity = 0

        self.topicNameLeftEncoder = "left_encoder_pulses"
        self.topicNameRightEncoder = "right_encoder_pulses"
        self.topicNameTheta = "theta"
        self.baseFrameName = rospy.get_param("~base_frame_id", "base_link")
        self.odomFrameName = rospy.get_param("~odom_frame_id", "odom")

        # Robot configuration
        self.wheelRadius = 0.05
        self.distanceWheels = 0.29
        self.encoderPulsesConstant = 1848
        self.updateFrequencyPublish = 100
        self.yAc = 0
        self.theta_Real = 0

        # flag for initial reading - these variables are set to zero after
        # the first reading from the encoder topics
        self.flagInitialLeftEncoder = 1
        self.flagInitialRightEncoder = 1

        # these variables are used to store the initial readings from the encoder topics
        # namely, when you start the system, you might have non-zero encoder readings
        # we need to store these readings in these variables
        # here, they are initialized by zeros, however, they are updated in the first encoder reading
        self.initialValueLeftEncoder = 0
        self.initialValueRightEncoder = 0

        # left encoder readings
        # current time step k
        self.currentValueLeftEncoder = 0
        # previous time step k-1
        self.pastValueLeftEncoder = 0

        # right encoder readings
        # current time step k
        self.currentValueRightEncoder = 0
        # previous time step k-1
        self.pastValueRightEncoder = 0

        # time
        # callback functions for the right and left encoders will update
        # these time stampt
        # current time stamp for left encoder
        self.currentTimeLeftEncoder = 0
        # current time stamp for right encoder
        self.currentTimeRightEncoder = 0

        # the function self.calculateUpdate will use these time veriables and
        # it will update them on the basis of
        # self.currentTimeLeftEncoder and self.currentTimeRightEncoder
        # current and past time for the complete code
        # Time and pose
        self.currentTime = 0
        self.pastTime = 0
        self.x = 0.0
        self.y = 0.0
        # Orientation angle
        self.theta = 0

        ###############################################################################
        # END: Definition of the constants, parameters, names, etc.
        ###############################################################################

        ###############################################################################
        # START: Start the node
        ###############################################################################
        # here, we initialize our node
        # we set "anonymous=True" to make sure that the node has a unique name
        # this parameter will add random numbers to the end of the node name
        rospy.init_node(self.nodeName, anonymous=True)

        # get the past time
        self.pastTime = rospy.get_time()
        # update the node name
        self.nodeName = rospy.get_name()
        # print the message
        rospy.loginfo("The node - %s has started" % self.nodeName)
        ###############################################################################
        # END: Start the node
        ###############################################################################

        ###############################################################################
        # START: Subscribers and publishers
        ###############################################################################
        # NOTE HERE THAT THE TWO CALLBACK FUNCTIONS ARE DEFINED LATER IN THE CODE

        # subscribe to the messages from the left encoder
        rospy.Subscriber(
            self.topicNameLeftEncoder, Int32, self.callBackFunctionLeftEncoder
        )
        # subscribe to the messages from the right encoder
        rospy.Subscriber(
            self.topicNameRightEncoder, Int32, self.callBackFunctionRightEncoder
        )

        rospy.Subscriber(self.topicNameTheta, Int32, self.callBackFunctionTheta)

        # we publish an odometry
        self.odometryPublisher = rospy.Publisher("odom", Odometry, queue_size=5)
        self.odometryBroadcaster = TransformBroadcaster()

        ###############################################################################
        # END: Subscribers and publishers
        ###############################################################################

    ###############################################################################
    # END: Constructor function
    ###############################################################################

    ###############################################################################
    # START: callback function
    ###############################################################################
    # These are the callback functions, that are called when the messages are received
    # These functions will print the encoder readings to the screen
    # NOTE THAT THESE FUNCTIONS ARE RUNNING IN THE BACKGROUND BY THE ROS SYSTEM
    # left encoder callback function
    def callBackFunctionLeftEncoder(self, message1):
        if self.flagInitialLeftEncoder == 1:
            self.initialValueLeftEncoder = message1.data
            self.flagInitialLeftEncoder = 0
        else:
            self.currentValueLeftEncoder = message1.data - self.initialValueLeftEncoder
            self.currentTimeLeftEncoder = rospy.get_time()

        self.ready = 1
        # print("Left encoder pulses: %s" %(message1.data))
        # print("Time stamp left encoder %s" %(rospy.get_time()))

    # right encoder callback function
    def callBackFunctionRightEncoder(self, message2):
        if self.flagInitialRightEncoder == 1:
            self.initialValueRightEncoder = message2.data
            self.flagInitialRightEncoder = 0
        else:
            self.currentValueRightEncoder = (
                message2.data - self.initialValueRightEncoder
            )
            self.currentTimeRightEncoder = rospy.get_time()
        self.ready1 = 1

    def callBackFunctionTheta(self, message3):
        self.theta_Real = (message3.data / 10) * pi / 180

        # print("Right encoder pulses: %s" %message2.data)
        # print("Time stamp right encoder %s" %(rospy.get_time()))

    ###############################################################################
    # END: callback function
    ###############################################################################

    ###############################################################################
    # START: Update function
    ###############################################################################
    # this function performs calculations of x,y, and theta on the basis of the encoder
    # readings and after that it creates a quaternion and publishes odometry
    # https://aleksandarhaber.com/what-is-dead-reckoning-clear-explanation-with-python-simulation-part-i/

    def calculateUpdate(self):
        # Get the current time
        self.currentTime = rospy.get_time()

        if self.ready == 1:
            self.read = 0
            # self.ready = 0
            # self.ready1 = 0
            # Time step
            deltaT = self.currentTime - self.pastTime

            if deltaT > 0:  # Ensure deltaT is valid
                self.timestamps.append(self.currentTime)
                # Calculate left and right encoder angle changes
                leftEncoderAngleChange = (2 * pi / self.encoderPulsesConstant) * (
                    self.currentValueLeftEncoder - self.pastValueLeftEncoder
                )
                rightEncoderAngleChange = (2 * pi / self.encoderPulsesConstant) * (
                    self.currentValueRightEncoder - self.pastValueRightEncoder
                )

                # Apply deadzone to filter noise
                deadzoneThreshold = 0.0  # Adjust based on encoder noise level
                if abs(leftEncoderAngleChange) < deadzoneThreshold:
                    leftEncoderAngleChange = 0
                if abs(rightEncoderAngleChange) < deadzoneThreshold:
                    rightEncoderAngleChange = 0

                # Calculate wheel velocities
                leftWheelVelocity = (self.wheelRadius * leftEncoderAngleChange) / deltaT
                rightWheelVelocity = (
                    self.wheelRadius * rightEncoderAngleChange
                ) / deltaT

                # Apply smoothing to wheel velocities
                alpha = 0.8  # Smoothing factor
                self.smoothedLeftVelocity = alpha * leftWheelVelocity + (
                    1 - alpha
                ) * getattr(self, "smoothedLeftVelocity", leftWheelVelocity)
                self.smoothedRightVelocity = alpha * rightWheelVelocity + (
                    1 - alpha
                ) * getattr(self, "smoothedRightVelocity", rightWheelVelocity)

                # Correct for slip/skid
                slipCorrectionFactor = 1  # Adjust based on real-world tests
                self.smoothedLeftVelocity *= slipCorrectionFactor
                self.smoothedRightVelocity *= slipCorrectionFactor

                # Calculate robot center velocity and angular velocity
                velocity = (
                    2.15 * (self.smoothedLeftVelocity + self.smoothedRightVelocity) / 2
                )
                # angularVelocity = 2.3*(self.smoothedRightVelocity - self.smoothedLeftVelocity) / self.distanceWheels

                self.veloc_fil = (
                    0.854 * self.veloc_fil + 0.0728 * velocity + 0.0728 * self.vel_pre
                )
                self.vel_pre = velocity

                # self.angu_fil= 0.854 * self.angu_fil + 0.0728 * angularVelocity+ 0.0728 * self.angu_pre
                # self.angu_pre = angularVelocity

                # Dead reckoning calculations using midpoint integration

                self.x_positions.append(self.x)
                self.y_positions.append(self.y)
                self.thetas.append(self.theta)

                deltaS = velocity * deltaT

                self.theta = self.theta_Real

                self.angularVelocity = (self.theta - self.theta_pre) / deltaT

                self.theta_pre = self.theta

                self.angu_fil = (
                    0.854 * self.angu_fil
                    + 0.0728 * self.angularVelocity
                    + 0.0728 * self.angu_pre
                )
                self.angu_pre = self.angularVelocity

                self.linear_velocities.append(self.veloc_fil)
                self.angular_velocities.append(self.angu_fil)

                self.x += deltaS * cos(self.theta)
                self.y += deltaS * sin(self.theta)

                self.yAc = -self.y

            # # Debugging output
            # print("x,y,theta: (%s,%s,%s)" % (self.x, self.y, self.theta))
            # print("Time difference %s" % (self.currentTime - self.pastTime))
            # print("Encoder: (%s,%s) " % (self.currentValueLeftEncoder, self.currentValueRightEncoder))
            # Debugging output with reduced decimal places
            print(
                "x,y,theta: ({:.6f},{:.6f},{:.6f})".format(self.x, self.y, self.theta)
            )
            print("Time difference {:.6f}".format(deltaT))
            print(
                "Encoder: ({},{})".format(
                    self.currentValueLeftEncoder, self.currentValueRightEncoder
                )
            )

            # Create quaternion for odometry
            quaternion = Quaternion()
            quaternion.x = 0
            quaternion.y = 0
            quaternion.z = sin(self.theta / 2)
            quaternion.w = cos(self.theta / 2)
            quaternionTuple = (quaternion.x, quaternion.y, quaternion.z, quaternion.w)

            # Publish transform
            self.odometryBroadcaster.sendTransform(
                (self.x, self.y, 0),
                quaternionTuple,
                rospy.Time.now(),
                self.baseFrameName,
                self.odomFrameName,
            )

            # Publish odometry message
            odometry1 = Odometry()
            odometry1.header.stamp = rospy.Time.now()
            odometry1.header.frame_id = self.odomFrameName
            odometry1.pose.pose.position.x = self.x
            odometry1.pose.pose.position.y = self.y
            odometry1.pose.pose.position.z = 0
            odometry1.pose.pose.orientation = quaternion
            odometry1.child_frame_id = self.baseFrameName
            odometry1.twist.twist.linear.x = self.veloc_fil
            odometry1.twist.twist.linear.y = 0
            odometry1.twist.twist.angular.z = self.angu_fil

            self.odometryPublisher.publish(odometry1)

            # Update past values for next iteration
            self.pastTime = self.currentTime
            self.pastValueLeftEncoder = self.currentValueLeftEncoder
            self.pastValueRightEncoder = self.currentValueRightEncoder

    ###############################################################################
    # END: Update function
    ###############################################################################

    ###############################################################################
    # START: main function
    ###############################################################################

    def plotOdometry(self):
        plt.figure(figsize=(12, 8))

        # Subplot for x position over time
        plt.subplot(5, 1, 1)
        plt.plot(self.timestamps, self.x_positions, label="X Position", color="blue")
        plt.xlabel("Time (s)")
        plt.ylabel("X Position (m)")
        plt.title("X Position Over Time")
        plt.grid()
        plt.legend()

        # Subplot for y position over time
        plt.subplot(5, 1, 2)
        plt.plot(self.timestamps, self.y_positions, label="Y Position", color="green")
        plt.xlabel("Time (s)")
        plt.ylabel("Y Position (m)")
        plt.title("Y Position Over Time")
        plt.grid()
        plt.legend()

        # Subplot for theta position over time
        plt.subplot(5, 1, 3)
        plt.plot(self.timestamps, self.thetas, label="Theta ", color="red")
        plt.xlabel("Time (s)")
        plt.ylabel("theta (rad)")
        plt.title("Theta Position Over Time")
        plt.grid()
        plt.legend()

        # Subplot for linear velocity
        plt.subplot(5, 1, 4)
        plt.plot(self.linear_velocities, label="Linear Velocity", color="green")
        plt.xlabel("Time Steps")
        plt.ylabel("Linear Velocity (m/s)")
        plt.title("Linear Velocity Over Time")
        plt.grid()
        plt.legend()

        # Subplot for angular velocity
        plt.subplot(5, 1, 5)
        plt.plot(self.angular_velocities, label="Angular Velocity", color="orange")
        plt.xlabel("Time Steps")
        plt.ylabel("Angular Velocity (rad/s)")
        plt.title("Angular Velocity Over Time")
        plt.grid()
        plt.legend()

        plt.tight_layout()
        plt.show()

    def mainLoop(self):
        ROSRate = rospy.Rate(self.updateFrequencyPublish)

        while not rospy.is_shutdown():
            self.calculateUpdate()
            ROSRate.sleep()

        # self.plotOdometry()


###############################################################################
# START: end function
###############################################################################
###############################################################################
# END: dead reckoning class
###############################################################################

if __name__ == "__main__":
    """ main """
    objectDR = DeadReckoningOdom()
    objectDR.mainLoop()
