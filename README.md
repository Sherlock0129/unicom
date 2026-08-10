# Factory Helmet Detection Demo

一个基于 Ultralytics YOLO 和 OpenCV 的工厂安全帽检测 Demo。程序支持视频文件、USB 摄像头和 RTSP 视频流，并仅对指定多边形区域内的人员执行安全帽规则。

## 1. 环境安装

项目使用 Python 3.10 或 3.11。PyTorch 需要根据本机 CPU/CUDA 环境单独安装；其余依赖运行：

```powershell
python -m pip install -r requirements.txt
```

## 2. 准备模型与视频

将训练好的安全帽检测权重放到：

```text
models/best.pt
```

模型类别名称建议为：

```text
person
helmet
no_helmet
```

如果类别名称不同，请修改 `configs/app.yaml` 中的 `classes` 映射。

将测试视频放到：

```text
data/input/demo.mp4
```

也可以在 `configs/app.yaml` 中把 `video.source` 改为摄像头编号 `0` 或 RTSP 地址。

## 3. 选择检测区域

运行：

```powershell
python -m scripts.select_region --source data/input/demo.mp4
```

在画面中左键添加顶点，按 `S` 保存到 `configs/regions.json`，按 `R` 清空重画，按 `Q` 退出。

## 4. 运行 Demo

```powershell
python -m app.main
```

运行窗口中按 `Q` 退出。违规截图和 JSON Lines 事件记录保存在 `runtime/alarms/`。

## 5. PyCharm 配置

创建 Python Run Configuration：

- Module name: `app.main`
- Working directory: 项目根目录 `unicom`
- Interpreter: 已安装 PyTorch 和 requirements 的虚拟环境

## 规则说明

- 使用人体框底边中心点判断人员是否位于多边形区域内。
- 在人体框顶部一定比例内匹配 `helmet` 或 `no_helmet` 检测框。
- 同一个跟踪 ID 连续未戴安全帽达到配置时长后才告警。
- 每次违规只生成一次告警，恢复佩戴或离开区域一段时间后解除状态。

