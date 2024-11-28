import cv2
import numpy as np
import open3d as o3d

# Hàm kiểm tra và khởi động camera
def initialize_camera(camera_id):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Không thể mở camera với ID {camera_id}.")
        exit()
    # Đặt độ phân giải cho camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

# Chuyển disparity thành đám mây điểm
def disparity_to_point_cloud(disparity, focal_length, baseline):
    h, w = disparity.shape
    points = []
    for y in range(h):
        for x in range(w):
            d = disparity[y, x]
            if d > 0:  # Chỉ xử lý disparity hợp lệ
                Z = (focal_length * baseline) / (d + 1e-5)
                X = (x - w / 2) * Z / focal_length
                Y = (y - h / 2) * Z / focal_length
                points.append([X, Y, Z])
    return np.array(points)

# Khởi động hai camera
cap_left = initialize_camera(0)  # Camera trái
cap_right = initialize_camera(1)  # Camera phải

# Cấu hình StereoSGBM
stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=64,  # Phải là bội số của 16
    blockSize=9,
    P1=8 * 3 * 9**2,
    P2=32 * 3 * 9**2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32
)

# Thông số camera (giá trị mẫu, thay đổi tùy thuộc vào thiết lập của bạn)
focal_length = 700  # Tiêu cự giả định
baseline = 0.1  # Khoảng cách giữa hai camera (m)

# Vòng lặp chính
while True:
    ret_left, frame_left = cap_left.read()
    ret_right, frame_right = cap_right.read()
    
    if not ret_left or not ret_right:
        print("Không thể đọc từ camera. Kiểm tra kết nối.")
        break

    # Chuyển sang grayscale
    gray_left = cv2.cvtColor(frame_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(frame_right, cv2.COLOR_BGR2GRAY)

    # Tính disparity
    disparity = stereo.compute(gray_left, gray_right).astype(np.float32) / 16.0

    # Lọc và làm mượt disparity
    disparity = cv2.medianBlur(disparity, 5)
    
    # Hiển thị disparity map
    disparity_normalized = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX)
    cv2.imshow("Disparity Map", disparity_normalized.astype(np.uint8))

    # Chuyển disparity thành đám mây điểm
    points_3d = disparity_to_point_cloud(disparity, focal_length, baseline)
    
    # Hiển thị đám mây điểm với Open3D
    if len(points_3d) > 0:
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(points_3d)
        o3d.visualization.draw_geometries([cloud])

    # Thoát nếu nhấn phím 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Giải phóng tài nguyên
cap_left.release()
cap_right.release()
cv2.destroyAllWindows()
