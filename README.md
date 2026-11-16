# Codex Desktop Pet | 白龙小姐桌面宠物

第三方 Codex 桌面陪伴程序，与 OpenAI 官方 Pets 无关。

![白龙小姐动作与对话演示](docs/demo.gif)

上图额度为模拟数据，不代表真实账户额度。演示图中的文字仅供展示。

## 功能

- 桌面拖动、动作预览、睡眠与唤醒，以及对话气泡。
- 尝试根据本地 Codex 会话事件展示任务状态和结束消息；远程任务和异常退出可能无法准确识别。
- 按需使用本地 Codex app-server 接口查询额度。结果不可用或账号不匹配时不显示数值。
- 提供 Linux 和 Windows 11 启动及打包脚本。Windows 版本尚未在实机验证。

程序读取本机会话记录以检测事件类型，不上传或显示会话内容。请仅在信任本程序的环境运行。

## 运行

- Linux：参见 [Linux 说明](packaging/linux/README.md)，需要 Python 3.10+、PyQt5 和图形桌面。跟随模式目前识别特定 Codex 安装路径。
- Windows 11：参见 [Windows 说明](packaging/windows/README.md)。这是源码运行和构建方案，不包含预编译 EXE。
- 生成两个平台的源码运行包：`python3 packaging/create_packages.py`。生成文件位于 `dist/`。

资源位于 `assets/transparent-v2/`。可在安装 Pillow 后运行 `python3 build_transparent_sprites.py`，从透明版源图重新生成动画帧。

## 调研与致谢

开发过程中曾检索以下相关 GitHub 项目，作为桌宠与透明动画素材方案的调研资料；目前没有证据表明本仓库复制了它们的代码或素材：

- [NewTurn2017/codex-pet-maker](https://github.com/NewTurn2017/codex-pet-maker)：透明动画素材与桌宠制作。
- [jeraldhu-yuan/codex-desktop-sprite](https://github.com/jeraldhu-yuan/codex-desktop-sprite)：桌面编程助手与宠物交互。
- [JosCom/JosCom-pet](https://github.com/JosCom/JosCom-pet)：动画状态与桌宠展示。

角色图像基于用户提供的参考图制作。公开展示不代表对第三方角色或参考图授予额外权利。代码和素材目前未指定开源许可证；如需复用，请先获得权利人许可。
