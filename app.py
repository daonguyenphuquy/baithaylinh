from flask import Flask, render_template, request, redirect, url_for, Response, jsonify, flash
import cv2
import os
import pandas as pd
import numpy as np
import datetime
import time
import shutil
import base64
from werkzeug.utils import secure_filename
import face_recognition  # Import thư viện chính thức

app = Flask(__name__)
app.secret_key = 'face_recognition_attendance_system'  # Thêm secret key để sử dụng flash

# Đường dẫn lưu dữ liệu
DATA_PATH = 'data'
FACES_PATH = os.path.join(DATA_PATH, 'faces')
STUDENTS_FILE = os.path.join(DATA_PATH, 'students.csv')
ATTENDANCE_FILE = os.path.join(DATA_PATH, 'attendance.csv')

# Tạo thư mục nếu chưa tồn tại
os.makedirs(DATA_PATH, exist_ok=True)
os.makedirs(FACES_PATH, exist_ok=True)

# Khởi tạo DataFrame nếu chưa tồn tại
if not os.path.exists(STUDENTS_FILE):
    pd.DataFrame(columns=['id', 'name', 'class']).to_csv(STUDENTS_FILE, index=False)

if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time']).to_csv(ATTENDANCE_FILE, index=False)

# Tạo danh sách khuôn mặt đã biết
known_face_encodings = []
known_face_names = []
known_face_ids = []

# Kiểm tra thư viện face_recognition
FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition  # Import thư viện chính thức từ site-packages

    # Debug để kiểm tra nguồn import
    print(f"Imported face_recognition from: {face_recognition.__file__}")

    # Kiểm tra phiên bản thư viện face_recognition (tùy chọn)
    if hasattr(face_recognition, '__version__'):
        print(f"Face Recognition version: {face_recognition.__version__}")

    # Kiểm tra hàm cần thiết có tồn tại không
    if hasattr(face_recognition, 'face_locations') and hasattr(face_recognition, 'face_encodings') and hasattr(
            face_recognition, 'compare_faces'):
        try:
            # Tạo một hình ảnh test nhỏ
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            # Thử sử dụng các hàm
            _ = face_recognition.face_locations(test_image)
            FACE_RECOGNITION_AVAILABLE = True
            print("Thư viện face_recognition hoạt động đúng!")
        except Exception as e:
            print(f"Lỗi khi kiểm tra hàm face_recognition: {e}")
    else:
        print("CẢNH BÁO: Thư viện face_recognition không có đầy đủ các phương thức cần thiết")
except ImportError:
    print("CẢNH BÁO: Thư viện face_recognition không được cài đặt!")
except Exception as e:
    print(f"CẢNH BÁO: Lỗi khi import face_recognition: {e}")


def load_known_faces():
    """Tải danh sách khuôn mặt đã biết từ thư mục faces"""
    global known_face_encodings, known_face_names, known_face_ids

    if not FACE_RECOGNITION_AVAILABLE:
        print("Không thể tải khuôn mặt do thư viện face_recognition không hoạt động")
        return

    try:
        students_df = pd.read_csv(STUDENTS_FILE)
    except Exception as e:
        print(f"Lỗi khi đọc file students.csv: {e}")
        students_df = pd.DataFrame(columns=['id', 'name', 'class'])

    known_face_encodings.clear()
    known_face_names.clear()
    known_face_ids.clear()

    for index, row in students_df.iterrows():
        student_id = row['id']
        student_name = row['name']
        face_image_path = os.path.join(FACES_PATH, f"{student_id}.jpg")

        if os.path.exists(face_image_path):
            try:
                # Sử dụng cv2 để đọc ảnh
                face_image = cv2.imread(face_image_path)
                if face_image is None:
                    print(f"Không thể đọc ảnh: {face_image_path}")
                    continue

                # Chuyển sang RGB (face_recognition yêu cầu ảnh RGB)
                face_image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                # Tìm khuôn mặt trong ảnh
                face_encoding = face_recognition.face_encodings(face_image_rgb)

                if len(face_encoding) > 0:
                    known_face_encodings.append(face_encoding[0])
                    known_face_names.append(student_name)
                    known_face_ids.append(student_id)
            except Exception as e:
                print(f"Lỗi khi tải ảnh {face_image_path}: {e}")


# Load khuôn mặt khi khởi động nếu thư viện face_recognition hoạt động
if FACE_RECOGNITION_AVAILABLE:
    load_known_faces()

# Biến toàn cục cho camera
camera = None
face_detection_active = False
recognized_faces = {}  # Lưu thông tin nhận diện để hiển thị liên tục


def recognize_face_in_image(image_array):
    """Nhận diện khuôn mặt trong ảnh đã chụp"""
    if not FACE_RECOGNITION_AVAILABLE:
        return None, None, None

    try:
        # Chuyển ảnh sang RGB (face_recognition yêu cầu định dạng RGB)
        rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        # Tìm vị trí khuôn mặt trong ảnh
        face_locations = face_recognition.face_locations(rgb_image)

        if len(face_locations) == 0:
            return None, None, None

        # Lấy encodings của khuôn mặt đầu tiên
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations[0:1])  # Chỉ lấy khuôn mặt đầu tiên

        best_match_name = None
        best_match_id = None
        best_match_class = None

        # So sánh với khuôn mặt đã biết
        if len(known_face_encodings) > 0 and len(face_encodings) > 0:
            face_encoding = face_encodings[0]  # Lấy khuôn mặt đầu tiên

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)

            # Tìm khoảng cách nhỏ nhất
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                best_match_id = known_face_ids[best_match_index]
                best_match_name = known_face_names[best_match_index]

                # Tìm thông tin lớp học
                students_df = pd.read_csv(STUDENTS_FILE)
                student_info = students_df[students_df['id'] == best_match_id]

                if len(student_info) > 0:
                    best_match_class = student_info.iloc[0]['class']

        return best_match_name, best_match_id, best_match_class
    except Exception as e:
        print(f"Lỗi khi nhận diện khuôn mặt: {e}")
        return None, None, None


def mark_attendance(student_id, student_name, student_class):
    """Ghi nhận điểm danh cho sinh viên"""
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    time_string = now.strftime("%H:%M:%S")

    # Đọc file CSV hiện tại
    try:
        attendance_df = pd.read_csv(ATTENDANCE_FILE)
        # Đảm bảo các cột cần thiết tồn tại
        required_columns = ['id', 'name', 'class', 'date', 'time']
        for col in required_columns:
            if col not in attendance_df.columns:
                attendance_df[col] = pd.NA
    except pd.errors.EmptyDataError:
        # Nếu file rỗng, tạo DataFrame mới
        attendance_df = pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time'])
    except Exception as e:
        print(f"Lỗi khi đọc file điểm danh: {e}")
        attendance_df = pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time'])

    # Kiểm tra xem sinh viên đã điểm danh trong ngày chưa
    today_attendance = attendance_df[(attendance_df['id'] == student_id) &
                                     (attendance_df['date'] == date_string)]

    if len(today_attendance) == 0:
        new_attendance = pd.DataFrame({
            'id': [student_id],
            'name': [student_name],
            'class': [student_class],
            'date': [date_string],
            'time': [time_string]
        })

        attendance_df = pd.concat([attendance_df, new_attendance], ignore_index=True)
        attendance_df.to_csv(ATTENDANCE_FILE, index=False)
        return True

    return False


def get_today_attendance():
    """Lấy danh sách sinh viên điểm danh trong ngày"""
    now = datetime.datetime.now()
    date_string = now.strftime("%Y-%m-%d")

    try:
        attendance_df = pd.read_csv(ATTENDANCE_FILE)
        # Kiểm tra xem cột 'date' có trong DataFrame không
        if 'date' not in attendance_df.columns:
            print("Cột 'date' không tồn tại trong file attendance.csv")
            return []
    except pd.errors.EmptyDataError:
        print("File attendance.csv rỗng")
        return []
    except Exception as e:
        print(f"Lỗi khi đọc file điểm danh: {e}")
        return []

    # Nếu DataFrame rỗng hoặc không có cột 'date', trả về danh sách rỗng
    if attendance_df.empty or 'date' not in attendance_df.columns:
        return []

    today_records = attendance_df[attendance_df['date'] == date_string]
    if today_records.empty:
        return []

    # Sắp xếp theo thời gian mới nhất
    today_records = today_records.sort_values(by='time', ascending=False)

    # Chuyển thành danh sách từ điển
    return today_records.to_dict('records')


def generate_frames():
    """Tạo frame cho video stream, nhận diện liên tục cho đến khi dừng camera"""
    global camera, face_detection_active, recognized_faces

    if not FACE_RECOGNITION_AVAILABLE:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg',
                                                                  create_error_frame(
                                                                      "Thư viện face_recognition không hoạt động!"))[
                   1].tobytes() + b'\r\n')
        return

    # Kiểm tra camera có sẵn không
    try:
        camera = cv2.VideoCapture(0)
        # Đặt độ phân giải ở mức vừa phải (640x480)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not camera.isOpened():
            raise Exception("Không thể mở camera")
    except Exception as e:
        print(f"Lỗi khi mở camera: {e}")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg',
                                                                  create_error_frame("Không thể kết nối với camera!"))[
                   1].tobytes() + b'\r\n')
        return

    try:
        frame_count = 0  # Biến đếm frame
        while face_detection_active:  # Tiếp tục nhận diện cho đến khi camera bị dừng
            success, frame = camera.read()
            if not success:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg',
                                                                          create_error_frame(
                                                                              "Không thể đọc frame từ camera!"))[
                           1].tobytes() + b'\r\n')
                break

            frame_count += 1
            # Chỉ xử lý mỗi 2 frame để tăng tốc độ nhận diện nhưng vẫn đủ nhanh
            if frame_count % 2 == 0:
                # Giữ kích thước frame ở mức 0.25 để đảm bảo độ chính xác nhận diện
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                # Tìm tất cả khuôn mặt trong frame (chỉ lấy khuôn mặt đầu tiên)
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations[0:1])  # Chỉ lấy khuôn mặt đầu

                message = "Không nhận diện được khuôn mặt nào!"
                if face_locations and face_encodings:  # Kiểm tra nếu có khuôn mặt
                    (top, right, bottom, left), face_encoding = face_locations[0], face_encodings[0]

                    # Tỉ lệ lại vị trí khuôn mặt do đã resize frame
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # So sánh với các khuôn mặt đã biết
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    student_id = ""

                    # Tìm khoảng cách nhỏ nhất
                    if len(known_face_encodings) > 0:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            student_id = known_face_ids[best_match_index]

                            # Tìm thông tin lớp học
                            students_df = pd.read_csv(STUDENTS_FILE)
                            student_info = students_df[students_df['id'] == student_id]

                            if len(student_info) > 0:
                                student_class = student_info.iloc[0]['class']

                                # Đánh dấu điểm danh
                                attendance_marked = mark_attendance(student_id, name, student_class)

                                if attendance_marked:
                                    message = f"Nhận diện thành công! {name} - Điểm danh thành công!"
                                    # Lưu thông tin nhận diện để hiển thị liên tục
                                    recognized_faces[student_id] = {
                                        'name': name,
                                        'timestamp': time.time()
                                    }
                                else:
                                    message = f"Nhận diện thành công! {name} - Đã điểm danh!"

                    # Vẽ bounding box và thông báo
                    cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)
                    cv2.rectangle(frame, (int(left), int(bottom) - 35), (int(right), int(bottom)), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, message, (int(left) + 6, int(bottom) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            # Mã hóa frame thành JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Gửi frame liên tục
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Lỗi trong quá trình xử lý frame: {e}")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + cv2.imencode('.jpg',
                                                                  create_error_frame(f"Lỗi: {str(e)}"))[
                   1].tobytes() + b'\r\n')
    finally:
        # Giải phóng camera sau khi nhận diện
        if camera is not None:
            camera.release()


def create_error_frame(message):
    """Tạo frame hiển thị thông báo lỗi"""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame


@app.route('/')
def index():
    return render_template('index.html', face_recognition_available=FACE_RECOGNITION_AVAILABLE)


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    message_type = None

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        student_name = request.form.get('student_name', '').strip()
        student_class = request.form.get('student_class', '').strip()
        student_image = request.files.get('student_image')

        if not student_id or not student_name or not student_class or not student_image:
            message = "Vui lòng điền đầy đủ thông tin và chọn ảnh!"
            message_type = "error"
        else:
            # Lưu thông tin sinh viên
            try:
                students_df = pd.read_csv(STUDENTS_FILE)
            except pd.errors.EmptyDataError:
                students_df = pd.DataFrame(columns=['id', 'name', 'class'])
            except Exception as e:
                print(f"Lỗi khi đọc file students.csv: {e}")
                students_df = pd.DataFrame(columns=['id', 'name', 'class'])

            # Kiểm tra ID đã tồn tại chưa
            if student_id in students_df['id'].values:
                message = "Mã sinh viên đã tồn tại!"
                message_type = "error"
            else:
                # Lưu ảnh khuôn mặt
                filename = secure_filename(f"{student_id}.jpg")
                image_path = os.path.join(FACES_PATH, filename)
                student_image.save(image_path)

                # Kiểm tra ảnh có khuôn mặt không
                if not FACE_RECOGNITION_AVAILABLE:
                    # Nếu không có face_recognition, vẫn cho phép đăng ký
                    new_student = pd.DataFrame({
                        'id': [student_id],
                        'name': [student_name],
                        'class': [student_class]
                    })

                    students_df = pd.concat([students_df, new_student], ignore_index=True)
                    students_df.to_csv(STUDENTS_FILE, index=False)

                    message = "Đăng ký sinh viên thành công (không thể kiểm tra khuôn mặt do thư viện face_recognition không hoạt động)!"
                    message_type = "warning"
                else:
                    try:
                        # Kiểm tra ảnh với face_recognition
                        face_image = cv2.imread(image_path)
                        if face_image is None:
                            raise Exception("Không thể đọc file ảnh")
                        face_image_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

                        face_encodings = face_recognition.face_encodings(face_image_rgb)

                        if len(face_encodings) == 0:
                            os.remove(image_path)
                            message = "Không tìm thấy khuôn mặt trong ảnh! Vui lòng thử lại."
                            message_type = "error"
                        else:
                            # Thêm sinh viên vào CSV
                            new_student = pd.DataFrame({
                                'id': [student_id],
                                'name': [student_name],
                                'class': [student_class]
                            })

                            students_df = pd.concat([students_df, new_student], ignore_index=True)
                            students_df.to_csv(STUDENTS_FILE, index=False)

                            # Cập nhật danh sách khuôn mặt đã biết
                            load_known_faces()

                            message = "Đăng ký sinh viên thành công!"
                            message_type = "success"
                    except Exception as e:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                        message = f"Có lỗi xảy ra: {str(e)}"
                        message_type = "error"

    return render_template('register.html', message=message, message_type=message_type,
                           face_recognition_available=FACE_RECOGNITION_AVAILABLE)


@app.route('/attendance')
def attendance():
    today_students = get_today_attendance()
    return render_template('attendance.html', today_students=today_students,
                           face_recognition_available=FACE_RECOGNITION_AVAILABLE)


@app.route('/video_feed')
def video_feed():
    if not FACE_RECOGNITION_AVAILABLE:
        # Trả về một frame tĩnh thông báo lỗi
        error_frame = create_error_frame("Thư viện face_recognition không hoạt động!")
        ret, buffer = cv2.imencode('.jpg', error_frame)
        return Response(
            (b'--frame\r\n'
             b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_camera')
def start_camera():
    global face_detection_active

    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({"status": "error", "message": "Thư viện face_recognition không hoạt động"})

    face_detection_active = True
    return jsonify({"status": "success"})


@app.route('/stop_camera')
def stop_camera():
    global face_detection_active, camera
    face_detection_active = False

    # Giải phóng camera
    if camera is not None:
        camera.release()
        camera = None

    return jsonify({"status": "success"})


@app.route('/process_snapshot', methods=['POST'])
def process_snapshot():
    """Xử lý ảnh chụp từ camera để điểm danh"""
    if request.method == 'POST':
        if not FACE_RECOGNITION_AVAILABLE:
            return jsonify({"status": "error", "message": "Thư viện face_recognition không hoạt động"})

        try:
            data = request.json
            image_data = data.get('image_data')

            if not image_data:
                return jsonify({"status": "error", "message": "Không nhận được dữ liệu ảnh"})

            # Chuyển đổi dữ liệu base64 thành numpy array
            try:
                # Xử lý trường hợp dữ liệu base64 không hợp lệ
                if ',' in image_data:
                    image_data = image_data.split(',')[1]  # Loại bỏ phần header của base64

                # Giải mã base64 an toàn
                try:
                    image_bytes = base64.b64decode(image_data)
                except Exception as e:
                    return jsonify({"status": "error", "message": f"Lỗi giải mã base64: {str(e)}"})

                # Chuyển thành array và giải mã thành ảnh
                image_array = np.frombuffer(image_bytes, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                if image is None:
                    return jsonify({"status": "error", "message": "Không thể giải mã dữ liệu ảnh"})
            except Exception as e:
                return jsonify({"status": "error", "message": f"Lỗi khi xử lý dữ liệu ảnh: {str(e)}"})

            # Nhận diện khuôn mặt trong ảnh
            student_name, student_id, student_class = recognize_face_in_image(image)

            if student_id is None:
                return jsonify({"status": "success", "recognized": False,
                                "message": "Không nhận diện được khuôn mặt nào trong ảnh"})

            # Đánh dấu điểm danh
            attendance_marked = mark_attendance(student_id, student_name, student_class)

            message = "Điểm danh thành công!" if attendance_marked else "Sinh viên đã được điểm danh trước đó"

            # Lưu thông tin nhận diện để hiển thị thông báo
            recognized_faces[student_id] = {
                'name': student_name,
                'timestamp': time.time()
            }

            # Tự động dừng camera sau khi nhận diện
            stop_camera()

            return jsonify({
                "status": "success",
                "recognized": True,
                "student_id": student_id,
                "student_name": student_name,
                "student_class": student_class,
                "attendance_marked": attendance_marked,
                "message": message
            })

        except Exception as e:
            print(f"Lỗi khi xử lý ảnh chụp: {e}")
            return jsonify({"status": "error", "message": f"Lỗi: {str(e)}"})


@app.route('/get_recognition_status')
def get_recognition_status():
    """API để kiểm tra trạng thái nhận diện mới"""
    global recognized_faces
    current_time = time.time()
    new_recognitions = []

    # Trả về danh sách sinh viên đã được nhận diện trong 5 giây qua
    for student_id, info in list(recognized_faces.items()):
        if current_time - info['timestamp'] < 5:  # 5 giây
            new_recognitions.append({
                'id': student_id,
                'name': info['name'].split(' - ')[0]  # Trả về tên không kèm thông báo trạng thái
            })
        else:
            # Xóa nhận diện cũ
            recognized_faces.pop(student_id, None)

    return jsonify({"recognitions": new_recognitions})


@app.route('/get_today_attendance')
def get_today_attendance_api():
    """API để lấy danh sách sinh viên điểm danh trong ngày"""
    today_students = get_today_attendance()
    return jsonify({"status": "success", "students": today_students})


@app.route('/report')
def report():
    # Kiểm tra file tồn tại
    if not os.path.exists(ATTENDANCE_FILE):
        return render_template('report.html',
                              attendance_records=[],
                              all_dates=[],
                              selected_date=None,
                              error="Chưa có dữ liệu điểm danh",
                              face_recognition_available=FACE_RECOGNITION_AVAILABLE)

    # Đọc dữ liệu điểm danh
    try:
        attendance_df = pd.read_csv(ATTENDANCE_FILE)
        if 'date' not in attendance_df.columns:
            return render_template('report.html',
                                  attendance_records=[],
                                  all_dates=[],
                                  selected_date=None,
                                  error="File điểm danh không có cột 'date'",
                                  face_recognition_available=FACE_RECOGNITION_AVAILABLE)
    except pd.errors.EmptyDataError:
        return render_template('report.html',
                              attendance_records=[],
                              all_dates=[],
                              selected_date=None,
                              error="Chưa có dữ liệu điểm danh",
                              face_recognition_available=FACE_RECOGNITION_AVAILABLE)
    except Exception as e:
        print(f"Lỗi khi đọc file attendance.csv: {e}")
        return render_template('report.html',
                              attendance_records=[],
                              all_dates=[],
                              selected_date=None,
                              error=f"Lỗi khi đọc dữ liệu: {str(e)}",
                              face_recognition_available=FACE_RECOGNITION_AVAILABLE)

    # Kiểm tra nếu DataFrame rỗng
    if attendance_df.empty:
        return render_template('report.html',
                              attendance_records=[],
                              all_dates=[],
                              selected_date=None,
                              error="Chưa có dữ liệu điểm danh",
                              face_recognition_available=FACE_RECOGNITION_AVAILABLE)

    # Xử lý cột 'date' để loại bỏ NaN và chuyển thành chuỗi
    attendance_df['date'] = attendance_df['date'].fillna('').astype(str)

    # Lọc theo ngày nếu được chỉ định
    date_filter = request.args.get('date')
    search_query = request.args.get('search', '').strip().lower()

    filtered_df = attendance_df.copy()

    if date_filter and date_filter != 'all':
        filtered_df = filtered_df[filtered_df['date'] == date_filter]

    # Tìm kiếm theo tên hoặc mã sinh viên
    if search_query:
        filtered_df = filtered_df[
            filtered_df['name'].str.lower().str.contains(search_query) |
            filtered_df['id'].str.lower().str.contains(search_query)
        ]

    # Sắp xếp theo ngày và thời gian mới nhất
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by=['date', 'time'], ascending=[False, False])

    # Lấy danh sách ngày để hiển thị trong dropdown
    all_dates = sorted(attendance_df['date'].unique(), reverse=True)

    # Chuyển DataFrame thành danh sách từ điển để dễ hiển thị
    attendance_records = filtered_df.to_dict('records')

    return render_template('report.html',
                          attendance_records=attendance_records,
                          all_dates=all_dates,
                          selected_date=date_filter,
                          search_query=search_query,
                          face_recognition_available=FACE_RECOGNITION_AVAILABLE)


@app.route('/clear_attendance', methods=['POST'])
def clear_attendance():
    """Xóa tất cả dữ liệu điểm danh"""
    try:
        # Sao lưu trước khi xóa
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(DATA_PATH, f'backup_{timestamp}')
        os.makedirs(backup_dir, exist_ok=True)

        # Kiểm tra file tồn tại trước khi sao lưu
        if os.path.exists(ATTENDANCE_FILE):
            shutil.copy2(ATTENDANCE_FILE, os.path.join(backup_dir, 'attendance.csv'))

        # Tạo file mới với header
        pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time']).to_csv(ATTENDANCE_FILE, index=False)
        return jsonify({"status": "success", "message": f"Đã xóa tất cả dữ liệu điểm danh và sao lưu vào {backup_dir}"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi: {str(e)}"})


@app.route('/backup_data', methods=['POST'])
def backup_data():
    """Sao lưu dữ liệu"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(DATA_PATH, f'backup_{timestamp}')
        os.makedirs(backup_dir, exist_ok=True)

        # Sao chép các file CSV
        if os.path.exists(STUDENTS_FILE):
            shutil.copy2(STUDENTS_FILE, os.path.join(backup_dir, 'students.csv'))
        if os.path.exists(ATTENDANCE_FILE):
            shutil.copy2(ATTENDANCE_FILE, os.path.join(backup_dir, 'attendance.csv'))

        # Sao chép thư mục faces
        faces_backup_dir = os.path.join(backup_dir, 'faces')
        os.makedirs(faces_backup_dir, exist_ok=True)

        if os.path.exists(FACES_PATH):
            for file in os.listdir(FACES_PATH):
                if file.endswith('.jpg'):
                    source_path = os.path.join(FACES_PATH, file)
                    if os.path.exists(source_path):
                        shutil.copy2(source_path, os.path.join(faces_backup_dir, file))

        return jsonify({
            "status": "success",
            "message": f"Đã sao lưu dữ liệu thành công vào thư mục {backup_dir}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Lỗi khi sao lưu: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True)