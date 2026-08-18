# 联通智安网页演示

这是工厂吊装区域安全帽监测项目的 Web 展示层，使用 React、TypeScript 和 Vinext/Vite 构建，采用中国联通红白配色。

## 快速启动

推荐回到项目根目录，双击：

```text
start_web_demo.bat
```

或在 PowerShell 中执行：

```powershell
.\scripts\start_web_demo.ps1
```

脚本会检查依赖和服务状态，后台启动网页，并自动打开 <http://localhost:3000>。

手动启动方式：

```powershell
cd web-demo
npm install
npm run dev
```

## 页面能力

- 播放 1 分钟 H.264 检测结果视频；
- 按 `events.json` 中的时间区间同步显示红色高风险告警；
- 展示吊钩危险区、安全帽状态、模型置信度和事件时间线；
- 支持提示音、浏览器系统通知、告警跳转与人工确认；
- 支持桌面和窄屏布局；
- 提供中文告警字幕和键盘可访问控件。

网页只负责结果展示，YOLO 推理由根目录下的 Python 脚本完成。重新生成告警数据：

```powershell
C:\Python\Python312\python.exe scripts\analyze_hook_safety.py `
  --model models\best.pt `
  --source data\raw_videos\demo_video.mp4 `
  --output web-demo\public\events.json
```

## 关键文件

- `app/page.tsx`：视频同步、告警状态、通知和事件交互；
- `app/globals.css`：红白主题与响应式布局；
- `app/layout.tsx`：页面及社交分享元数据；
- `public/demo_result.mp4`：约 11.8 MB 的 H.264 演示视频；
- `public/events.json`：4 个候选告警事件；
- `public/captions-zh.vtt`：中文告警字幕。

## 质量检查

```powershell
npm run lint
npm run build
npm audit --omit=dev
```

当前生产依赖安全检查为 0 个已知漏洞。完整模型指标、数据集构成、演示结果和局限性请查看项目根目录的 `README.md`。