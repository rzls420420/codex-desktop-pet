# 白龙小姐桌宠：Windows 11

本包包含当前透明版动作素材，不含旧素材、原始生成图或账号数据。它是源码运行与构建包，尚不包含预编译 EXE，也尚未在 Windows 实机验证。

1. 安装 Python 3.10 或更新版本，并确认 Python Launcher（`py`）可用。
2. 双击 `setup.bat`。它在本目录创建 `.venv`，并联网安装 PyQt5 与 PyInstaller。
3. 双击 `standalone.bat` 独立启动，或双击 `follow-codex.bat` 尝试随 Codex 启动和退出。
4. 如需 EXE，双击 `build.bat`，保留生成的整个 `dist\WhiteDragon` 文件夹。启动脚本会优先使用该 EXE。

跟随模式依赖 Codex 的 Windows 进程名称和安装路径，不能保证识别所有安装方式，也不会自动添加开机启动。额度查询需要本机可发现的 Codex CLI 和匹配的账号；不满足条件时显示不可用。任务状态依赖本地会话日志，远程任务或异常退出可能无法判断。

左键交互和拖动，右键可选择睡眠、动作预览、额度和退出。
