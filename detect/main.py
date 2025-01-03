import cv2  # 导入 OpenCV 库
import time  # 导入时间库
from detector import ArmorDetector  # 从 detector 导入 Detector 类
from transfer import Trans
from armor_tracker_node import ArmorTracker
from loguru import logger
import time
import board,time
from digitalio import DigitalInOut, Direction

#构建LED对象和初始化
led = DigitalInOut(board.LED) #定义引脚编号
led.direction = Direction.OUTPUT  #IO为输出

for i in range(5):
    led.value = 1 #输出高电平，点亮板载LED蓝灯
    time.sleep(0.3)
    led.value = 0 #输出低电平，熄灭板载LED蓝灯
    time.sleep(0.3)
led.value = 1 #输出高电平，点亮板载LED蓝灯

def find_first_camera():
    # 假设最多有10个摄像头设备
    camera_count = 10

    for i in range(camera_count):
        # 尝试打开摄像头
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            return cap  # 返回找到的第一个摄像头对象


class Cam():
    def __init__(self, cam_params):    
        self.width = cam_params["width"]  # 你想要的宽度
        self.height = cam_params["height"]   # 你想要的高度
        self.fps = cam_params["fps"]  # 你想要的帧率

    def detect(self, detector, tracker, transfer):
        tracker.pic_width = self.width
        video_stream = find_first_camera()  # 打开视频流
                # 设置分辨率
        video_stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        video_stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        video_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        video_stream.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        video_stream.set(cv2.CAP_PROP_EXPOSURE, 50)      
        # 设置帧率
        video_stream.set(cv2.CAP_PROP_FPS, self.fps)
        w = video_stream.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = video_stream.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = video_stream.get(cv2.CAP_PROP_FPS)

        if not video_stream.isOpened():  # 检查视频流是否成功打开
            print("错误: 无法打开视频流。")
        while True:  # 持续读取视频帧
            start_time = time.time()  # 记录帧处理开始时间
            ret, frame = video_stream.read()  # 读取视频帧
            if not ret:  # 如果未成功读取帧
                print("错误: 无法读取帧")
                break  # 退出循环
            #logger.info(f"cam: {w} x {h} @ {fps}") 
            info = detector.detect_armor(frame)  # 使用 detector 进行检测
            # bin, img = detector.display()
            # cv2.imshow("bin",bin)
            # cv2.imshow("img",img)
            target_yaw, target_pitch = tracker.track(info)
            transfer.send(target_yaw, target_pitch)
            # end_time = time.time()  # 记录帧处理结束时间
            # detection_time = (end_time - start_time) * 1000  # 转换为毫秒
            #logger.debug(f"检测延迟: {int(detection_time)} 毫秒")  # 输出检测延迟
            if cv2.waitKey(1) & 0xFF == ord("q"):  # 检测按键
                break  # 退出循环
        video_stream.release()  # 释放视频流
        cv2.destroyAllWindows()  # 关闭所有窗口
        transfer.close()
        logger.info("off")
    
detect_color =  0  # 颜色参数 0: 识别红色装甲板, 1: 识别蓝色装甲板, 2: 识别全部装甲板
# 图像参数字典
binary_val = 92   
light_params = {
    "light_area_min": 5,  # 最小灯条面积
    "light_angle_min": -45,  # 最小灯条角度
    "light_angle_max": 45,  # 最大灯条角度
    "light_angle_tol": 7,  # 灯条角度容差
    "vertical_discretization": 0.615,  # 垂直离散
    "height_tol": 15,  # 高度容差
    "cy_tol":8,  # 中心点的y轴容差
    "height_multiplier": 4.8
}
# 颜色参数字典
color_params = {
    "armor_color": {1: (255, 255, 0), 0: (128, 0, 128)},  # 装甲板颜色映射
    "armor_id": {1: 1, 0: 7},  # 装甲板 ID 映射
    "light_color": {1: (200, 71, 90), 0: (0, 100, 255)},  # 灯条颜色映射
    "light_dot": {1: (0, 0, 255), 0: (255, 0, 0)}  # 灯条中心点颜色映射
}
cam_params = { 
        "width": 640,  # 你想要的宽度
        "height": 480,   # 你想要的高度
        "fps": 30,  # 你想要的帧率
}
# 配置串口参数
serial_port = '/dev/ttyS2'  # 根据实际情况修改
baud_rate = 115200       # 波特率
timeout = 1            # 超时设置
detector = ArmorDetector(detect_color, 2, binary_val, light_params, color_params)  # 创建检测器对象
tracker = ArmorTracker(detect_color)
tracker.frame_add = 3
tracker.vfov = 35
transfer = Trans(serial_port, baud_rate, timeout)
cam = Cam(cam_params)
cam.detect(detector, tracker, transfer)
