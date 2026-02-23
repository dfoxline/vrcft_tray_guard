# 🛡️ VRCFT Guard | VRCFT 守护卫士 v1.1

<p align="center">
  <img src="bot.ico" width="128" height="128" alt="VRCFT Guard Logo">
</p>

<p align="center">
  <strong>一款解决 VRCFaceTracking 关闭残留问题的轻量化守护工具</strong><br>
  <em>A lightweight guard tool to fix VRCFaceTracking closure issues.</em>
</p>

---

## 📖 简介 | Introduction

**VRCFT Guard** 是一个旨在解决 VRCFaceTracking (VRCFT) 常见 Bug 的自动化小工具。
由于 VRCFT 的模块沙盒机制，主程序关闭后 `VRCFaceTracking.ModuleProcess.exe` 经常无法自动退出，导致 Steam 认为游戏仍在运行，或者导致 OSC 端口被持续占用。

本工具通过 OS 级别的句柄监听，在**不消耗 CPU** 的情况下，实时监测并在主程序关闭后立即清理残留进程。

**VRCFT Guard** is a specialized tool to fix a common bug in VRCFaceTracking. Due to its module sandboxing, `VRCFaceTracking.ModuleProcess.exe` often stays active after the main app is closed, preventing Steam from stopping the game or blocking OSC ports. This tool uses OS-level handle listening to monitor and clean up residual processes instantly with **near-zero CPU usage**.

---

## 🆕 V1.1 更新内容 | What's New in V1.1

- 🧹 **启动智能大扫除 (Startup Cleanup):** 软件启动时自动扫描。若主程序未运行但存在“僵尸模块”，将立即强制清理。
- 🚀 **原生开机自启 (Native Auto-Start):** 新增 UI 选项，通过 Windows 注册表实现自启。配合 `--minimized` 参数，开机时可静默隐藏至托盘。
- ⚙️ **底层性能调优 (Performance Tuning):** 优化了进程遍历逻辑与异常处理，大幅减少 CPU 上下文切换，运行更加稳定。

- 🧹 **Startup Cleanup:** Automatically scans the environment upon launch. If the main app isn't running but "zombie modules" exist, they are cleared immediately.
- 🚀 **Native Auto-Start:** Toggle auto-start directly in the UI. Uses the `--minimized` flag to launch silently into the system tray on Windows startup.
- ⚙️ **Performance Tuning:** Optimized process iteration and exception handling to minimize CPU context switching and improve stability.

---

## ✨ 核心特性 | Features

- **⚡ 极低占用 (Zero CPU Idle):** 采用 `wait()` 阻塞挂起而非高频轮询，运行期间几乎 0 占用。
- **📥 托盘静默 (System Tray):** 支持最小化到系统托盘，静默守护，不占用任务栏空间。
- **📝 实时日志 (Real-time Logs):** 窗口化显示详细操作日志，清理状态一目了然。
- **🎨 兼容打包 (Standalone Ready):** 适配 PyInstaller 路径逻辑，支持单文件打包并完美内嵌图标。

- **⚡ Efficient Monitoring:** Uses OS-level `wait()` instead of busy loops, ensuring near-zero CPU impact.
- **📥 System Tray Support:** Minimizes to the tray to stay out of your way while keeping your environment clean.
- **📝 Real-time Logs:** See exactly when processes are detected or cleaned through the built-in log viewer.
- **🎨 Deployment Ready:** Fully compatible with PyInstaller for single-EXE distribution with embedded icons.

---

## 🛠️ 安装与编译 | Setup & Build

### 1. 源码运行 | Requirements
- Python 3.10+
- `psutil`, `PySide6`

```bash
# 克隆仓库 Clone the repo
git clone [https://github.com/YourUsername/VRCFT_Guard.git](https://github.com/YourUsername/VRCFT_Guard.git)
cd VRCFT_Guard

# 安装依赖 Install dependencies
pip install psutil PySide6

# 启动运行 Run the script
python vrcft_tray_guard.py
