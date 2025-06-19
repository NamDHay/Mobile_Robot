#!/usr/bin/env python3
import rospy
import pyaudio
import speech_recognition as sr
from rtabmap_msgs.srv import SetGoal, SetGoalRequest
from rtabmap_msgs.srv import ListLabels, ListLabelsRequest


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
        rospy.wait_for_service("/rtabmap/set_goal", timeout=10)

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


def get_connected_microphones():
    recognizer = sr.Recognizer()

    mic_list = sr.Microphone.list_microphone_names()

    p = pyaudio.PyAudio()

    connected_mics = []

    print("Scanning")

    for i, mic_name in enumerate(mic_list):
        try:
            with sr.Microphone(device_index=i) as source:
                device_info = p.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    connected_mics.append(
                        {
                            "index": i,
                            "name": mic_name,
                            "channels": device_info["maxInputChannels"],
                            "sample_rate": int(device_info["defaultSampleRate"]),
                        }
                    )
        except Exception as e:
            pass

    p.terminate()

    return connected_mics


def test_microphone(device_index):
    recognizer = sr.Recognizer()
    WAKE_WORD = "robot"  # Define the wake word (case-insensitive)

    try:
        with sr.Microphone(device_index=device_index) as source:
            print(f"Adjusting for ambient noise on device {device_index}...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            while not rospy.is_shutdown():
                print(
                    "Listening for wake word 'Robot'..."
                )  # Indicate waiting for wake word
                try:
                    # Listen for audio input with a timeout
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    text = recognizer.recognize_google(audio, language="vi-VN").lower()
                    print(f"Heard: {text}")

                    # Check if the wake word is in the recognized text
                    if WAKE_WORD in text:
                        print("Wake word detected! Ready for command...")
                        # Listen for the command after wake word
                        try:
                            print("Listening for command...")
                            audio = recognizer.listen(
                                source, timeout=5, phrase_time_limit=5
                            )
                            command = recognizer.recognize_google(
                                audio, language="vi-VN"
                            )
                            print(f"Command: {command}")
                            # Process the last word as the command (as per your original logic)
                            words = command.split()
                            last_word = words[-1] if words else None
                            if last_word:
                                success = set_rtabmap_goal(last_word)
                                if success:
                                    print(f"Successfully set goal to: {last_word}")
                                else:
                                    print(f"Failed to set goal to: {last_word}")
                            else:
                                print("No valid command received")
                        except sr.UnknownValueError:
                            print("Could not understand the command")
                        except sr.RequestError as e:
                            print(f"Error with Google Speech Recognition: {e}")
                    else:
                        print("Wake word not detected, continuing to listen...")

                except sr.WaitTimeoutError:
                    print("No speech detected, continuing to listen...")
                except sr.UnknownValueError:
                    print("Could not understand speech")
                except sr.RequestError as e:
                    print(f"Error with Google Speech Recognition: {e}")

    except Exception as e:
        print(f"Device checking failed: {e}")
        return False, None


def main():
    # Lấy danh sách các thiết bị micro đang kết nối
    connected_mics = get_connected_microphones()

    if not connected_mics:
        print("No device found\n")
        return

    print(f"Finding {len(connected_mics)} device:")
    for i, mic in enumerate(connected_mics):
        print(
            f"{i + 1}. {mic['name']} (Index: {mic['index']}, Channels: {mic['channels']}, Sample Rate: {mic['sample_rate']}Hz)"
        )

    try:
        index = int(input(f"Device ID (1-{len(connected_mics)}): ")) - 1
        if 0 <= index < len(connected_mics):
            device_index = connected_mics[index]["index"]
            print(f"\nChecking: {connected_mics[index]['name']}")
            test_microphone(device_index)
        else:
            print("ID not found\n.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
