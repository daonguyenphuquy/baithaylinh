import os
import pandas as pd
import numpy as np
import shutil
import cv2
from datetime import datetime

# Kiểm tra thư viện face_recognition
try:
    import my_face_recognition
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

# Đường dẫn lưu dữ liệu
DATA_PATH = 'data'
FACES_PATH = os.path.join(DATA_PATH, 'faces')
STUDENTS_FILE = os.path.join(DATA_PATH, 'students.csv')
ATTENDANCE_FILE = os.path.join(DATA_PATH, 'attendance.csv')


# Hàm thay thế cho face_recognition.load_image_file
def load_image_file(file_path):
    """Hàm thay thế cho face_recognition.load_image_file"""
    img = cv2.imread(file_path)
    if img is None:
        raise Exception(f"Không thể đọc file ảnh: {file_path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# Khởi tạo cấu trúc thư mục và file
def initialize_database():
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(FACES_PATH, exist_ok=True)

    # Khởi tạo DataFrame nếu chưa tồn tại
    if not os.path.exists(STUDENTS_FILE):
        pd.DataFrame(columns=['id', 'name', 'class']).to_csv(STUDENTS_FILE, index=False)

    if not os.path.exists(ATTENDANCE_FILE):
        pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time']).to_csv(ATTENDANCE_FILE, index=False)


# Đọc dữ liệu sinh viên
def get_students():
    if os.path.exists(STUDENTS_FILE):
        try:
            return pd.read_csv(STUDENTS_FILE)
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['id', 'name', 'class'])
        except Exception as e:
            print(f"Lỗi khi đọc file students.csv: {e}")
            return pd.DataFrame(columns=['id', 'name', 'class'])
    return pd.DataFrame(columns=['id', 'name', 'class'])


# Thêm sinh viên mới
def add_student(student_id, student_name, student_class, face_image_path):
    students_df = get_students()

    # Kiểm tra ID đã tồn tại chưa
    if student_id in students_df['id'].values:
        return False, "Mã sinh viên đã tồn tại!"

    try:
        # Kiểm tra ảnh có khuôn mặt không (nếu có face_recognition)
        if FACE_RECOGNITION_AVAILABLE:
            try:
                face_image = load_image_file(face_image_path)
                face_encodings = face_recognition.face_encodings(face_image)

                if len(face_encodings) == 0:
                    return False, "Không tìm thấy khuôn mặt trong ảnh!"
            except Exception as e:
                return False, f"Lỗi khi xử lý ảnh: {str(e)}"
        else:
            # Nếu không có face_recognition, vẫn tiếp tục nhưng cảnh báo
            print("CẢNH BÁO: Không thể kiểm tra khuôn mặt do thư viện face_recognition không hoạt động!")

        # Thêm sinh viên vào CSV
        new_student = pd.DataFrame({
            'id': [student_id],
            'name': [student_name],
            'class': [student_class]
        })

        students_df = pd.concat([students_df, new_student], ignore_index=True)
        students_df.to_csv(STUDENTS_FILE, index=False)

        # Di chuyển ảnh vào thư mục faces
        destination_path = os.path.join(FACES_PATH, f"{student_id}.jpg")
        shutil.copy2(face_image_path, destination_path)

        return True, "Đăng ký sinh viên thành công!"
    except Exception as e:
        return False, f"Lỗi: {str(e)}"


# Đọc dữ liệu điểm danh
def get_attendance(date=None, search_query=None):
    if os.path.exists(ATTENDANCE_FILE):
        try:
            attendance_df = pd.read_csv(ATTENDANCE_FILE)

            # Lọc theo ngày nếu có
            if date and date != 'all':
                attendance_df = attendance_df[attendance_df['date'] == date]

            # Tìm kiếm nếu có
            if search_query:
                search_query = search_query.lower()
                attendance_df = attendance_df[
                    attendance_df['name'].str.lower().str.contains(search_query) |
                    attendance_df['id'].str.lower().str.contains(search_query)
                    ]

            # Sắp xếp theo ngày và thời gian mới nhất
            if not attendance_df.empty:
                attendance_df = attendance_df.sort_values(by=['date', 'time'], ascending=[False, False])

            return attendance_df
        except pd.errors.EmptyDataError:
            return pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time'])
        except Exception as e:
            print(f"Lỗi khi đọc file attendance.csv: {e}")
            return pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time'])
    return pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time'])


# Ghi nhận điểm danh
def mark_attendance(student_id, student_name, student_class, date, time):
    try:
        attendance_df = get_attendance()

        # Kiểm tra xem sinh viên đã điểm danh trong ngày chưa
        today_attendance = attendance_df[(attendance_df['id'] == student_id) &
                                         (attendance_df['date'] == date)]

        if len(today_attendance) == 0:
            new_attendance = pd.DataFrame({
                'id': [student_id],
                'name': [student_name],
                'class': [student_class],
                'date': [date],
                'time': [time]
            })

            attendance_df = pd.concat([attendance_df, new_attendance], ignore_index=True)
            attendance_df.to_csv(ATTENDANCE_FILE, index=False)
            return True

        return False
    except Exception as e:
        print(f"Lỗi khi đánh dấu điểm danh: {e}")
        return False


# Lấy tất cả các ngày đã điểm danh
def get_attendance_dates():
    attendance_df = get_attendance()
    if attendance_df.empty:
        return []
    return sorted(attendance_df['date'].unique(), reverse=True)


# Tải danh sách khuôn mặt đã biết
def load_known_faces():
    if not FACE_RECOGNITION_AVAILABLE:
        print("Không thể tải khuôn mặt do thư viện face_recognition không hoạt động")
        return [], [], []

    students_df = get_students()
    known_face_encodings = []
    known_face_names = []
    known_face_ids = []

    for index, row in students_df.iterrows():
        student_id = row['id']
        student_name = row['name']
        face_image_path = os.path.join(FACES_PATH, f"{student_id}.jpg")

        if os.path.exists(face_image_path):
            try:
                face_image = load_image_file(face_image_path)
                face_encoding = face_recognition.face_encodings(face_image)

                if len(face_encoding) > 0:
                    known_face_encodings.append(face_encoding[0])
                    known_face_names.append(student_name)
                    known_face_ids.append(student_id)
            except Exception as e:
                print(f"Lỗi khi tải ảnh {face_image_path}: {e}")

    return known_face_encodings, known_face_names, known_face_ids


# Xóa dữ liệu điểm danh
def clear_attendance_data():
    try:
        # Tạo bản sao lưu trước khi xóa
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(DATA_PATH, f'attendance_backup_{timestamp}.csv')
        if os.path.exists(ATTENDANCE_FILE):
            shutil.copy2(ATTENDANCE_FILE, backup_file)

        # Tạo file mới với header
        pd.DataFrame(columns=['id', 'name', 'class', 'date', 'time']).to_csv(ATTENDANCE_FILE, index=False)
        return True, f"Đã xóa dữ liệu và tạo bản sao lưu {backup_file}"
    except Exception as e:
        return False, f"Lỗi khi xóa dữ liệu: {str(e)}"


# Sao lưu toàn bộ dữ liệu
def backup_all_data():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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

        return True, f"Đã sao lưu dữ liệu thành công vào thư mục {backup_dir}"
    except Exception as e:
        return False, f"Lỗi khi sao lưu: {str(e)}"