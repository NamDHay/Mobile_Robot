#!/usr/bin/env python3

import rospy
from rtabmap_msgs.srv import SetLabel, SetLabelRequest
from rtabmap_msgs.srv import RemoveLabel, RemoveLabelRequest
from rtabmap_msgs.srv import SetGoal, SetGoalRequest
from rtabmap_msgs.srv import ListLabels, ListLabelsRequest
import argparse
import sys


def set_rtabmap_label(label):
    try:
        # Wait for the set_label service to become available
        rospy.wait_for_service("/rtabmap/set_label", timeout=10)

        # Create a service proxy for set_label
        set_label = rospy.ServiceProxy("/rtabmap/set_label", SetLabel)

        # Create the request
        request = SetLabelRequest()
        request.node_id = 0  # 0 means current (last) node
        request.node_label = label

        # Call the service (no response fields to check)
        set_label(request)

        rospy.loginfo(f"Successfully set label: {label}")
        return True

    except rospy.ServiceException as e:
        rospy.logerr(f"Set label service call failed: {e}")
        return False
    except rospy.ROSException as e:
        rospy.logerr(f"ROS error: {e}")
        return False


def remove_rtabmap_label(label):
    try:
        # Wait for the remove_label service to become available
        rospy.wait_for_service("/rtabmap/remove_label", timeout=10)

        # Create a service proxy for remove_label
        remove_label = rospy.ServiceProxy("/rtabmap/remove_label", RemoveLabel)

        # Create the request
        request = RemoveLabelRequest()
        request.label = label

        # Call the service (no response fields to check)
        remove_label(request)

        rospy.loginfo(f"Successfully removed label: {label}")
        return True

    except rospy.ServiceException as e:
        rospy.logerr(f"Remove label service call failed: {e}")
        return False
    except rospy.ROSException as e:
        rospy.logerr(f"ROS error: {e}")
        return False


def list_rtabmap_labels():
    try:
        # Wait for the list_labels service to become available
        rospy.wait_for_service("/rtabmap/list_labels", timeout=10)

        # Create a service proxy for list_labels
        list_labels = rospy.ServiceProxy("/rtabmap/list_labels", ListLabels)

        # Create the request (empty)
        request = ListLabelsRequest()

        # Call the service
        response = list_labels(request)

        # Create a dictionary of labels to node IDs
        label_to_id = dict(zip(response.labels, response.ids))

        rospy.loginfo(
            f"Retrieved {len(label_to_id)} labels: {list(label_to_id.keys())}"
        )
        return label_to_id

    except rospy.ServiceException as e:
        rospy.logerr(f"List labels service call failed: {e}")
        return None
    except rospy.ROSException as e:
        rospy.logerr(f"ROS error: {e}")
        return None


def set_rtabmap_goal(label):
    # Check if the label exists
    label_to_id = list_rtabmap_labels()
    if label_to_id is None:
        rospy.logerr("Failed to retrieve labels; cannot set goal")
        return False
    if label not in label_to_id:
        rospy.logerr(f"Label '{label}' not found in RTAB-Map's graph")
        return False

    try:
        # Wait for the set_goal service to become available
        rospy.wait_for_service("/rtabmap/set_goal", timeout=10)

        # Create a service proxy for set_goal
        set_goal = rospy.ServiceProxy("/rtabmap/set_goal", SetGoal)

        # Create the request
        request = SetGoalRequest()
        request.node_id = 0  # Use node_label instead of node_id
        request.node_label = label
        request.frame_id = ""  # Empty to use robot's base frame

        # Call the service
        response = set_goal(request)

        # Log response details
        rospy.loginfo(f"Successfully set goal to label: {label}")
        rospy.loginfo(f"Path IDs: {response.path_ids}")
        rospy.loginfo(f"Path Poses: {len(response.path_poses)} poses")
        rospy.loginfo(f"Planning Time: {response.planning_time} seconds")
        return True

    except rospy.ServiceException as e:
        rospy.logerr(f"Set goal service call failed: {e}")
        return False
    except rospy.ROSException as e:
        rospy.logerr(f"ROS error: {e}")
        return False


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Manage labels and set goals in RTAB-Map"
    )
    parser.add_argument("-a", "--add", type=str, help="Add a label (e.g., 'door1')")
    parser.add_argument(
        "-r", "--remove", type=str, help="Remove a label (e.g., 'door1')"
    )
    parser.add_argument(
        "-g",
        "--goal",
        type=str,
        help="Set a navigation goal to a labeled node (e.g., 'door1')",
    )
    args = parser.parse_args()

    # Initialize the ROS node
    rospy.init_node("rtabmap_label_manager", anonymous=True)

    # Ensure exactly one action is specified
    action_count = sum(1 for x in [args.add, args.remove, args.goal] if x is not None)
    if action_count != 1:
        rospy.logerr(
            "Usage: python3 label.py [-a <label_name> | -r <label_name> | -g <label_name>]"
        )
        sys.exit(1)

    # Handle add label
    if args.add:
        if not set_rtabmap_label(args.add):
            sys.exit(1)

    # Handle remove label
    if args.remove:
        if not remove_rtabmap_label(args.remove):
            sys.exit(1)

    # Handle set goal
    if args.goal:
        if not set_rtabmap_goal(args.goal):
            sys.exit(1)

    # Keep the node running briefly to ensure the service call is processed
    rospy.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
