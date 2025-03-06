import cv2
import numpy as np
import os
import datetime
from database import mark_attendance, get_students

# Kiểm tra thư viện face_recognition
try:
    import face_recognition  # Sửa từ my_face_recognition thành face_recognition
    # Kiểm tra hàm cần thiết có tồn tại không
    if hasattr(face_recognition, 'face_locations') and hasattr(face_recognition, 'face_encodings'):
        FACE_RECOGNITION_AVAILABLE = True
    else:
        FACE_RECOGNITION_AVAILABLE = False
        print("CẢNH BÁO: Thư viện face_recognition không có đầy đủ các phương thức cần thiết")
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("CẢNH BÁO: Thư viện face_recognition không được cài đặt!")
except Exception as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"CẢNH BÁO: Lỗi khi import face_recognition: {e}")


class FaceRecognitionSystem:
    def __init__(self, known_face_encodings=[], known_face_names=[], known_face_ids=[]):
        self.known_face_encodings = known_face_encodings
        self.known_face_names = known_face_names
        self.known_face_ids = known_face_ids
        self.face_detection_active = False
        self.camera = None
        self.process_counter = 0
        self.tolerance = 0.6  # Ngưỡng so sánh khuôn mặt (0.6 là mặc định)
        self.recognized_students = {}  # Lưu trữ sinh viên đã được nhận diện

    def start_camera(self):
        """Khởi động camera"""
        try:
            # Đặt độ phân giải ở mức vừa phải (640x480)
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.camera.isOpened():
                return False
            self.face_detection_active = True
            return True
        except Exception as e:
            print(f"Lỗi khi khởi động camera: {e}")
            return False

    def stop_camera(self):
        """Dừng camera"""
        self.face_detection_active = False
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        return True

    def update_known_faces(self, encodings, names, ids):
        """Cập nhật danh sách khuôn mặt đã biết"""
        self.known_face_encodings = encodings
        self.known_face_names = names
        self.known_face_ids = ids

    def get_attendance_status(self, student_id):
        """Kiểm tra sinh viên đã điểm danh trong ngày chưa"""
        now = datetime.datetime.now()
        date_string = now.strftime("%Y-%m-%d")
        students_df = get_students()
        student_info = students_df[students_df['id'] == student_id]

        if len(student_info) > 0:
            student_name = student_info.iloc[0]['name']
            student_class = student_info.iloc[0]['class']
            time_string = now.strftime("%H:%M:%S")

            # Lưu thời gian nhận diện
            if student_id not in self.recognized_students:
                self.recognized_students[student_id] = {
                    'name': student_name,
                    'timestamp': now.timestamp()
                }

            # Đánh dấu điểm danh và trả về trạng thái
            attendance_marked = mark_attendance(student_id, student_name, student_class, date_string, time_string)

            if attendance_marked:
                return f"{student_name} - Điểm danh thành công!"
            else:
                return f"{student_name} - Đã điểm danh!"
        return "Unknown"

    def get_recent_recognitions(self, seconds=5):
        """Lấy danh sách sinh viên được nhận diện gần đây"""
        now = datetime.datetime.now().timestamp()
        recent = []

        for student_id, info in list(self.recognized_students.items()):
            if now - info['timestamp'] < seconds:
                recent.append({
                    'id': student_id,
                    'name': info['name']
                })
            else:
                # Xóa nhận diện cũ
                self.recognized_students.pop(student_id, None)

        return recent

    def process_frame(self, frame):
        """Xử lý frame để nhận diện khuôn mặt"""
        if not FACE_RECOGNITION_AVAILABLE:
            # Hiển thị thông báo nếu không có face_recognition
            cv2.putText(frame, "Thư viện face_recognition không hoạt động!",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return frame

        # Chỉ xử lý mỗi 2 frame (thay vì 5) để tăng tốc độ nhận diện nhưng vẫn đủ nhanh
        self.process_counter = (self.process_counter + 1) % 2

        if self.process_counter == 0:
            # Kiểm tra frame có rỗng không
            if frame is None or frame.size == 0:
                return create_error_frame("Lỗi camera!")

            try:
                # Giữ kích thước frame ở mức 0.25 để đảm bảo độ chính xác nhận diện
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                # Tìm tất cả khuôn mặt trong frame
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Tỉ lệ lại vị trí khuôn mặt do đã resize frame
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # So sánh với các khuôn mặt đã biết
                    name = "Unknown"
                    student_id = ""

                    if len(self.known_face_encodings) > 0:
                        matches = face_recognition.compare_faces(
                            self.known_face_encodings, face_encoding, tolerance=self.tolerance
                        )

                        # Tìm khoảng cách nhỏ nhất
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                            student_id = self.known_face_ids[best_match_index]

                            # Lấy trạng thái điểm danh
                            name = self.get_attendance_status(student_id)

                    # Vẽ bounding box
                    cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)

                    # Vẽ label
                    cv2.rectangle(frame, (int(left), int(bottom) - 35), (int(right), int(bottom)), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, name, (int(left) + 6, int(bottom) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            except Exception as e:
                print(f"Lỗi khi xử lý frame: {e}")
                # Thêm thông báo lỗi vào frame
                cv2.putText(frame, f"Lỗi: {str(e)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame

    def generate_frames(self):
        """Generator để stream frames đã xử lý, nhận diện liên tục"""
        if not self.start_camera():
            yield None
            return

        while self.face_detection_active:
            try:
                success, frame = self.camera.read()
                if not success:
                    frame = create_error_frame("Không thể đọc từ camera!")
                else:
                    # Xử lý frame để nhận diện khuôn mặt
                    frame = self.process_frame(frame)

                # Mã hóa frame thành JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                # Gửi frame đến client
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print(f"Lỗi khi tạo frame: {e}")
                error_frame = create_error_frame(f"Lỗi: {str(e)}")
                ret, buffer = cv2.imencode('.jpg', error_frame)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        # Giải phóng camera khi kết thúc
        self.stop_camera()


def create_error_frame(message):
    """Tạo frame hiển thị thông báo lỗi"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame