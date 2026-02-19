import os
import sys
import time
import psutil
from PySide6.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit, 
                             QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QStyle)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QIcon, QAction, QFont

# 把目标进程名字提出来，以后要是 VRCFT 改名了直接改这俩就行
MAIN_EXE = "VRCFaceTracking.exe"
MODULE_EXE = "VRCFaceTracking.ModuleProcess.exe"

def get_resource_path(relative_path):
    """
    找文件的绝对路径。
    主要是为了防一手 PyInstaller 打包：打包成单文件exe后，
    运行时会解压到一个临时目录(_MEIPASS)，得去那里找我们的 bot.ico
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # 没打包的话，就直接拿当前 py 文件所在的目录
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

class MonitorThread(QThread):
    # 用信号机制往主界面传日志，不然跨线程直接改 UI 会崩
    log_signal = Signal(str)

    def run(self):
        self.log_signal.emit(">>> 后台狗仔队已就位，开始蹲点...")
        
        while True:
            vrcft_proc = None
            # 翻一遍当前运行的所有进程，找找有没有主程序
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == MAIN_EXE:
                    vrcft_proc = proc
                    break

            if vrcft_proc:
                self.log_signal.emit(f"逮到 {MAIN_EXE} 了 (PID: {vrcft_proc.pid})")
                try:
                    # 这里的 wait() 是精髓。
                    # 它会让代码停在这，等系统通知进程死掉再往下走。
                    # 完全不占用 CPU，比写个 while 循环在那干瞪眼强多了
                    vrcft_proc.wait()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # 进程突然没了或者权限不够，不管它，接着跑
                    pass
                
                self.log_signal.emit("主程序开溜了，准备清理战场...")
                time.sleep(1) # 稍微等一秒，免得主程序还没死透
                self.kill_residuals()
            
            # 主程序没开的时候，每 3 秒睁眼看一次，省资源
            time.sleep(3)

    def kill_residuals(self):
        count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == MODULE_EXE:
                    proc.kill() # 发现残留，直接按死
                    count += 1
            except: 
                pass
                
        if count > 0:
            self.log_signal.emit(f"清理完毕：顺手干掉了 {count} 个赖着不走的模块。")
        else:
            self.log_signal.emit("扫了一圈，没发现残留进程。")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VRCFT 守护卫士")
        self.resize(500, 300)

        # 尝试加载同目录下的 bot.ico
        icon_path = get_resource_path("bot.ico")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
        else:
            # 万一图标丢了，给个系统自带的电脑图标兜底，免得报错闪退
            self.app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            
        self.setWindowIcon(self.app_icon)

        # 搞个简单的黑底白字文本框当控制台
        layout = QVBoxLayout()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_view)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 把右下角托盘图标也支棱起来
        self.setup_tray()

        # 启动后台监听线程
        self.monitor = MonitorThread()
        self.monitor.log_signal.connect(self.add_log)
        self.monitor.start()

    def add_log(self, text):
        # 打印日志顺带加上时间戳
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {text}")
        
        # 保证有新日志时自动滚到最下面，不用手动拿鼠标拖
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon) 
        
        # 右键菜单
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        quit_action = QAction("彻底退出", self)
        
        show_action.triggered.connect(self.restore_window)
        quit_action.triggered.connect(self.real_quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator() # 加条分割线好看点
        tray_menu.addAction(quit_action)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
        
        # 绑定点击托盘图标的动作
        self.tray.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        # 如果是鼠标左键单击
        if reason == QSystemTrayIcon.ActivationReason.Trigger: 
            if self.isVisible():
                self.hide() # 看得见就藏起来
            else:
                self.restore_window() # 看不见就揪出来

    def restore_window(self):
        # 把窗口弹出来，并且强制抢占焦点，防遮挡
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        # 拦截右上角的 X 号
        event.ignore() 
        self.hide()    
        
        # 弹个气泡通知，告诉自己它还在后台干活
        self.tray.showMessage(
            "VRCFT 守护卫士", 
            "程序已乖乖缩进托盘继续摸鱼~", 
            QSystemTrayIcon.MessageIcon.Information, 
            2000 # 显示两秒
        )

    def real_quit(self):
        # 这才是真要关了，先掐断监听线程，再退出整个程序
        self.monitor.terminate() 
        QApplication.instance().quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 这句很关键：告诉 PyQt 就算所有窗口都关了，也别擅自结束程序
    app.setQuitOnLastWindowClosed(False) 
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())