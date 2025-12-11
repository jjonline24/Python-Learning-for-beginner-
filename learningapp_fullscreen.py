from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QScrollArea, QFrame,
    QHBoxLayout, QToolButton, QSizePolicy,
    QPushButton, QStyle, QSlider
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTime
import sys
import os

#คลาส FullscreenVideoWindow สำหรับแสดงวิดีโอแบบเต็มจอ
class FullscreenVideoWindow(QWidget):
    def __init__(self, media_player, parent=None):                                                      #ฟังก์ชั่นเริ่มต้น
        super().__init__(parent)                                                                        #สร้าง QWidget parent
        self.media_player = media_player                                                                #เก็บ media player ที่ส่งมา
        self.original_parent = parent                                                                   #เก็บพาเรนต์เดิมของวิดีโอไว้หลังจากปิดโหมด fullscreen
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)                   #ตั้งค่าวินโดว์แบบไม่มีขอบ 
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)                                          #ลบวิดีโอเมื่อปิดหน้าต่าง
        
        #สร้าง layout
        main_layout = QVBoxLayout(self)                                                                 #สร้าง layout หลัก
        main_layout.setContentsMargins(0, 0, 0, 0)                                                      #ตั้งค่าขอบเป็น 0      
        main_layout.setSpacing(0)                                                                       #ตั้งค่าช่องว่างเป็น 0    
        
        #สร้าง video widget สำหรับ fullscreen 
        self.video_widget = QVideoWidget()                                                              #สร้าง video widget             
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)     #ตั้งค่าให้ขยายเต็มที่
        main_layout.addWidget(self.video_widget)                                                        #เพิ่ม video widget ลงใน layout
        
        #สร้างส่วนควบคุม
        self.controls_widget = self._create_controls()                                                  #สร้างส่วนควบคุมวิดีโอ
        main_layout.addWidget(self.controls_widget)                                                     #เพิ่มส่วนควบคุมลงใน layout
        
        #เชื่อมต่อ media player กับ video widget
        self.media_player.setVideoOutput(self.video_widget)                                             #ตั้งค่า video output เป็น video widget
        
        #ตั้งค่า slider ให้ตรงกับตำแหน่งปัจจุบันของวิดีโอ
        current_position = self.media_player.position()                                                 #ตำแหน่งปัจจุบันของวิดีโอ
        current_duration = self.media_player.duration()                                                 #ความยาวทั้งหมดของวิดีโอ 
        
        if current_duration > 0:
            self.position_slider.setRange(0, current_duration)                                          #ตั้งค่าช่วงของ slider
            self.position_slider.setValue(current_position)                                             #ตั้งค่าตำแหน่งของ slider   
            self.update_time_label(current_position, current_duration)                                  #อัปเดตป้ายเวลา
        
        #เชื่อมต่อสัญญาณ
        self.media_player.positionChanged.connect(self.update_position)                                 #อัปเดตตำแหน่งเมื่อวิดีโอเปลี่ยนตำแหน่ง   
        self.media_player.durationChanged.connect(self.update_duration)                                 #อัปเดตช่วงเมื่อความยาววิดีโอเปลี่ยนแปลง
        # ใช้ sliderMoved แทน valueChanged เพื่อตอบสนองเฉพาะเมื่อผู้ใช้ลาก              
        self.position_slider.sliderMoved.connect(self.on_slider_moved)                                  #อัปเดตตำแหน่งเมื่อ slider ถูกลาก
        self.position_slider.sliderPressed.connect(self.slider_pressed)                                 #จัดการเมื่อเริ่มกดลาก   
        self.position_slider.sliderReleased.connect(self.slider_released)                               #จัดการเมื่อปล่อยการลาก
        
        #ตัวแปรสำหรับจัดการการลาก
        self.is_slider_being_dragged = False                                                            #ตัวแปรตรวจสอบการลาก slider 
        self.ignore_position_updates = False                                                            #ตัวแปรเพื่อเลี่ยงการอัปเดตตำแหน่งขณะลาก  
        
    def _create_controls(self):
        #สร้างส่วนควบคุมวิดีโอใน fullscreen
        control_widget = QWidget()                                                                      #สร้าง widget สำหรับส่วนควบคุม
        control_widget.setStyleSheet("""                                                                #ตั้งค่า style ของส่วนควบคุม
            QWidget {                   
                background-color: rgba(0, 0, 0, 200);                                                   /*สีพื้นหลังโปร่งใส*/
            }
            QPushButton {
                background-color: #1e88e5;                                                              /*สีพื้นหลังปุ่มกด*/
                color: white;                                                                           /*สีตัวอักษรปุ่มสีขาว*/
                border: none;                                                                           /*ไม่มีขอบ*/  
                padding: 10px 20px;                                                                     /*ระยะห่างภายในปุ่ม*/              
                font-size: 14px;                                                                        /*ขนาดตัวอักษร*/      
                border-radius: 5px;                                                                     /*มุมโค้งมน*/
                min-width: 80px;                                                                        /*ความกว้างขั้นต่ำของปุ่ม*/
            }
            QPushButton:hover {
                background-color: #1976d2;                                                              /*สีพื้นหลังปุ่มเมื่อเลื่อนเมาส์*/
            }
            QPushButton:pressed {
                background-color: #1565c0;                                                              /*สีพื้นหลังปุ่มเมื่อกด*/   
            }
        """)
        
        v_layout = QVBoxLayout(control_widget)                                                          #สร้าง layout แนวตั้ง
        v_layout.setContentsMargins(30, 15, 30, 15)                                                     #ตั้งค่าขอบของ layout   
        v_layout.setSpacing(15)                                                                         #ตั้งค่าช่องว่างระหว่างวิดเจ็ตใน layout
        
        #ตัวเลื่อน vdo และเวลา
        self.position_slider = QSlider(Qt.Orientation.Horizontal)                                       #สร้างตัวเลื่อนแนวนอน
        self.position_slider.setRange(0, 0)                                                             #ตั้งค่าช่วงเริ่มต้นเป็น 0-0       
        self.position_slider.setTracking(True)                                                          #ตั้งค่าให้ติดตามการเคลื่อนไหว
        self.position_slider.setEnabled(True)                                                           #ตั้งค่าให้ใช้งานได้
        self.position_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)                                 #สามารถรับ focus การเลื่อนได้
        self.position_slider.setMouseTracking(True)                                                     #ตั้งค่าติดตาม mouse
        self.position_slider.setStyleSheet("""                                                          /*ตั้งค่า style ของตัวเลื่อน*/
            QSlider {
                min-height: 40px;                                                                       /*ความสูงขั้นต่ำของ slider*/
                background: transparent;                                                                /*พื้นหลังโปร่งใส*/
            }
            QSlider::groove:horizontal {                                                                /*ความยาวของรางเลื่อน*/     
                border: 2px solid #666;                                                                 /*ขอบของรางเลื่อน*/
                height: 12px;                                                                           /*ความสูงของรางเลื่อน*/       
                background: #444;                                                                       /*สีพื้นหลังของรางเลื่อน*/
                margin: 0px;                                                                            /*ระยะขอบของรางเลื่อน*/
                border-radius: 6px;                                                                     /*มุมโค้งมนของรางเลื่อน*/
            }
            QSlider::handle:horizontal {                                                                /*ตัวจับเลื่อน*/
                background: #1e88e5;                                                                    /*สีพื้นหลังของตัวจับเลื่อน*/
                border: 2px solid #1565c0;                                                              /*ขอบของตัวจับเลื่อน*/
                width: 24px;                                                                            /*ความกว้างของตัวจับเลื่อน*/      
                height: 24px;                                                                           /*ความสูงของตัวจับเลื่อน*/  
                margin: -8px 0;                                                                         /*ระยะขอบของตัวจับเลื่อน*/       
                border-radius: 12px;                                                                    /*มุมโค้งมนของตัวจับเลื่อน*/     
            }
            QSlider::handle:horizontal:hover {                                                          /*ตัวจับเลื่อนเมื่อเลื่อนเมาส์*/
                background: #42a5f5;                                                                    /*สีพื้นหลังเมื่อเลื่อนเมาส์*/  
                border: 2px solid #1e88e5;                                                              /*ขอบเมื่อเลื่อนเมาส์*/
            }
            QSlider::handle:horizontal:pressed {                                                        /*ตัวจับเลื่อนเมื่อกด*/  
                background: #1976d2;                                                                    /*สีพื้นหลังเมื่อกด*/
            }
        """)
        
        self.time_label = QLabel("00:00 / 00:00")                                                       #สร้างป้ายแสดงเวลา
        self.time_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; min-width: 120px;")        #ตั้งค่า style ของป้ายเวลา
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)                   #จัดตำแหน่งป้ายเวลา
        
        slider_layout = QHBoxLayout()                                                                   #สร้าง layout แนวนอนสำหรับตัวเลื่อนและป้ายเวลา     
        slider_layout.setSpacing(15)                                                                    #ตั้งค่าช่องว่างระหว่างวิดเจ็ตใน layout
        slider_layout.addWidget(self.position_slider, 1)  # ให้ slider ขยายเต็มที่                          #เพิ่มตัวเลื่อนลงใน layout
        slider_layout.addWidget(self.time_label, 0)  # time label ไม่ขยาย                                #เพิ่มป้ายเวลาลงใน layout   
        v_layout.addLayout(slider_layout)                                                               #เพิ่ม layout ตัวเลื่อนลงใน layout หลัก
        
        #2. ปุ่มควบคุมวิดีโอ
        button_layout = QHBoxLayout()                                                                   #สร้าง layout แนวนอนสำหรับปุ่มควบคุมวิดีโอ
        style = QApplication.style()                                                                    #รับ style ของแอปพลิเคชัน
        
        #ปุ่ม Play
        play_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)                              #รับไอคอนปุ่มเล่น
        self.play_btn = QPushButton(play_icon, "เล่น")                                                   #สร้างปุ่มเล่น  
        self.play_btn.clicked.connect(self.media_player.play)                                           #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันเล่นวิดีโอ 
        
        #ปุ่ม Pause
        pause_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPause)                            #รับไอคอนปุ่มหยุดชั่วคราว
        self.pause_btn = QPushButton(pause_icon, "หยุดชั่วคราว")                                           #สร้างปุ่มหยุดชั่วคราว        
        self.pause_btn.clicked.connect(self.media_player.pause)                                         #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันหยุดชั่วคราว     
        
        #ปุ่ม Stop
        stop_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaStop)                              #รับไอคอนปุ่มหยุด
        self.stop_btn = QPushButton(stop_icon, "หยุด")                                                   #สร้างปุ่มหยุด
        self.stop_btn.clicked.connect(self.media_player.stop)                                           #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันหยุดวิดีโอ
        
        #ปุ่มปิด fullscreen
        close_icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)                     #รับไอคอนปุ่มปิด
        self.exit_fullscreen_btn = QPushButton(close_icon, "ออกจากโหมดเต็มจอ (ESC)")                     #สร้างปุ่มปิด fullscreen
        self.exit_fullscreen_btn.clicked.connect(self.exit_fullscreen)                                  #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันออกจาก fullscreen
        self.exit_fullscreen_btn.setStyleSheet("""
            QPushButton {                                                                               /*ตั้งค่า style ของปุ่มปิด fullscreen*/
                background-color: #1e88e5;;                                                             /*สีพื้นหลังปุ่มกด*/  
                color: white;                                                                           /*สีตัวอักษรปุ่มสีขาว*/  
                border: none;                                                                           /*ไม่มีขอบ*/ 
                padding: 10px 20px;                                                                     /*ระยะขอบภายในปุ่ม*/
                font-size: 14px;                                                                        /*ขนาดตัวอักษร*/            
                border-radius: 5px;                                                                     /*มุมโค้งมน*/
                min-width: 150px;                                                                       /*ความกว้างขั้นต่ำของปุ่ม*/
            }
            QPushButton:hover {                                                                         /*ปุ่มปิด fullscreen เมื่อเลื่อนเมาส์*/
                background-color: #c62828;                                                              /*สีพื้นหลังปุ่มเมื่อเลื่อนเมาส์*/   
            }
            QPushButton:pressed {                                                                       /*ปุ่มปิด fullscreen เมื่อกด*/             
                background-color: #b71c1c;                                                              /*สีพื้นหลังปุ่มเมื่อกด*/        
            }
        """)
        
        button_layout.addStretch(1)                                                                     #เพิ่มตัวเว้นวรรคด้านซ้ายของปุ่ม
        button_layout.addWidget(self.play_btn)                                                          #เพิ่มปุ่มเล่นลงใน layout
        button_layout.addWidget(self.pause_btn)                                                         #เพิ่มปุ่มหยุดชั่วคราวลงใน layout
        button_layout.addWidget(self.stop_btn)                                                          #เพิ่มปุ่มหยุดลงใน layout          
        button_layout.addWidget(self.exit_fullscreen_btn)                                               #เพิ่มปุ่มปิด fullscreen ลงใน layout
        button_layout.addStretch(1)                                                                     #เพิ่มตัวเว้นวรรคด้านขวาของปุ่ม 
        
        v_layout.addLayout(button_layout)                                                               #เพิ่ม layout ปุ่มควบคุมลงใน layout หลัก
        
        return control_widget                                                                           #คืนค่า widget ส่วนควบคุม
    
    def update_duration(self, duration):                                                                 
        #ตั้งค่าช่วงสูงสุดของตัวเลื่อน
        self.position_slider.setRange(0, duration)                                                      #ตั้งค่าช่วงของ slider
        self.update_time_label(self.media_player.position(), duration)                                  #อัปเดตป้ายเวลา
    
    def update_position(self, position):
        #อัปเดตตำแหน่งของตัวเลื่อน"""
        #ไม่อัปเดต slider เมื่อผู้ใช้กำลังลากอยู่
        if not self.is_slider_being_dragged and not self.ignore_position_updates:                       #ตรวจสอบสถานะการลาก
            self.position_slider.setValue(position)                                                     #ตั้งค่าตำแหน่งของ slider    
        #อัปเดตเวลาเสมอ
        self.update_time_label(position, self.media_player.duration())                                  #อัปเดตป้ายเวลา
    
    def on_slider_moved(self, position):
        #เมื่อผู้ใช้ลาก slider
        #อัปเดตเวลาทันทีขณะลาก
        self.update_time_label(position, self.media_player.duration())                                  #อัปเดตป้ายเวลาขณะลาก     
    
    def slider_pressed(self):
        #เมื่อเริ่มกดลากตัวเลื่อน
        self.is_slider_being_dragged = True                                                             #ตั้งค่าสถานะการลากเป็นจริง
        self.ignore_position_updates = True                                                             #ให้เลี่ยงการอัปเดตตำแหน่งขณะลาก
    
    def slider_released(self):
        #เมื่อปล่อยตัวเลื่อน - ตั้งค่าตำแหน่งสุดท้าย
        position = self.position_slider.value()                                                         #รับค่าตำแหน่งปัจจุบันของ slider       
        self.media_player.setPosition(position)                                                         #ตั้งค่าตำแหน่งวิดีโอตาม slider
        
        #ให้รอสักครู่แล้วค่อยเปิดการอัปเดต position อีกครั้ง
        self.is_slider_being_dragged = False                                                            
        # ใช้ QTimer เพื่อหน่วงเวลาเล็กน้อย
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: setattr(self, 'ignore_position_updates', False))                 #หน่วงเวลา 100 มิลลิวินาที ก่อนเปิดการอัปเดตตำแหน่งอีกครั้ง
    
    def update_time_label(self, current_ms, total_ms):
        #อัปเดตเวลาที่แสดง"""
        current_time = QTime(0, 0).addMSecs(current_ms)                                                 #แปลงมิลลิวินาทีเป็น QTime
        total_time = QTime(0, 0).addMSecs(total_ms)                                                     #แปลงมิลลิวินาทีเป็น QTime
        current_str = current_time.toString("mm:ss")                                                    #แปลงเวลาปัจจุบันเป็นสตริงรูปแบบ mm:ss นาที:วินาที
        total_str = total_time.toString("mm:ss")                                                        #แปลงเวลาทั้งหมดเป็นสตริงรูปแบบ mm:ss นาที:วินาที    
        self.time_label.setText(f"{current_str} / {total_str}")                                         #ตั้งค่าข้อความป้ายเวลา
    
    def exit_fullscreen(self):
        #ออกจากโหมด fullscreen
        #คืน video output กลับไปที่ parent
        if self.original_parent and hasattr(self.original_parent, 'video_widget'):                      #ตรวจสอบว่ามี parent และมี video_widget
            self.media_player.setVideoOutput(self.original_parent.video_widget)                         #ตั้งค่า video output กลับไปที่ video widget ของพาเรนต์
            # รีเซ็ตตัวแปร fullscreen_window ใน parent
            self.original_parent.fullscreen_window = None                                               #รีเซ็ตตัวแปร fullscreen_window ในพาเรนต์เป็น None
        self.close()                                                                                    #ปิดหน้าต่าง fullscreen            
    
    def keyPressEvent(self, event):
        #รองรับการกด ESC เพื่อออกจาก fullscreen
        if event.key() == Qt.Key.Key_Escape:                                                            #ตรวจสอบว่ากดปุ่ม ESC
            self.exit_fullscreen()                                                                      #เรียกฟังก์ชันออกจาก fullscreen
        else:
            super().keyPressEvent(event)                                                                #เรียกฟังก์ชันเริ่มต้นของ QWidget

#คลาส CollapsibleSection สำหรับเมนูส่วนที่ยุบ/ขยายได้
class CollapsibleSection(QWidget):
    def __init__(self, title, content, video_path, parent=None):                                        #ฟังก์ชั่นเริ่มต้น มีหัวข้อ เนื้อหา และพาธวิดีโอ
        super().__init__(parent)                                                                        #สร้าง QWidget พาเรนต์
        self.is_expanded = True                                                                         #สถานะเริ่มต้น: ขยายเมนู
        self.fullscreen_window = None                                                                   #ตัวแปรเก็บหน้าต่าง fullscreen video        
        
        self.media_player = None                                                                        #ตัวแปรเก็บ media player
        self.video_widget = None                                                                        #ตัวแปรเก็บ video widget
        self.audio_output = None                                                                        #ตัวแปรเก็บ audio output
        self.position_slider = None                                                                     #ตัวแปรเก็บตัวเลื่อนตำแหน่งวิดีโอ
        self.time_label = None                                                                          #ตัวแปรเก็บป้ายเวลา   

        main_layout = QVBoxLayout(self)                                                                 #สร้าง layout หลัก           
        main_layout.setContentsMargins(0, 0, 0, 0)                                                      #ตั้งค่าขอบเป็น 0
        main_layout.setSpacing(0)                                                                       #ตั้งค่าช่องว่างเป็น 0    

        self.title_bar = self._create_title_bar(title)                                                  #สร้างแถบชื่อเรื่อง
        main_layout.addWidget(self.title_bar)                                                           #เพิ่มแถบชื่อเรื่องลงใน layout    
        
        self.content_container = self._create_content_container(content, video_path)                    #สร้างคอนเทนเนอร์สำหรับเนื้อหาและวิดีโอ
        main_layout.addWidget(self.content_container)                                                   #เพิ่มคอนเทนเนอร์ลงใน layout

        self.controls_widget = self._create_video_controls()                                            #สร้างปุ่มควบคุมวิดีโอ
        main_layout.addWidget(self.controls_widget)                                                     #เพิ่มปุ่มควบคุมลงใน layout  
        
        if self.media_player and self.position_slider:                                                  #ถ้ามี media player และ slider
            self.media_player.positionChanged.connect(self.update_position)                             #เชื่อมต่อสัญญาณเปลี่ยนตำแหน่งของวิดีโอ  
            self.media_player.durationChanged.connect(self.update_duration)                             #เชื่อมต่อสัญญาณเปลี่ยนความยาวของวิดีโอ 
            self.position_slider.sliderMoved.connect(self.set_position)                                 #เชื่อมต่อสัญญาณเลื่อน slider เพื่อเปลี่ยนตำแหน่งวิดีโอ
            
        self.toggle_expand(initial=True)                                                                #ตั้งค่าสถานะเริ่มต้นของเมนูยุบ/ขยาย

    def _create_title_bar(self, title):
        #สร้างแถบชื่อเรื่อง
        title_bar = QWidget()                                                                           #สร้าง widget สำหรับแถบชื่อเรื่อง
        h_layout = QHBoxLayout(title_bar)                                                               #สร้าง layout แนวนอนสำหรับแถบชื่อเรื่อง      
        h_layout.setContentsMargins(10, 10, 10, 10)                                                     #ตั้งค่าขอบของ layout  
        
        self.toggle_btn = QToolButton()                                                                 #สร้างปุ่มเครื่องมือสำหรับยุบ/ขยาย   
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)                                            #ตั้งค่าเป็นลูกศรชี้ลง (ขยาย)
        self.toggle_btn.setStyleSheet("QToolButton { border: none; background-color: transparent; color: white; }")     #ตั้งค่า style ของปุ่ม
        
        self.title_label = QLabel(title)                                                                #สร้างป้ายชื่อเรื่อง
        self.title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: white;")             #ตั้งค่า style ของป้ายชื่อเรื่อง
        
        title_bar.setStyleSheet("background-color: #1e88e5; border-radius: 5px;")                       #ตั้งค่า style ของแถบชื่อเรื่อง
        
        h_layout.addWidget(self.toggle_btn, alignment=Qt.AlignmentFlag.AlignLeft)                       #เพิ่มปุ่มยุบ/ขยายลงใน layout
        h_layout.addWidget(self.title_label)                                                            #เพิ่มป้ายชื่อเรื่องลงใน layout
        h_layout.addStretch(1)                                                                          #เพิ่มตัวเว้นวรรคด้านขวา                 

        self.toggle_btn.clicked.connect(self.toggle_expand)                                             #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันยุบ/ขยาย      
        title_bar.mousePressEvent = lambda event: self.toggle_btn.click()                               

        return title_bar                                                                                #คืนค่าแถบชื่อเรื่อง   

    def _create_content_container(self, content, video_path):
        #สร้างคอนเทนเนอร์สำหรับเนื้อหาและวิดีโอ
        container = QWidget()                                                                           #สร้าง widget คอนเทนเนอร์
        v_layout = QVBoxLayout(container)                                                               #สร้าง layout แนวตั้งสำหรับคอนเทนเนอร์    
        v_layout.setContentsMargins(10, 5, 10, 10)                                                      #ตั้งค่าขอบของ layout  
        
        content_label = QLabel(content)                                                                 #สร้างป้ายเนื้อหา   
        content_label.setWordWrap(True)                                                                 #ตั้งค่าให้ข้อความขึ้นบรรทัดใหม่อัตโนมัติ   
        content_label.setStyleSheet("padding: 5px; border: 1px solid #ddd; background-color: #f9f9f9;") #ตั้งค่า style ของป้ายเนื้อหา
        
        self.video_widget = QVideoWidget()                                                              #สร้าง video widget สำหรับแสดงวิดีโอ
        self.video_widget.setMinimumHeight(300)                                                         #ตั้งค่าความสูงขั้นต่ำของ video widget  
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)     #ตั้งค่าให้ขยายเต็มที่
        
        self.media_player = QMediaPlayer()                                                              #สร้าง media player สำหรับเล่นวิดีโอ  
        self.audio_output = QAudioOutput()                                                              #สร้าง audio output สำหรับเสียงวิดีโอ 
        self.media_player.setAudioOutput(self.audio_output)                                             #ตั้งค่า audio output ให้กับ media player
        self.audio_output.setVolume(50.0)                                                               #ตั้งค่าระดับเสียงเริ่มต้นที่ 50%  
        
        self.media_player.setVideoOutput(self.video_widget)                                             #ตั้งค่า video output เป็น video widget
        
        file_url = QUrl.fromLocalFile(video_path)                                                       #สร้าง URL จากพาธไฟล์วิดีโอ
        
        if file_url.isValid() and os.path.exists(video_path):                                           #ตรวจสอบว่า URL ถูกต้องและไฟล์มีอยู่
            self.media_player.setSource(file_url)                                                       #ตั้งค่าแหล่งที่มาของ media player เป็นไฟล์วิดีโอ 
        else:
            error_label = QLabel(f"❌ ไม่พบไฟล์วิดีโอ:\n'{video_path}'\nโปรดตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกันและชื่อถูกต้อง.")      #สร้างป้ายแสดงข้อผิดพลาดเมื่อไม่พบไฟล์วิดีโอ
            error_label.setWordWrap(True)                                                               #ตั้งค่าให้ข้อความขึ้นบรรทัดใหม่อัตโนมัติ
            error_label.setStyleSheet("color: red; font-weight: bold; background-color: #fee;")         #ตั้งค่า style ของป้ายข้อผิดพลาด
            v_layout.addWidget(error_label)                                                             #เพิ่มป้ายข้อผิดพลาดลงใน layout
        
        v_layout.addWidget(content_label)                                                               #เพิ่มป้ายเนื้อหาลงใน layout
        v_layout.addWidget(self.video_widget)                                                           #เพิ่ม video widget ลงใน layout           
        
        return container                                                                                #คืนค่าคอนเทนเนอร์

    def _create_video_controls(self):
        #สร้างปุ่มควบคุมวิดีโอ
        if not self.media_player:                                                                       #ถ้าไม่มี media player ให้คืนค่า widget ว่าง
            return QWidget()                                                                            #สร้าง widget ว่าง
        
        control_widget = QWidget()                                                                      #สร้าง widget สำหรับส่วนควบคุม   
        v_layout = QVBoxLayout(control_widget)                                                          #สร้าง layout แนวตั้งสำหรับส่วนควบคุม      
        v_layout.setContentsMargins(10, 5, 10, 10)                                                      #ตั้งค่าขอบของ layout
        v_layout.setSpacing(5)                                                                          #ตั้งค่าช่องว่างระหว่างวิดเจ็ตใน layout 

        #ตัวเลื่อนและเวลา
        self.position_slider = QSlider(Qt.Orientation.Horizontal)                                       #สร้างตัวเลื่อนแนวนอน
        self.position_slider.setRange(0, 0)                                                             #ตั้งค่าช่วงเริ่มต้นเป็น 0-0    
        self.position_slider.setStyleSheet("""                                                          /*ตั้งค่า style ของตัวเลื่อน*/   
            QSlider::groove:horizontal {                                                                /*ความยาวของรางเลื่อน*/     
                border: 1px solid #999999;                                                              /*ขอบของรางเลื่อน*/
                height: 8px;                                                                            /*ความสูงของรางเลื่อน*/       
                background: #ccc;                                                                       /*สีพื้นหลังของรางเลื่อน*/      
                margin: 2px 0;                                                                          /*ระยะขอบของรางเลื่อน*/
                border-radius: 4px;                                                                     /*มุมโค้งมนของรางเลื่อน*/       
            }
            QSlider::handle:horizontal {                                                                /*ตัวจับเลื่อน*/
                background: #1e88e5;                                                                    /*สีพื้นหลังของตัวจับเลื่อน*/      
                border: 1px solid #1e88e5;                                                              /*ขอบของตัวจับเลื่อน*/       
                width: 18px;                                                                            /*ความกว้างของตัวจับเลื่อน*/    
                margin: -5px 0;                                                                         /*ระยะขอบของตัวจับเลื่อน*/ 
                border-radius: 9px;                                                                     /*มุมโค้งมนของตัวจับเลื่อน*/
            }
        """)

        self.time_label = QLabel("00:00 / 00:00")                                                       #สร้างป้ายแสดงเวลา
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)                                       #จัดตำแหน่งป้ายเวลา

        slider_layout = QHBoxLayout()                                                                   #สร้าง layout แนวนอนสำหรับตัวเลื่อนและป้ายเวลา    
        slider_layout.addWidget(self.position_slider)                                                   #เพิ่มตัวเลื่อนลงใน layout   
        slider_layout.addWidget(self.time_label)                                                        #เพิ่มป้ายเวลาลงใน layout
        
        v_layout.addLayout(slider_layout)                                                               #เพิ่ม layout ตัวเลื่อนลงใน layout หลัก      

        #ปุ่มควบคุม
        button_layout = QHBoxLayout()                                                                   #สร้าง layout แนวนอนสำหรับปุ่มควบคุมวิดีโอ
        style = QApplication.style()                                                                    #รับ style ของแอปพลิเคชัน  
        
        play_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay)                              #ตั้งค่าไอคอนปุ่มเล่น
        self.play_btn = QPushButton(play_icon, "เล่น")                                                   #สร้างปุ่มเล่น
        self.play_btn.clicked.connect(self.media_player.play)                                           #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันเล่นวิดีโอ
        
        pause_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPause)                            #ตั้งค่าไอคอนปุ่มหยุดชั่วคราว
        self.pause_btn = QPushButton(pause_icon, "หยุดชั่วคราว")                                           #สร้างปุ่มหยุดชั่วคราว    
        self.pause_btn.clicked.connect(self.media_player.pause)                                         #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันหยุดชั่วคราว 
        
        stop_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaStop)                              #ตั้งค่าไอคอนปุ่มหยุด
        self.stop_btn = QPushButton(stop_icon, "หยุด")                                                   #สร้างปุ่มหยุด
        self.stop_btn.clicked.connect(self.media_player.stop)                                           #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันหยุดวิดีโอ   
        
        #ปุ่มขยายเต็มจอ
        fullscreen_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMaxButton)                #ตั้งค่าไอคอนปุ่มขยายเต็มจอ
        self.fullscreen_btn = QPushButton(fullscreen_icon, "ขยายเต็มจอ")                                 #สร้างปุ่มขยายเต็มจอ
        self.fullscreen_btn.clicked.connect(self.enter_fullscreen)                                      #เชื่อมต่อสัญญาณคลิกกับฟังก์ชันขยายเต็มจอ
        self.fullscreen_btn.setStyleSheet("""                                                           /*ตั้งค่า style ของปุ่มขยายเต็มจอ*/        
            QPushButton {                                                                               /*ตั้งค่า style ของปุ่มกด*/  
                background-color: #1e88e5;                                                              /*สีพื้นหลังปุ่มกด ขยายเต็ม*/  
                color: white;                                                                           /*สีตัวอักษรปุ่มสีขาว*/    
                border: none;                                                                           /*ไม่มีขอบ*/       
                padding: 5px 10px;                                                                      /*ระยะขอบภายในปุ่ม*/  จอ
                border-radius: 3px;                                                                     /*มุมโค้งมน*/  
            }
            QPushButton:hover {                                                                         /*ปุ่มขยายเต็มจอเมื่อเลื่อนเมาส์*/       
                background-color: #c62828;                                                              /*สีพื้นหลังปุ่มเป็นสีแดงเมื่อเลื่อนเมาส์*/          
            }
        """)
        
        button_layout.addStretch(1)                                                                     #เพิ่มตัวเว้นวรรคด้านซ้ายของปุ่ม             
        button_layout.addWidget(self.play_btn)                                                          #เพิ่มปุ่มเล่นลงใน layout
        button_layout.addWidget(self.pause_btn)                                                         #เพิ่มปุ่มหยุดชั่วคราวลงใน layout      
        button_layout.addWidget(self.stop_btn)                                                          #เพิ่มปุ่มหยุดลงใน layout    
        button_layout.addWidget(self.fullscreen_btn)                                                    #เพิ่มปุ่มขยายเต็มจอลงใน layout
        button_layout.addStretch(1)                                                                     #เพิ่มตัวเว้นวรรคด้านขวาของปุ่ม                 

        v_layout.addLayout(button_layout)                                                               #เพิ่ม layout ปุ่มควบคุมลงใน layout หลัก
        control_widget.setVisible(False)                                                                #ตั้งค่าให้ส่วนควบคุมมองไม่เห็นเริ่มต้น
        return control_widget                                                                           #คืนค่าส่วนควบคุม

    def enter_fullscreen(self):
        #เข้าสู่โหมด fullscreen
        #ถ้ามี fullscreen window อยู่แล้ว ให้ปิดก่อน
        if self.fullscreen_window:                                                                      #ตรวจสอบว่ามีหน้าต่าง fullscreen อยู่แล้ว
            self.fullscreen_window.close()                                                              #ปิดหน้าต่าง fullscreen เดิม    
            self.fullscreen_window = None                                                               #รีเซ็ตตัวแปร fullscreen_window เป็น None
        
        #สร้าง fullscreen window ใหม่
        self.fullscreen_window = FullscreenVideoWindow(self.media_player, self)                         #สร้างหน้าต่าง fullscreen ใหม่
        self.fullscreen_window.showFullScreen()                                                         #แสดงหน้าต่าง fullscreen แบบเต็มจอ       

    def update_duration(self, duration):
        #ตั้งค่าช่วงสูงสุดของตัวเลื่อน
        self.position_slider.setRange(0, duration)                                                      #ตั้งค่าช่วงของ slider
        self.update_time_label(self.media_player.position(), duration)                                  #อัปเดตป้ายเวลา

    def update_position(self, position):
        #อัปเดตตำแหน่งของตัวเลื่อน
        if not self.position_slider.isSliderDown():                                                     #ตรวจสอบว่าผู้ใช้ไม่ได้กำลังลากตัวเลื่อนอยู่
            self.position_slider.setValue(position)                                                     #ตั้งค่าตำแหน่งของ slider
        self.update_time_label(position, self.media_player.duration())                                  #อัปเดตป้ายเวลา

    def set_position(self, position):
        #ตั้งค่าตำแหน่งวิดีโอ
        self.media_player.setPosition(position)                                                         #ตั้งค่าตำแหน่งวิดีโอตาม slider
        self.update_time_label(position, self.media_player.duration())                                  #อัปเดตป้ายเวลา
        
    def update_time_label(self, current_ms, total_ms):
        #อัปเดตเวลาที่แสดง
        current_time = QTime(0, 0).addMSecs(current_ms)                                                 #แปลงมิลลิวินาทีเป็น QTime
        total_time = QTime(0, 0).addMSecs(total_ms)                                                     #แปลงมิลลิวินาทีเป็น QTime
        current_str = current_time.toString("mm:ss")                                                    #แปลงเวลาปัจจุบันเป็นสตริงรูปแบบ mm:ss นาที:วินาที
        total_str = total_time.toString("mm:ss")                                                        #แปลงเวลาทั้งหมดเป็นสตริงรูปแบบ mm:ss นาที:วินาที
        self.time_label.setText(f"{current_str} / {total_str}")                                         #ตั้งค่าข้อความป้ายเวลา

    def toggle_expand(self, initial=False):
        #จัดการการยุบและขยายส่วนเนื้อหา
        if not initial:                                                                                 #ถ้าไม่ใช่การตั้งค่าเริ่มต้น
            self.is_expanded = not self.is_expanded                                                     #สลับสถานะยุบ/ขยาย
            
        self.content_container.setVisible(self.is_expanded)                                             #ตั้งค่าการมองเห็นของคอนเทนเนอร์เนื้อหา
        self.controls_widget.setVisible(self.is_expanded)                                               #ตั้งค่าการมองเห็นของปุ่มควบคุมวิดีโอ
        
        if self.is_expanded:                                                                            #ถ้าอยู่ในสถานะขยาย
            self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)                                        #ตั้งค่าเป็นลูกศรชี้ลง
        else:
            self.toggle_btn.setArrowType(Qt.ArrowType.RightArrow)                                       #ตั้งค่าเป็นลูกศรชี้ขวา
            if self.media_player:                                                                       #ถ้ามี media player เล่นอยู่
                self.media_player.pause()                                                               #หยุดเล่นวิดีโอเมื่อยุบเมนู
        
        self.updateGeometry()                                                                           #อัปเดตขนาดของวิดเจ็ตด้วย

#คลาส VideoPlayerApp
class VideoPlayerApp(QWidget):
    def __init__(self, section_data):                                                                   #ฟังก์ชั่นเริ่มต้น รับข้อมูลส่วนต่างๆ
        super().__init__()                                                                              #สร้าง QWidget parent
        self.setWindowTitle("วิดีโอเนื้อหาการเรียน python (กดที่หัวข้อวิดีโอเพือย่อ/ขยาย)")                                                   #ตั้งชื่อหน้าต่าง
        self.resize(800, 600)                                                                           #ตั้งขนาดหน้าต่างเริ่มต้น                      
        self.sections_data = section_data                                                               #เก็บข้อมูลส่วนต่างๆ     
        self.setup_ui()                                                                                 #ตั้งค่า UI

    def setup_ui(self):
        scroll = QScrollArea()                                                                          #สร้าง scroll area
        scroll.setWidgetResizable(True)                                                                 #ตั้งค่าให้ widget ภายใน scroll สามารถขยายได้               
        scroll.setFrameShape(QFrame.Shape.NoFrame)                                                      #ตั้งค่าไม่มีกรอบรอบ scroll area 

        content_widget = QWidget()                                                                      #สร้าง widget สำหรับเนื้อหาภายใน scroll area
        content_layout = QVBoxLayout(content_widget)                                                    #สร้าง layout แนวตั้งสำหรับเนื้อหา
        content_layout.setContentsMargins(10, 10, 10, 10)                                               #ตั้งค่าขอบของ layout      

        for i, data in enumerate(self.sections_data):                                                   #วนลูปผ่านข้อมูลแต่ละส่วน
            section_widget = CollapsibleSection(                                                        #สร้าง widget ส่วนที่ยุบ/ขยายได้ ประกอบด้วย
                data["title"],                                                                          #หัวข้อ
                data["content"],                                                                        #เนื้อหา
                data["video_path"]                                                                      #พาธวิดีโอ            
            )
            content_layout.addWidget(section_widget)                                                    #เพิ่ม widget ส่วนที่ยุบ/ขยายได้ลงใน layout    
            
            if i < len(self.sections_data) - 1:                                                         #ถ้าไม่ใช่ส่วนสุดท้าย ให้เพิ่มเส้นคั่นระหว่างส่วน
                separator = QFrame()                                                                    #สร้างเส้นคั่น     
                separator.setFrameShape(QFrame.Shape.HLine)                                             #ตั้งค่าเป็นเส้นแนวนอน
                separator.setFrameShadow(QFrame.Shadow.Sunken)                                          #ตั้งค่าเงาของเส้นคั่น
                separator.setStyleSheet("margin: 10px 0;")                                              #ตั้งค่าระยะขอบของเส้นคั่น
                content_layout.addWidget(separator)                                                     #เพิ่มเส้นคั่นลงใน layout
        
        content_layout.addStretch(1)                                                                    #เพิ่มตัวเว้นวรรคด้านล่างสุดของเนื้อหา
        scroll.setWidget(content_widget)                                                                #ตั้งค่า widget ภายใน scroll area          
        
        main_layout = QVBoxLayout(self)                                                                 #สร้าง layout หลักของหน้าต่าง       
        main_layout.addWidget(scroll)                                                                   #เพิ่ม scroll area ลงใน layout หลัก

#ส่วนเช็คป้ายชื่อ
if __name__ == "__main__":                                                                              
    
    current_script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))                                  #รับพาธโฟลเดอร์ที่เก็บสคริปต์นี้อยู่

    video_file_1 = "pythoninstallation.mp4"                                                             #ชื่อไฟล์วิดีโอของหัวข้อที่ 1    
    video_file_2 = "homeworkday2.mp4"                                                                   #ชื่อไฟล์วิดีโอของหัวข้อที่ 2    
    video_file_3 = "classroomnamechange.mp4"                                                            #ชื่อไฟล์วิดีโอของหัวข้อที่ 3
    
    video_path_1 = os.path.join(current_script_dir, video_file_1)                                       #สร้างพาธเต็มของไฟล์วิดีโอหัวข้อที่ 1
    video_path_2 = os.path.join(current_script_dir, video_file_2)                                       #สร้างพาธเต็มของไฟล์วิดีโอหัวข้อที่ 2
    video_path_3 = os.path.join(current_script_dir, video_file_3)                                       #สร้างพาธเต็มของไฟล์วิดีโอหัวข้อที่ 3
    
    print(f"โฟลเดอร์ปัจจุบัน: {current_script_dir}")                                                        #แสดงพาธโฟลเดอร์ปัจจุบัน
    print(f"Path ที่ใช้สำหรับวิดีโอ 1: {video_path_1}")                                                       #แสดงพาธที่ใช้สำหรับวิดีโอหัวข้อที่ 1
    
    sections_data = [
        {
            "title": "วิดีโอ 1: แนะนำ",                                                                   #หัวข้อของวิดีโอ 1
            "content": f"วิธีการติดตั้ง Python และเครื่องมือที่จำเป็นที่ใช้: '{video_path_1}'",                       #เนื้อหาของวิดีโอ 1
            "video_path": video_path_1                                                                  #พาธของวิดีโอ 1       
        },
        {
            "title": "วิดีโอ 2: การบ้านวันที่ 2",                                                             #หัวข้อของวิดีโอ 2        
            "content": f"วิธีทำตัวอย่างการบ้านวันที่ 2: เขียนฟังก์ชั่นคำนวณค่า BMI '{video_path_2}'",                #เนื้อหาของวิดีโอ 2
            "video_path": video_path_2                                                                  #พาธของวิดีโอ 2
        },
        {
            "title": "วิดีโอ 3: การเปลี่ยนชื่อใน Google Classroom",                                           #หัวข้อของวิดีโอ 3
            "content": f"วิธีการเปลี่ยนชื่อใน Google Classroom: '{video_path_3}'",                            #เนื้อหาของวิดีโอ 3
            "video_path": video_path_3                                                                  #พาธของวิดีโอ 3
        }
    ]

    try:
        app = QApplication(sys.argv)                                                                    #สร้าง QApplication
    except RuntimeError:                                                                                #ยกเว้นถ้ามี QApplication อยู่แล้ว          
        app = QApplication.instance()                                                                   #ให้รับ instance ที่มีอยู่แล้ว       

    w = VideoPlayerApp(sections_data)                                                                   #สร้างหน้าต่าง VideoPlayerApp พร้อมส่งข้อมูลส่วนต่างๆ    
    w.show()                                                                                            #และแสดงหน้าต่าง            
    sys.exit(app.exec())                                                                                #รันแอปพลิเคชันและรอจนกว่าจะปิดหน้าต่าง