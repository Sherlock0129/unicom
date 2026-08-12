# 联通智安 · 吊装作业安全监测 Demo

这是对现有 YOLO11n 检测结果进行包装的演示网页，采用中国联通红白配色。页面播放已经完成识别标注的监控视频，并根据吊钩危险区规则展示实时告警。

## 安全规则

- 吊钩下方及周边区域必须佩戴安全帽。
- 同一帧中同时检测到 `hook` 与其危险区域内的 `no_helmet` 时，记为违规候选。
- 违规持续至少 0.8 秒后生成高风险事件，避免单帧误检造成频繁告警。
- 告警方式包括页面红色提示、提示音、浏览器系统通知和事件记录。

## 启动演示网页

需要 Node.js 22.13 或更高版本。在项目根目录执行：

```powershell
cd web-demo
npm install
npm run dev
```

然后访问 <http://localhost:3000>。首次使用系统通知时，点击页面右上角“开启通知”并在浏览器中允许通知权限。

## 生产构建

```powershell
cd web-demo
npm run lint
npm run build
```

## 重新分析演示视频

在项目根目录执行：

```powershell
C:\Python\Python312\python.exe scripts\analyze_hook_safety.py `
  --model models\best.pt `
  --source data\raw_videos\demo_video.mp4 `
  --output web-demo\public\events.json
```

常用规则参数：

- `--horizontal 420`：吊钩左右方向危险区半径（像素）。
- `--vertical 780`：吊钩下方危险区长度（像素）。
- `--min-duration 0.8`：生成告警前的最短持续时间（秒）。
- `--merge-gap 0.8`：允许合并的短暂漏检间隔（秒）。
- `--conf 0.20`：模型最低置信度。

## 主要文件

- `app/page.tsx`：监控大屏交互、视频同步、通知和告警事件。
- `app/globals.css`：中国联通红白主题及响应式布局。
- `public/demo_result.mp4`：H.264 网页版演示视频。
- `public/events.json`：模型分析得到的告警时间段。
- `../scripts/analyze_hook_safety.py`：吊钩危险区事件分析脚本。

> 当前规则采用固定像素范围，适合本项目固定机位 Demo。实际部署时建议把危险区改为按画面比例或多边形 ROI 配置。