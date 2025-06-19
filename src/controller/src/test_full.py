#!/usr/bin/env python3
import rospy
import speech_recognition as sr
from gtts import gTTS
import pygame
import requests
import json
import time
import os
import numpy as np
import math
import threading
from queue import Queue, Empty
import asyncio
from io import BytesIO

# Import các thành phần của ROS
from std_msgs.msg import Bool
from rtabmap_msgs.srv import SetGoal, SetGoalRequest, ListLabels, ListLabelsRequest


# ==============================================================================
# LỚP AVATAR (GIỮ NGUYÊN TỪ CODE GỐC CỦA BẠN)
# ==============================================================================
class AIAvatar:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        self.base_size = 100
        self.scale_factor = 1.0

        # Animation states
        self.blink_timer = 0
        self.blink_interval = np.random.randint(60, 180)
        self.is_blinking = False
        self.blink_duration = 5
        self.blink_counter = 0

        self.mouth_animation_frame = 0
        self.mouth_open_amount = 0

        self.emotion_timer = 0
        self.emotion_intensity = 1.0

        self.emotions = {
            "happy": {
                "mouth_curve": 1,
                "eye_shape": "normal",
                "eyebrow_lift": 5,
                "cheek_lift": True,
            },
            "sad": {
                "mouth_curve": -1,
                "eye_shape": "droopy",
                "eyebrow_lift": -3,
                "cheek_lift": False,
            },
            "thinking": {
                "mouth_curve": 0,
                "eye_shape": "looking_up",
                "eyebrow_lift": 8,
                "cheek_lift": False,
            },
            "talking": {
                "mouth_curve": 0.3,
                "eye_shape": "normal",
                "eyebrow_lift": 2,
                "cheek_lift": False,
            },
            "listening": {
                "mouth_curve": 0.1,
                "eye_shape": "focused",
                "eyebrow_lift": 3,
                "cheek_lift": False,
            },
            "neutral": {
                "mouth_curve": 0,
                "eye_shape": "normal",
                "eyebrow_lift": 0,
                "cheek_lift": False,
            },
            "unanswered": {
                "mouth_curve": -0.8,
                "eye_shape": "droopy",
                "eyebrow_lift": -5,
                "cheek_lift": False,
            },
        }
        self.current_emotion = "neutral"

    def update_scale(self):
        screen_width, screen_height = self.screen.get_width(), self.screen.get_height()
        min_dimension = min(screen_width, screen_height)
        self.scale_factor = max(1.0, min(4.0, min_dimension / 400.0))

    def get_scaled_size(self, base_size):
        return int(base_size * self.scale_factor)

    def update_blink(self):
        self.blink_timer += 1
        if self.blink_timer >= self.blink_interval and not self.is_blinking:
            self.is_blinking = True
            self.blink_counter = 0
            self.blink_interval = np.random.randint(60, 180)
            self.blink_timer = 0
        if self.is_blinking:
            self.blink_counter += 1
            if self.blink_counter >= self.blink_duration:
                self.is_blinking = False

    def draw_eyes(self, center_x, center_y):
        emotion = self.emotions[self.current_emotion]
        eye_offset = self.get_scaled_size(30)
        eye_radius = self.get_scaled_size(12)
        pupil_radius = self.get_scaled_size(8)
        eyebrow_width = self.get_scaled_size(30)
        eyebrow_height = self.get_scaled_size(15)

        left_eye_x, left_eye_y = (
            center_x - eye_offset,
            center_y - self.get_scaled_size(20),
        )
        right_eye_x, right_eye_y = (
            center_x + eye_offset,
            center_y - self.get_scaled_size(20),
        )

        eyebrow_lift = self.get_scaled_size(emotion["eyebrow_lift"])
        eyebrow_offset = self.get_scaled_size(25)

        pygame.draw.arc(
            self.screen,
            (139, 69, 19),
            pygame.Rect(
                left_eye_x - eyebrow_width // 2,
                left_eye_y - eyebrow_offset + eyebrow_lift,
                eyebrow_width,
                eyebrow_height,
            ),
            0,
            np.pi,
            max(2, self.get_scaled_size(3)),
        )
        pygame.draw.arc(
            self.screen,
            (139, 69, 19),
            pygame.Rect(
                right_eye_x - eyebrow_width // 2,
                right_eye_y - eyebrow_offset + eyebrow_lift,
                eyebrow_width,
                eyebrow_height,
            ),
            0,
            np.pi,
            max(2, self.get_scaled_size(3)),
        )

        if self.is_blinking:
            line_length = self.get_scaled_size(12)
            line_width = max(2, self.get_scaled_size(3))
            pygame.draw.line(
                self.screen,
                (0, 0, 0),
                (left_eye_x - line_length, left_eye_y),
                (left_eye_x + line_length, left_eye_y),
                line_width,
            )
            pygame.draw.line(
                self.screen,
                (0, 0, 0),
                (right_eye_x - line_length, right_eye_y),
                (right_eye_x + line_length, right_eye_y),
                line_width,
            )
        else:
            if emotion["eye_shape"] == "droopy":
                eye_w, eye_h = self.get_scaled_size(24), self.get_scaled_size(15)
                pupil_w, pupil_h = self.get_scaled_size(16), self.get_scaled_size(10)
                pygame.draw.ellipse(
                    self.screen,
                    (255, 255, 255),
                    pygame.Rect(left_eye_x - eye_w // 2, left_eye_y - 5, eye_w, eye_h),
                )
                pygame.draw.ellipse(
                    self.screen,
                    (0, 0, 0),
                    pygame.Rect(
                        left_eye_x - pupil_w // 2, left_eye_y - 2, pupil_w, pupil_h
                    ),
                )
                pygame.draw.ellipse(
                    self.screen,
                    (255, 255, 255),
                    pygame.Rect(
                        right_eye_x - eye_w // 2, right_eye_y - 5, eye_w, eye_h
                    ),
                )
                pygame.draw.ellipse(
                    self.screen,
                    (0, 0, 0),
                    pygame.Rect(
                        right_eye_x - pupil_w // 2, right_eye_y - 2, pupil_w, pupil_h
                    ),
                )
            elif emotion["eye_shape"] == "looking_up":
                pupil_offset = self.get_scaled_size(5)
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (left_eye_x, left_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen,
                    (0, 0, 0),
                    (left_eye_x, left_eye_y - pupil_offset),
                    pupil_radius,
                )
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (right_eye_x, right_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen,
                    (0, 0, 0),
                    (right_eye_x, right_eye_y - pupil_offset),
                    pupil_radius,
                )
            elif emotion["eye_shape"] == "focused":
                focused_pupil = self.get_scaled_size(10)
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (left_eye_x, left_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen, (0, 0, 0), (left_eye_x, left_eye_y), focused_pupil
                )
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (right_eye_x, right_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen, (0, 0, 0), (right_eye_x, right_eye_y), focused_pupil
                )
            else:
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (left_eye_x, left_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen, (0, 0, 0), (left_eye_x, left_eye_y), pupil_radius
                )
                pygame.draw.circle(
                    self.screen, (255, 255, 255), (right_eye_x, right_eye_y), eye_radius
                )
                pygame.draw.circle(
                    self.screen, (0, 0, 0), (right_eye_x, right_eye_y), pupil_radius
                )
            if self.current_emotion == "happy":
                sparkle_size = max(1, self.get_scaled_size(2))
                sparkle_offset = self.get_scaled_size(3)
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (left_eye_x - sparkle_offset, left_eye_y - sparkle_offset),
                    sparkle_size,
                )
                pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (right_eye_x - sparkle_offset, right_eye_y - sparkle_offset),
                    sparkle_size,
                )

    def draw_mouth(self, center_x, center_y):
        emotion = self.emotions[self.current_emotion]
        mouth_x, mouth_y = center_x, center_y + self.get_scaled_size(30)
        curve = emotion["mouth_curve"]

        if self.current_emotion == "talking":
            self.mouth_animation_frame += 1
            base_open = self.get_scaled_size(15)
            min_open = self.get_scaled_size(5)
            mouth_width = self.get_scaled_size(40)
            open_amount = (
                abs(math.sin(self.mouth_animation_frame * 0.5)) * base_open + min_open
            )
            pygame.draw.ellipse(
                self.screen,
                (150, 50, 50),
                pygame.Rect(
                    mouth_x - mouth_width // 2,
                    mouth_y - open_amount // 2,
                    mouth_width,
                    open_amount,
                ),
            )
        elif curve > 0:
            smile_width = self.get_scaled_size(60)
            smile_height = self.get_scaled_size(20)
            line_width = max(2, self.get_scaled_size(4))
            smile_rect = pygame.Rect(
                mouth_x - smile_width // 2,
                mouth_y - smile_height // 2,
                smile_width,
                smile_height,
            )
            pygame.draw.arc(
                self.screen, (150, 50, 50), smile_rect, np.pi, 2 * np.pi, line_width
            )
            if emotion["cheek_lift"]:
                cheek_size = self.get_scaled_size(8)
                cheek_offset = self.get_scaled_size(50)
                cheek_y_offset = self.get_scaled_size(10)
                pygame.draw.circle(
                    self.screen,
                    (255, 200, 200),
                    (center_x - cheek_offset, center_y + cheek_y_offset),
                    cheek_size,
                )
                pygame.draw.circle(
                    self.screen,
                    (255, 200, 200),
                    (center_x + cheek_offset, center_y + cheek_y_offset),
                    cheek_size,
                )
        elif curve < 0:
            frown_width = self.get_scaled_size(50)
            frown_height = self.get_scaled_size(15)
            line_width = max(2, self.get_scaled_size(4))
            frown_rect = pygame.Rect(
                mouth_x - frown_width // 2,
                mouth_y + self.get_scaled_size(5),
                frown_width,
                frown_height,
            )
            pygame.draw.arc(
                self.screen, (100, 30, 30), frown_rect, 0, np.pi, line_width
            )
        else:
            if self.current_emotion == "listening":
                mouth_width = self.get_scaled_size(16)
                mouth_height = self.get_scaled_size(6)
                pygame.draw.ellipse(
                    self.screen,
                    (150, 50, 50),
                    pygame.Rect(
                        mouth_x - mouth_width // 2,
                        mouth_y - mouth_height // 2,
                        mouth_width,
                        mouth_height,
                    ),
                )
            else:
                line_length = self.get_scaled_size(15)
                line_width = max(2, self.get_scaled_size(3))
                pygame.draw.line(
                    self.screen,
                    (100, 30, 30),
                    (mouth_x - line_length, mouth_y),
                    (mouth_x + line_length, mouth_y),
                    line_width,
                )

    def draw_face(self):
        self.screen.fill((240, 248, 255))
        self.update_scale()
        center_x, center_y = self.screen.get_width() // 2, self.screen.get_height() // 2
        face_radius = self.get_scaled_size(self.base_size)
        face_border = max(2, self.get_scaled_size(3))
        pygame.draw.circle(
            self.screen, (255, 220, 177), (center_x, center_y), face_radius
        )
        pygame.draw.circle(
            self.screen, (245, 210, 167), (center_x, center_y), face_radius, face_border
        )
        self.draw_eyes(center_x, center_y)
        self.draw_mouth(center_x, center_y)
        nose_radius = max(2, self.get_scaled_size(3))
        nose_y_offset = self.get_scaled_size(5)
        pygame.draw.circle(
            self.screen,
            (235, 200, 157),
            (center_x, center_y + nose_y_offset),
            nose_radius,
        )

    def update(self):
        self.update_blink()
        self.draw_face()
        pygame.display.flip()
        self.clock.tick(30)
        return True

    def set_emotion(self, emotion):
        if emotion in self.emotions:
            self.current_emotion = emotion
            self.emotion_timer = 0
            if emotion == "talking":
                self.mouth_animation_frame = 0


# ==============================================================================
# CÁC LỚP NHẬN DẠNG GIỌNG NÓI (TỪ CODE AVATAR, ĐÃ TÍCH HỢP AVATAR)
# ==============================================================================
class EnhancedSpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_calibrated = False
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3

    def calibrate_for_noise(self, source, duration=1):
        if not self.is_calibrated:
            rospy.loginfo("🎤 Đang hiệu chỉnh micro để lọc nhiễu... Hãy giữ im lặng!")
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
            self.is_calibrated = True
            rospy.loginfo("✅ Hiệu chỉnh hoàn tất! Bây giờ bạn có thể nói chuyện.")

    def listen_with_noise_reduction(self, source, timeout=None, phrase_time_limit=None):
        return self.recognizer.listen(
            source, timeout=timeout, phrase_time_limit=phrase_time_limit
        )

    def recognize_speech(self, audio_data, language="vi-VN"):
        try:
            return self.recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            rospy.logerr(f"Lỗi kết nối Google Speech Recognition: {e}")
            return None


class ThreadedSpeechRecognizer:
    def __init__(self, avatar_instance):
        self.enhanced_recognizer = EnhancedSpeechRecognizer()
        self.result_queue = Queue()
        self.is_listening = False
        self.listen_thread = None
        self.WAKE_WORD = "robot"
        self.avatar = avatar_instance
        self.is_speaking_event = threading.Event()

    def start_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.listen_thread = threading.Thread(
                target=self._listen_worker, daemon=True
            )
            self.listen_thread.start()

    def stop_listening(self):
        self.is_listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)

    def _listen_worker(self):
        with sr.Microphone() as source:
            self.enhanced_recognizer.calibrate_for_noise(source, duration=1)

            while self.is_listening and not rospy.is_shutdown():
                if self.is_speaking_event.is_set():
                    time.sleep(0.1)
                    continue

                try:
                    audio = self.enhanced_recognizer.listen_with_noise_reduction(
                        source, timeout=5, phrase_time_limit=3
                    )

                    if not self.is_listening:
                        break
                    text = self.enhanced_recognizer.recognize_speech(audio)

                    if text and self.WAKE_WORD in text.lower():
                        rospy.loginfo("✅ Từ khóa 'robot' được phát hiện!")
                        self.avatar.set_emotion("listening")
                        rospy.loginfo("⚡ Đang lắng nghe lệnh...")
                        try:
                            audio_command = (
                                self.enhanced_recognizer.listen_with_noise_reduction(
                                    source, timeout=5, phrase_time_limit=8
                                )
                            )
                            if not self.is_listening:
                                break
                            command = self.enhanced_recognizer.recognize_speech(
                                audio_command
                            )
                            if command:
                                self.result_queue.put(command)
                                rospy.loginfo(f"👤 Bạn: {command}")
                            else:
                                rospy.logwarn("Không hiểu lệnh sau từ khóa.")
                                self.avatar.set_emotion("unanswered")
                        except sr.WaitTimeoutError:
                            rospy.logwarn("Hết thời gian chờ lệnh sau từ khóa.")
                            self.avatar.set_emotion("unanswered")
                        except Exception as e:
                            rospy.logerr(f"❌ Lỗi khi lắng nghe lệnh: {e}")
                            self.avatar.set_emotion("unanswered")

                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    rospy.logerr(f"❌ Lỗi nhận diện giọng nói khi chờ từ khóa: {e}")

    def get_result(self):
        try:
            return self.result_queue.get_nowait()
        except Empty:
            return None


# ==============================================================================
# CLASS CHÍNH ĐIỀU KHIỂN TOÀN BỘ ỨNG DỤNG
# ==============================================================================
class RosAvatarNavigator:
    def __init__(self):
        # --- Khởi tạo ROS ---
        rospy.init_node("ros_avatar_navigator_node", anonymous=False)
        self.goal_reached_flag = None
        self.rtabmap_labels = {}
        rospy.Subscriber("/rtabmap/goal_reached", Bool, self.goal_reached_callback)

        # --- Khởi tạo Pygame ---
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption("ROS Avatar Navigator")

        # --- Khởi tạo các thành phần ---
        self.avatar = AIAvatar(screen)
        self.speech_recognizer = ThreadedSpeechRecognizer(self.avatar)

        # --- API Settings ---
        self.NgrokURL = (
            "https://6b42-34-91-181-100.ngrok-free.app"  # Đảm bảo URL này còn hoạt động
        )
        self.chat_url = self.NgrokURL + "/chat/noauth"
        self.headers = {"Content-Type": "application/json"}
        self.session_id = None

    # --- Các hàm của ROS ---
    def goal_reached_callback(self, msg):
        rospy.loginfo("Nhận được trạng thái goal_reached.")
        self.goal_reached_flag = msg.data

    def list_rtabmap_labels(self):
        try:
            rospy.wait_for_service("/rtabmap/list_labels", timeout=5)
            list_labels_srv = rospy.ServiceProxy("/rtabmap/list_labels", ListLabels)
            response = list_labels_srv(ListLabelsRequest())
            label_to_id = dict(zip(response.labels, response.ids))
            rospy.loginfo(
                f"Lấy được {len(label_to_id)} địa điểm: {list(label_to_id.keys())}"
            )
            return label_to_id
        except Exception as e:
            rospy.logerr(f"Lỗi khi lấy danh sách địa điểm: {e}")
            return {}

    def set_rtabmap_goal(self, label):
        if not self.rtabmap_labels:
            asyncio.run(
                self.speak(
                    "Không thể lấy danh sách các địa điểm. Vui lòng kiểm tra RTAB-Map."
                )
            )
            return False
        if label not in self.rtabmap_labels:
            asyncio.run(self.speak(f"Địa điểm '{label}' không tìm thấy trong bản đồ."))
            return False

        try:
            rospy.wait_for_service("/rtabmap/set_goal", timeout=5)
            set_goal_srv = rospy.ServiceProxy("/rtabmap/set_goal", SetGoal)
            request = SetGoalRequest(node_label=label)
            set_goal_srv(request)
            asyncio.run(self.speak(f"Đã đặt mục tiêu đến địa điểm '{label}'."))
            rospy.loginfo(f"Successfully set goal to label: {label}")
            return True
        except Exception as e:
            asyncio.run(self.speak(f"Có lỗi khi đặt mục tiêu đến '{label}'."))
            rospy.logerr(f"Lỗi khi đặt mục tiêu: {e}")
            return False

    # --- Các hàm của Chatbot ---
    def chat_with_bot(self, query):
        payload = {"query": query}
        if self.session_id:
            payload["session_id"] = self.session_id

        try:
            response = requests.post(
                self.chat_url,
                data=json.dumps(payload),
                headers=self.headers,
                verify=False,
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                if self.session_id is None and "session_id" in data:
                    self.session_id = data["session_id"]
                return data["response"]
            else:
                return "Xin lỗi, hệ thống đang gặp sự cố."
        except Exception as e:
            rospy.logerr(f" Lỗi kết nối chatbot: {e}")
            return "Không thể kết nối đến server chatbot."

    # --- Hàm nói (TTS) đã được tối ưu hóa ---
    async def speak(self, text):
        self.speech_recognizer.is_speaking_event.set()
        rospy.loginfo(f" Trợ lý: {text}")
        self.avatar.set_emotion("talking")

        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=text, lang="vi")
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)

            pygame.mixer.music.load(mp3_fp)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() and not rospy.is_shutdown():
                if not self.avatar.update():
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.033)

        except Exception as e:
            rospy.logerr(f"❌ Lỗi phát âm thanh: {e}")
            self.avatar.set_emotion("unanswered")
        finally:
            pygame.mixer.music.unload()
            self.speech_recognizer.is_speaking_event.clear()
            self.avatar.set_emotion("neutral")

    # --- Hàm xử lý lệnh ---
    async def handle_command(self, command):
        processed_command = command.lower().strip()

        # BỘ ĐỊNH TUYẾN LỆNH
        # Ưu tiên các lệnh điều hướng ROS trước
        if "danh sách" in processed_command:
            self.avatar.set_emotion("thinking")
            if self.rtabmap_labels:
                await self.speak("Các địa điểm hiện có là:")
                for label_name in self.rtabmap_labels.keys():
                    await self.speak(label_name)
            else:
                await self.speak("Hiện không có địa điểm nào trong bản đồ.")

        elif "đi tới" in processed_command or "đến" in processed_command:
            self.avatar.set_emotion("thinking")
            target_label = None
            if self.rtabmap_labels:
                for label_name in self.rtabmap_labels.keys():
                    if label_name.lower() in processed_command:
                        target_label = label_name
                        break

            if target_label:
                self.set_rtabmap_goal(target_label)
            else:
                await self.speak(
                    "Tôi không tìm thấy địa điểm bạn muốn đến. Bạn có thể nói 'danh sách' để xem các lựa chọn."
                )

            # Nếu không phải lệnh ROS, xử lý như chat thông thường
        else:
            self.avatar.set_emotion("thinking")
            rospy.loginfo("🔍 Đang tìm câu trả lời ...")
            answer = self.chat_with_bot(command)

            # Cập nhật cảm xúc dựa trên câu trả lời
            if any(
                word in answer.lower() for word in ["vui", "hạnh phúc", "tốt", "tuyệt"]
            ):
                self.avatar.set_emotion("happy")
            elif any(word in answer.lower() for word in ["buồn", "tiếc", "xin lỗi"]):
                self.avatar.set_emotion("sad")
            else:
                self.avatar.set_emotion("neutral")

            await self.speak(answer)

    # --- Vòng lặp chính của ứng dụng ---
    async def run(self):
        self.avatar.set_emotion("neutral")

        # Lấy danh sách địa điểm khi khởi động
        self.rtabmap_labels = self.list_rtabmap_labels()
        if not self.rtabmap_labels:
            await self.speak(
                "Cảnh báo, không kết nối được với RTAB-Map để lấy danh sách địa điểm."
            )

        await self.speak("Xin chào! Hãy nói 'robot' để bắt đầu.")
        self.speech_recognizer.start_listening()

        running = True
        try:
            while running and not rospy.is_shutdown():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.VIDEORESIZE:
                        self.avatar.screen = pygame.display.set_mode(
                            (event.w, event.h), pygame.RESIZABLE
                        )

                if not self.avatar.update():
                    running = False
                    break

                # Xử lý lệnh từ hàng đợi
                command = self.speech_recognizer.get_result()
                if command:
                    if command.lower().strip() in ["thoát", "tạm biệt"]:
                        running = False
                        await self.speak("Tạm biệt!")
                    else:
                        await self.handle_command(command)

                # Kiểm tra trạng thái đến đích của ROS
                if self.goal_reached_flag is True:
                    self.goal_reached_flag = None  # Reset cờ
                    self.avatar.set_emotion("happy")
                    await self.speak("Đã đến đích thành công!")
                elif self.goal_reached_flag is False:
                    self.goal_reached_flag = None  # Reset cờ
                    self.avatar.set_emotion("sad")
                    await self.speak("Rất tiếc, không thể đến được đích.")

                await asyncio.sleep(0.01)

        except (rospy.ROSInterruptException, KeyboardInterrupt):
            rospy.loginfo("🛑 Dừng chương trình...")
        finally:
            self.speech_recognizer.stop_listening()
            pygame.quit()
            rospy.loginfo("✅ Node đã dừng.")


if __name__ == "__main__":
    try:
        navigator = RosAvatarNavigator()
        asyncio.run(navigator.run())
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"Lỗi nghiêm trọng ngoài vòng lặp chính: {e}")

