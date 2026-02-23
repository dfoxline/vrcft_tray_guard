# 🛡️ vrcft_tray_guard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![AI: Gemini-Assistant](https://img.shields.io/badge/Collaborator-AI-green.svg)](#-开发背景)

**vrcft_tray_guard** 是一个专为解决 [VRCFaceTracking](https://github.com/benaclejames/VRCFaceTracking) 进程残留 bug 而设计的轻量级工具。它能自动监控主程序的生命周期，并在其关闭后强制清理“赖着不走”的模块进程，还你一个干净的 Steam/VRChat 运行状态。

---

## ✨ 功能特性

* **智能监控**：基于 Windows 事件句柄监听，非暴力轮询，CPU 占用几乎为零。
* **彻底清理**：精准捕捉 `VRCFaceTracking.ModuleProcess.exe` 残留并一键强制结束。
* **原生交互**：配备简洁的 GUI 界面，支持实时日志滚动。
* **静默守护**：支持最小化到系统托盘（右下角图标），点叉不退出，后台默默守护。
* **开箱即用**：自动识别本地 `bot.ico` 图标，支持 PyInstaller 单文件打包。

---

## 🛠️ 安装与使用

### 环境要求
* Python 3.8+
* 依赖库：`psutil`, `PySide6`

### 快速开始
1. 克隆仓库：
   ```bash
   git clone [https://github.com/你的用户名/VRCFT-Guardian.git](https://github.com/你的用户名/VRCFT-Guardian.git)
   cd VRCFT-Guardian
