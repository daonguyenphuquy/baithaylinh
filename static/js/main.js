// Chức năng chung cho toàn bộ ứng dụng
document.addEventListener('DOMContentLoaded', function() {
    // Hiệu ứng active cho menu
    const currentPage = window.location.pathname;
    const navLinks = document.querySelectorAll('nav ul li a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        }
    });

    // Hiệu ứng nút
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mousedown', function() {
            this.style.transform = 'scale(0.98)';
        });

        button.addEventListener('mouseup', function() {
            this.style.transform = 'scale(1)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
});

// Chức năng cho trang đăng ký
function initRegisterPage() {
    if (!document.getElementById('student_image') && !document.getElementById('capture-container')) return;

    // Nếu có phần chụp ảnh trực tiếp
    if (document.getElementById('capture-container')) {
        const video = document.getElementById('capture-video');
        const captureButton = document.getElementById('capture-button');
        const canvas = document.getElementById('capture-canvas');
        const context = canvas.getContext('2d');
        const previewImg = document.getElementById('capture-preview');
        const fileInput = document.getElementById('student_image');
        const usePhotoButton = document.getElementById('use-photo');
        let stream = null;

        // Khởi động camera
        document.getElementById('start-capture').addEventListener('click', async function() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
                document.getElementById('capture-controls').style.display = 'block';
                this.style.display = 'none';
                captureButton.style.display = 'block';
            } catch (err) {
                showAlert('Không thể kết nối với camera. Vui lòng kiểm tra quyền truy cập camera.', 'error');
                console.error('Lỗi kết nối camera:', err);
            }
        });

        // Chụp ảnh
        captureButton.addEventListener('click', function() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Hiển thị ảnh đã chụp
            const imageDataUrl = canvas.toDataURL('image/jpeg');
            previewImg.src = imageDataUrl;
            previewImg.style.display = 'block';

            // Hiển thị nút sử dụng ảnh
            usePhotoButton.style.display = 'block';
            document.getElementById('retake-photo').style.display = 'block';
            captureButton.style.display = 'none';
        });

        // Chụp lại ảnh
        document.getElementById('retake-photo').addEventListener('click', function() {
            previewImg.style.display = 'none';
            usePhotoButton.style.display = 'none';
            this.style.display = 'none';
            captureButton.style.display = 'block';
        });

        // Sử dụng ảnh đã chụp
        usePhotoButton.addEventListener('click', function() {
            // Chuyển dữ liệu ảnh sang file
            canvas.toBlob(function(blob) {
                const file = new File([blob], "captured_image.jpg", { type: "image/jpeg" });

                // Tạo FileList object để gán cho input file
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;

                // Hiển thị tên file
                document.getElementById('file-name').textContent = 'captured_image.jpg';

                // Hiển thị ảnh trong phần xem trước chính
                const mainPreview = document.getElementById('image-preview');
                mainPreview.src = previewImg.src;
                mainPreview.style.display = 'block';

                // Dừng camera và ẩn phần chụp ảnh
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                document.getElementById('capture-container').style.display = 'none';
                document.getElementById('toggle-capture').textContent = 'Sử dụng camera';
                document.getElementById('file-input-container').style.display = 'flex';

                showAlert('Đã chụp ảnh thành công!', 'success');
            }, 'image/jpeg', 0.9);
        });

        // Chuyển đổi giữa tải file và chụp ảnh
        document.getElementById('toggle-capture').addEventListener('click', function() {
            const captureContainer = document.getElementById('capture-container');
            const fileInputContainer = document.getElementById('file-input-container');

            if (captureContainer.style.display === 'none') {
                captureContainer.style.display = 'block';
                fileInputContainer.style.display = 'none';
                this.textContent = 'Tải file ảnh';
                document.getElementById('start-capture').style.display = 'block';
                document.getElementById('capture-controls').style.display = 'none';
                document.getElementById('capture-preview').style.display = 'none';
                document.getElementById('use-photo').style.display = 'none';
                document.getElementById('retake-photo').style.display = 'none';
            } else {
                captureContainer.style.display = 'none';
                fileInputContainer.style.display = 'flex';
                this.textContent = 'Sử dụng camera';

                // Dừng camera nếu đang chạy
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
            }
        });

        // Dừng camera khi rời khỏi trang
        window.addEventListener('beforeunload', function() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
    }

    // Hiển thị tên file khi chọn ảnh
    document.getElementById('student_image').addEventListener('change', function() {
        var fileName = this.files[0] ? this.files[0].name : 'Chưa có ảnh nào được chọn';
        document.getElementById('file-name').textContent = fileName;

        // Hiển thị xem trước ảnh
        var preview = document.getElementById('image-preview');
        if (this.files && this.files[0]) {
            var reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(this.files[0]);
        } else {
            preview.style.display = 'none';
        }
    });

    // Reset form khi nhấn nút làm mới
    document.querySelector('button[type="reset"]').addEventListener('click', function() {
        document.getElementById('file-name').textContent = 'Chưa có ảnh nào được chọn';
        document.getElementById('image-preview').style.display = 'none';

        // Xóa thông báo
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.style.display = 'none';
        }
    });

    // Xác thực form trước khi submit
    document.querySelector('.register-form').addEventListener('submit', function(e) {
        const studentId = document.getElementById('student_id').value.trim();
        const studentName = document.getElementById('student_name').value.trim();
        const studentClass = document.getElementById('student_class').value.trim();
        const studentImage = document.getElementById('student_image').files[0];

        if (!studentId || !studentName || !studentClass || !studentImage) {
            e.preventDefault();
            showAlert('Vui lòng điền đầy đủ thông tin và chọn ảnh!', 'error');
            return;
        }

        // Kiểm tra định dạng ID sinh viên (chỉ cho phép chữ và số)
        if (!/^[a-zA-Z0-9]+$/.test(studentId)) {
            e.preventDefault();
            showAlert('Mã sinh viên chỉ được chứa chữ cái và số!', 'error');
            return;
        }

        // Kiểm tra kích thước ảnh
        if (studentImage.size > 5 * 1024 * 1024) { // 5MB
            e.preventDefault();
            showAlert('Kích thước ảnh không được vượt quá 5MB!', 'error');
            return;
        }

        // Kiểm tra định dạng ảnh
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!validTypes.includes(studentImage.type)) {
            e.preventDefault();
            showAlert('Chỉ chấp nhận file ảnh định dạng JPEG, JPG hoặc PNG!', 'error');
            return;
        }

        // Thêm hiệu ứng loading cho nút submit
        const submitBtn = document.querySelector('button[type="submit"]');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
        submitBtn.disabled = true;
    });

    // Hiển thị thông báo
    function showAlert(message, type) {
        // Xóa thông báo cũ nếu có
        const oldAlert = document.querySelector('.alert');
        if (oldAlert) {
            oldAlert.remove();
        }

        // Tạo thông báo mới
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = message;

        // Thêm nút đóng
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'alert-close';
        closeBtn.addEventListener('click', function() {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        });

        alert.appendChild(closeBtn);

        // Thêm vào trang
        const formContainer = document.querySelector('.form-container');
        formContainer.insertBefore(alert, formContainer.firstChild);

        // Tự động ẩn sau 5 giây
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);
    }
}

// Chức năng cho trang điểm danh
function initAttendancePage() {
    if (!document.getElementById('start-camera')) return;

    // Cập nhật thời gian hiện tại
    function updateTime() {
        const now = new Date();

        // Thời gian
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        document.getElementById('current-time').textContent = `${hours}:${minutes}:${seconds}`;

        // Ngày tháng
        const day = String(now.getDate()).padStart(2, '0');
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const year = now.getFullYear();
        document.getElementById('current-date').textContent = `${day}/${month}/${year}`;
    }

    // Cập nhật thời gian mỗi giây
    setInterval(updateTime, 1000);
    updateTime();

    // Xử lý bật/tắt camera
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const takeSnapshotBtn = document.getElementById('take-snapshot');
    const videoElement = document.getElementById('video');
    const cameraPlaceholder = document.getElementById('camera-placeholder');
    const attendanceMessage = document.getElementById('attendance-message');

    // Chức năng chụp ảnh điểm danh
    if (takeSnapshotBtn) {
        takeSnapshotBtn.addEventListener('click', function() {
            // Lấy ảnh từ video
            const canvas = document.createElement('canvas');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

            // Chuyển ảnh thành dữ liệu base64
            const imageData = canvas.toDataURL('image/jpeg');

            // Hiển thị hiệu ứng đang xử lý
            takeSnapshotBtn.disabled = true;
            takeSnapshotBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';

            // Gửi ảnh lên server để xử lý điểm danh
            fetch('/process_snapshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image_data: imageData })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (data.recognized) {
                        showToast(`Đã nhận diện và điểm danh: ${data.student_name}`, 'success');
                    } else {
                        showToast('Không nhận diện được khuôn mặt nào trong ảnh', 'warning');
                    }
                } else {
                    showToast(data.message || 'Có lỗi xảy ra khi xử lý ảnh', 'error');
                }
                takeSnapshotBtn.disabled = false;
                takeSnapshotBtn.innerHTML = '<i class="fas fa-camera"></i> Chụp ảnh điểm danh';
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Có lỗi xảy ra khi gửi ảnh lên máy chủ', 'error');
                takeSnapshotBtn.disabled = false;
                takeSnapshotBtn.innerHTML = '<i class="fas fa-camera"></i> Chụp ảnh điểm danh';
            });
        });
    }

    startCameraBtn.addEventListener('click', function() {
        // Thêm hiệu ứng loading cho nút
        startCameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang khởi động...';
        startCameraBtn.disabled = true;

        fetch('/start_camera')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    videoElement.style.display = 'block';
                    cameraPlaceholder.style.display = 'none';
                    startCameraBtn.disabled = true;
                    startCameraBtn.innerHTML = '<i class="fas fa-video"></i> Bắt đầu camera';
                    stopCameraBtn.disabled = false;
                    takeSnapshotBtn.disabled = false;
                    attendanceMessage.textContent = 'Đang nhận diện khuôn mặt...';

                    // Thêm hiệu ứng loading
                    attendanceMessage.classList.add('processing');

                    // Bắt đầu kiểm tra trạng thái nhận diện
                    startRecognitionCheck();
                } else {
                    showToast('Không thể kết nối với camera', 'error');
                    startCameraBtn.innerHTML = '<i class="fas fa-video"></i> Bắt đầu camera';
                    startCameraBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Không thể kết nối với camera. Vui lòng thử lại!', 'error');
                startCameraBtn.innerHTML = '<i class="fas fa-video"></i> Bắt đầu camera';
                startCameraBtn.disabled = false;
            });
    });

    stopCameraBtn.addEventListener('click', function() {
        stopCameraBtn.disabled = true;
        stopCameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang dừng...';
        takeSnapshotBtn.disabled = true;

        fetch('/stop_camera')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    videoElement.style.display = 'none';
                    cameraPlaceholder.style.display = 'flex';
                    startCameraBtn.disabled = false;
                    stopCameraBtn.disabled = true;
                    stopCameraBtn.innerHTML = '<i class="fas fa-stop"></i> Dừng camera';
                    takeSnapshotBtn.disabled = true;
                    attendanceMessage.textContent = 'Chờ nhận diện khuôn mặt...';

                    // Xóa hiệu ứng loading
                    attendanceMessage.classList.remove('processing');

                    // Dừng kiểm tra nhận diện
                    stopRecognitionCheck();
                } else {
                    showToast('Không thể dừng camera', 'error');
                    stopCameraBtn.innerHTML = '<i class="fas fa-stop"></i> Dừng camera';
                    stopCameraBtn.disabled = false;
                    takeSnapshotBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Có lỗi xảy ra khi dừng camera', 'error');
                stopCameraBtn.innerHTML = '<i class="fas fa-stop"></i> Dừng camera';
                stopCameraBtn.disabled = false;
                takeSnapshotBtn.disabled = false;
            });
    });

    // Kiểm tra nhận diện mới
    let recognitionCheckInterval;

    function startRecognitionCheck() {
        // Kiểm tra mỗi 2 giây
        recognitionCheckInterval = setInterval(checkForNewRecognitions, 2000);
    }

    function stopRecognitionCheck() {
        clearInterval(recognitionCheckInterval);
    }

    function checkForNewRecognitions() {
        fetch('/get_recognition_status')
            .then(response => response.json())
            .then(data => {
                if (data.recognitions && data.recognitions.length > 0) {
                    // Hiển thị thông báo cho mỗi sinh viên được nhận diện
                    data.recognitions.forEach(student => {
                        // Kiểm tra xem đã hiển thị thông báo cho sinh viên này chưa
                        if (!document.querySelector(`.success-overlay[data-student-id="${student.id}"]`)) {
                            showSuccessRecognition(student.name);
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error checking recognition status:', error);
            });
    }

    // Hiển thị danh sách sinh viên đã điểm danh hôm nay
    function loadTodayAttendance() {
        const attendanceList = document.getElementById('today-attendance-list');
        if (attendanceList) {
            fetch('/get_today_attendance')
                .then(response => response.json())
                .then(data => {
                    // Xóa danh sách hiện tại
                    attendanceList.innerHTML = '';

                    if (data.students && data.students.length > 0) {
                        // Hiển thị số lượng sinh viên đã điểm danh
                        document.getElementById('attendance-count').textContent = data.students.length;

                        // Tạo danh sách mới
                        data.students.forEach(student => {
                            const listItem = document.createElement('li');
                            listItem.innerHTML = `
                                <strong>${student.name}</strong> - ${student.id}
                                <span class="attendance-time">${student.time}</span>
                            `;
                            attendanceList.appendChild(listItem);
                        });
                    } else {
                        document.getElementById('attendance-count').textContent = '0';
                        const emptyItem = document.createElement('li');
                        emptyItem.className = 'empty-list';
                        emptyItem.textContent = 'Chưa có sinh viên nào điểm danh hôm nay';
                        attendanceList.appendChild(emptyItem);
                    }
                })
                .catch(error => {
                    console.error('Error loading today attendance:', error);
                });
        }
    }

    // Tải danh sách điểm danh khi trang được tải và mỗi 30 giây
    loadTodayAttendance();
    setInterval(loadTodayAttendance, 30000);

    // Hiệu ứng nhận diện khuôn mặt thành công
    function showSuccessRecognition(studentName) {
        const successOverlay = document.createElement('div');
        successOverlay.className = 'success-overlay';
        successOverlay.setAttribute('data-student-id', studentName);
        successOverlay.innerHTML = `
            <div class="success-message">
                <i class="fas fa-check-circle"></i>
                <h3>Nhận diện thành công!</h3>
                <p>${studentName}</p>
            </div>
        `;

        document.body.appendChild(successOverlay);

        // Xóa overlay sau 3 giây
        setTimeout(() => {
            successOverlay.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(successOverlay);
            }, 500);
        }, 3000);

        // Cập nhật danh sách điểm danh
        loadTodayAttendance();
    }

    // Hiển thị thông báo toast
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Hiển thị toast
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 100);

        // Ẩn toast sau 3 giây
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 500);
        }, 3000);
    }

    // Sự kiện unload để đảm bảo camera được giải phóng
    window.addEventListener('beforeunload', function() {
        if (!stopCameraBtn.disabled) {
            fetch('/stop_camera').catch(err => console.log('Error stopping camera:', err));
        }
    });

    // Hỗ trợ phát hiện lỗi camera
    videoElement.addEventListener('error', function() {
        showToast('Có lỗi với camera', 'error');
        stopCameraBtn.click();
    });
}

// Chức năng cho trang báo cáo
function initReportPage() {
    if (!document.getElementById('date-filter')) return;

    // Tự động gửi form khi thay đổi bộ lọc ngày
    document.getElementById('date-filter').addEventListener('change', function() {
        document.querySelector('.filter-form').submit();
    });

    // Tìm kiếm sinh viên
    const searchInput = document.getElementById('student-search');
    if (searchInput) {
        // Tìm kiếm ngay khi nhập
        searchInput.addEventListener('input', function() {
            // Chỉ tìm kiếm khi người dùng dừng nhập trong 500ms
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                if (this.value.trim() === '') {
                    // Nếu ô tìm kiếm trống, hiển thị tất cả
                    document.querySelectorAll('.report-table tbody tr').forEach(row => {
                        row.style.display = '';
                    });
                } else {
                    const searchValue = this.value.toLowerCase();
                    filterTable(searchValue);
                }
            }, 500);
        });

        // Form tìm kiếm
        document.getElementById('search-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const searchValue = searchInput.value.trim().toLowerCase();
            if (searchValue) {
                filterTable(searchValue);
            }
        });

        // Lọc bảng theo từ khóa
        function filterTable(keyword) {
            const rows = document.querySelectorAll('.report-table tbody tr');
            let hasResults = false;

            rows.forEach(row => {
                if (row.querySelector('.no-data')) return;

                const studentName = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
                const studentId = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                const studentClass = row.querySelector('td:nth-child(4)').textContent.toLowerCase();

                if (studentName.includes(keyword) || studentId.includes(keyword) || studentClass.includes(keyword)) {
                    row.style.display = '';
                    hasResults = true;
                } else {
                    row.style.display = 'none';
                }
            });

            // Hiển thị thông báo nếu không có kết quả
            const noResultsRow = document.getElementById('no-results-row');
            if (!hasResults) {
                if (!noResultsRow) {
                    const tbody = document.querySelector('.report-table tbody');
                    const newRow = document.createElement('tr');
                    newRow.id = 'no-results-row';
                    newRow.innerHTML = '<td colspan="7" class="no-data">Không tìm thấy kết quả phù hợp!</td>';
                    tbody.appendChild(newRow);
                } else {
                    noResultsRow.style.display = '';
                }
            } else if (noResultsRow) {
                noResultsRow.style.display = 'none';
            }
        }
    }

    // Xuất CSV
    document.getElementById('export-csv').addEventListener('click', function() {
        // Kiểm tra xem có dữ liệu để xuất không
        const rows = document.querySelectorAll('.report-table tbody tr');
        let hasData = false;

        rows.forEach(row => {
            if (!row.querySelector('.no-data') && row.style.display !== 'none') {
                hasData = true;
            }
        });

        if (!hasData) {
            showToast('Không có dữ liệu để xuất!', 'error');
            return;
        }

        // Tạo nội dung CSV
        let csvContent = "STT,Mã SV,Họ và tên,Lớp,Ngày,Thời gian,Trạng thái\n";

        rows.forEach((row, index) => {
            if (!row.querySelector('.no-data') && row.style.display !== 'none') {
                const cells = row.querySelectorAll('td');
                const rowData = Array.from(cells).map(cell => {
                    // Lấy văn bản từ cell, cho phép xử lý trạng thái
                    // Thay thế dấu phẩy bằng dấu chấm phẩy để tránh lỗi định dạng CSV
                    return `"${cell.textContent.trim().replace(/"/g, '""')}"`;
                });
                csvContent += rowData.join(',') + "\n";
            }
        });

        // Tạo Blob với mã hóa UTF-8 BOM để Excel nhận dạng đúng tiếng Việt
        const BOM = new Uint8Array([0xEF, 0xBB, 0xBF]);
        const blob = new Blob([BOM, csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);

        // Tạo tên file với ngày hiện tại
        const now = new Date();
        const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        link.setAttribute('download', `bao-cao-diem-danh-${dateStr}.csv`);

        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Hiển thị thông báo
        showToast('Xuất file CSV thành công!');
    });

    // In báo cáo
    document.getElementById('print-report').addEventListener('click', function() {
        // Kiểm tra xem có dữ liệu để in không
        const rows = document.querySelectorAll('.report-table tbody tr');
        let hasData = false;

        rows.forEach(row => {
            if (!row.querySelector('.no-data') && row.style.display !== 'none') {
                hasData = true;
            }
        });

        if (!hasData) {
            showToast('Không có dữ liệu để in!', 'error');
            return;
        }

        // Ẩn các phần không cần in
        const originalPrint = document.getElementById('print-styles');
        if (!originalPrint) {
            const style = document.createElement('style');
            style.id = 'print-styles';
            style.innerHTML = `
                @media print {
                    header, nav, footer, .report-controls, .no-print {
                        display: none !important;
                    }
                    body, main {
                        margin: 0;
                        padding: 0;
                        background: white;
                        box-shadow: none;
                    }
                    main h2 {
                        margin-top: 20px;
                    }
                    .report-table-container {
                        box-shadow: none;
                    }
                    .report-table {
                        width: 100%;
                    }
                    /* Hiển thị các hàng bị ẩn bởi tìm kiếm */
                    .report-table tbody tr {
                        display: table-row !important;
                    }
                    /* Ẩn hàng 'không tìm thấy kết quả' khi in */
                    #no-results-row {
                        display: none !important;
                    }
                    /* Chỉ in các hàng đang hiển thị (không bị ẩn bởi tìm kiếm) */
                    .report-table tbody tr[style*="display: none"] {
                        display: none !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        window.print();
    });

    // Xóa dữ liệu điểm danh
    const clearDataBtn = document.getElementById('clear-data');
    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', function() {
            if (confirm('Bạn có chắc chắn muốn xóa tất cả dữ liệu điểm danh? Hành động này không thể hoàn tác!')) {
                fetch('/clear_attendance', {
                    method: 'POST',
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast(data.message);
                        // Tải lại trang sau 1 giây
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        showToast(data.message, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Có lỗi xảy ra khi xóa dữ liệu', 'error');
                });
            }
        });
    }

    // Sao lưu dữ liệu
    const backupDataBtn = document.getElementById('backup-data');
    if (backupDataBtn) {
        backupDataBtn.addEventListener('click', function() {
            backupDataBtn.disabled = true;
            backupDataBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang sao lưu...';

            fetch('/backup_data', {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast(data.message);
                } else {
                    showToast(data.message, 'error');
                }
                backupDataBtn.disabled = false;
                backupDataBtn.innerHTML = '<i class="fas fa-download"></i> Sao lưu dữ liệu';
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Có lỗi xảy ra khi sao lưu dữ liệu', 'error');
                backupDataBtn.disabled = false;
                backupDataBtn.innerHTML = '<i class="fas fa-download"></i> Sao lưu dữ liệu';
            });
        });
    }

    // Hiển thị thông báo
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        document.body.appendChild(toast);

        // Hiển thị toast
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 100);

        // Ẩn toast sau 3 giây
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 500);
        }, 3000);
    }
}

// Khởi tạo chức năng của từng trang
document.addEventListener('DOMContentLoaded', function() {
    initRegisterPage();
    initAttendancePage();
    initReportPage();

    // Thêm hiệu ứng cho các thông báo
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Tự động ẩn thông báo sau 5 giây
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 5000);

        // Thêm nút đóng thông báo nếu chưa có
        if (!alert.querySelector('.alert-close')) {
            const closeBtn = document.createElement('span');
            closeBtn.innerHTML = '&times;';
            closeBtn.className = 'alert-close';
            closeBtn.addEventListener('click', function() {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 500);
            });

            alert.appendChild(closeBtn);
        }
    });
});

// Thêm hiệu ứng CSS cho hiệu ứng nhận diện thành công và toast
const style = document.createElement('style');
style.textContent = `
.success-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    opacity: 1;
    transition: opacity 0.5s ease;
}

.success-message {
    background-color: white;
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    max-width: 80%;
    animation: scale-up 0.4s ease;
}

@keyframes scale-up {
    0% { transform: scale(0.8); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}

.success-message i {
    font-size: 4rem;
    color: #4CAF50;
    margin-bottom: 15px;
    animation: bounce 1s ease infinite;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.success-message h3 {
    margin-bottom: 10px;
    color: #333;
}

.success-message p {
    color: #666;
}

.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background-color: #333;
    color: white;
    padding: 15px 25px;
    border-radius: 5px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast.success {
    background-color: #4CAF50;
}

.toast.error {
    background-color: #f44336;
}

.toast.info {
    background-color: #2196F3;
}

.toast.warning {
    background-color: #ff9800;
}

.processing {
    position: relative;
}

.processing::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: loading 1.5s infinite;
}

@keyframes loading {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.alert-close {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 1.2rem;
    cursor: pointer;
    color: inherit;
    opacity: 0.7;
}

.alert-close:hover {
    opacity: 1;
}

.alert {
    position: relative;
    transition: opacity 0.5s ease;
}

/* Cải thiện bảng báo cáo */
.report-table {
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 8px;
    overflow: hidden;
}

.report-table th:first-child {
    border-top-left-radius: 8px;
}

.report-table th:last-child {
    border-top-right-radius: 8px;
}

.report-table tbody tr:last-child td:first-child {
    border-bottom-left-radius: 8px;
}

.report-table tbody tr:last-child td:last-child {
    border-bottom-right-radius: 8px;
}

.filter-container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    margin-bottom: 20px;
}

#search-form {
    display: flex;
    align-items: center;
}

#student-search {
    padding: 10px 15px;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
    margin-right: 10px;
    min-width: 250px;
}

#student-search:focus {
    border-color: #6a11cb;
    outline: none;
    box-shadow: 0 0 0 2px rgba(106, 17, 203, 0.2);
}

.buttons-container {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

/* Phong cách cho phần điểm danh hôm nay */
.attendance-list-container {
    background-color: #f5f7fb;
    border-radius: 10px;
    padding: 15px;
    margin-top: 20px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.attendance-list-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.attendance-list-header h3 {
    margin: 0;
    color: #333;
}

.attendance-count {
    background-color: #6a11cb;
    color: white;
    padding: 5px 10px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: bold;
}

#today-attendance-list {
    list-style-type: none;
    padding: 0;
    margin: 0;
    max-height: 300px;
    overflow-y: auto;
}

#today-attendance-list li {
    padding: 10px 15px;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

#today-attendance-list li:last-child {
    border-bottom: none;
}

.attendance-time {
    color: #666;
    font-size: 0.9rem;
}

.empty-list {
    text-align: center;
    color: #666;
    font-style: italic;
    padding: 20px 0 !important;
}

/* Phong cách cho chức năng chụp ảnh */
.capture-container {
    margin-bottom: 20px;
    background-color: #f5f7fb;
    border-radius: 10px;
    padding: 15px;
    display: none;
}

#capture-video {
    width: 100%;
    border-radius: 8px;
    margin-bottom: 15px;
}

#capture-preview {
    width: 100%;
    border-radius: 8px;
    margin-bottom: 15px;
    display: none;
}

#capture-controls {
    display: none;
}

.capture-buttons {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-top: 15px;
}

@media (max-width: 768px) {
    .filter-container {
        flex-direction: column;
        align-items: stretch;
    }
    
    #search-form {
        width: 100%;
    }
    
    #student-search {
        flex: 1;
    }
    
    .buttons-container {
        justify-content: center;
    }
    
    .capture-buttons {
        flex-direction: column;
    }
}
`;

document.head.appendChild(style);