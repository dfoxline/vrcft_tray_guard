import os
import sys
import time
import psutil
import winreg # 用于操作 Windows 注册表实现开机自启
from PySide6.QtWidgets import (QApplication, QMainWindow, QPlainTextEdit, 
                             QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QStyle, QCheckBox)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon, QAction, QFont

# 配置 
MAIN_EXE = "VRCFaceTracking.exe"
MODULE_EXE = "VRCFaceTracking.ModuleProcess.exe"
APP_NAME = "VRCFT_Guard"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_resource_path(relative_path):
    """兼容 PyInstaller 打包的资源路径获取"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def get_exe_path():
    """获取当前程序的绝对路径，用于写入注册表"""
    if getattr(sys, 'frozen', False):
        return sys.executable # 打包后的 exe 路径
    return os.path.abspath(sys.argv[0]) # 没打包时的 py 路径

class MonitorThread(QThread):
    log_signal = Signal(str)

    def run(self):
        # 1. 启动时的智能大扫除：如果主程序没开，但模块还在，直接杀！
        self.initial_cleanup()
        self.log_signal.emit(">>> 后台监控已就位，进入极低耗能模式...")
        
        # 2. 核心监控循环
        while True:
            vrcft_proc = self.find_process(MAIN_EXE)

            if vrcft_proc:
                self.log_signal.emit(f"🎯 捕获到 {MAIN_EXE} (PID: {vrcft_proc.pid})")
                try:
                    # OS 级挂起，0 CPU 占用等待目标进程死亡
                    vrcft_proc.wait()
                except psutil.Error:
                    pass
                
                self.log_signal.emit("⚠️ 主程序已退出，1秒后执行清理...")
                time.sleep(1) # 缓冲时间
                self.kill_residuals()
            
            time.sleep(3) # 低频轮询

    def find_process(self, name):
        """性能优化：找到即停，不遍历全表"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == name:
                    return proc
            except psutil.Error:
                pass
        return None

    def initial_cleanup(self):
        """启动时的环境检测"""
        if not self.find_process(MAIN_EXE):
            count = self.kill_residuals(silent=True)
            if count > 0:
                self.log_signal.emit(f"🧹 启动清理：发现了 {count} 个上个班次的僵尸模块，已超度。")

    def kill_residuals(self, silent=False):
        count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == MODULE_EXE:
                    proc.kill()
                    count += 1
            except psutil.Error: 
                pass
                
        if not silent:
            if count > 0:
                self.log_signal.emit(f"✅ 清理完毕：成功结束了 {count} 个残留进程。")
            else:
                self.log_signal.emit("🔍 未发现残留进程，环境干净。")
        return count

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VRCFT 守护卫士 v1.1")
        self.resize(550, 350)

        # 图标加载逻辑
        icon_path = get_resource_path("bot.ico")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
        else:
            self.app_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(self.app_icon)

        # UI 布局构建
        layout = QVBoxLayout()
        
        # 日志框
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border-radius: 5px;")
        layout.addWidget(self.log_view)
        
        # 开机自启复选框
        self.autostart_cb = QCheckBox("🚀 开机自动启动 (静默隐藏到托盘)")
        self.autostart_cb.setChecked(self.check_autostart_status())
        self.autostart_cb.stateChanged.connect(self.toggle_autostart)
        layout.addWidget(self.autostart_cb)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.setup_tray()

        self.monitor = MonitorThread()
        self.monitor.log_signal.connect(self.add_log)
        self.monitor.start()

    def add_log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.log_view.appendPlainText(f"[{timestamp}] {text}")
        scrollbar = self.log_view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ================= 注册表开机自启逻辑 =================
    def check_autostart_status(self):
        """检查注册表中是否有我们的启动项"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False

    def toggle_autostart(self, state):
        """开关开机自启"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
            if state == Qt.CheckState.Checked.value:
                # 写入路径，并附带 --minimized 参数
                cmd = f'"{get_exe_path()}" --minimized'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                self.add_log("⚙️ 已开启开机自启。")
            else:
                winreg.DeleteValue(key, APP_NAME)
                self.add_log("⚙️ 已关闭开机自启。")
            winreg.CloseKey(key)
        except Exception as e:
            self.add_log(f"❌ 设置自启失败: {e}")

    # ================= 托盘与窗口逻辑 =================
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon) 
        
        tray_menu = QMenu()
        show_action = QAction("显示主窗口", self)
        quit_action = QAction("完全退出", self)
        
        show_action.triggered.connect(self.restore_window)
        quit_action.triggered.connect(self.real_quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
        self.tray.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: 
            if self.isVisible():
                self.hide()
            else:
                self.restore_window()

    def restore_window(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore() 
        self.hide()    
        self.tray.showMessage("VRCFT Guard", "已最小化到托盘继续守护", QSystemTrayIcon.MessageIcon.Information, 2000)

    def real_quit(self):
        self.monitor.terminate() 
        QApplication.instance().quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    
    window = MainWindow()
    
    # 检测启动参数，如果是开机自启(--minimized)则不显示主窗口
    if "--minimized" not in sys.argv:
        window.show()
    
    sys.exit(app.exec())