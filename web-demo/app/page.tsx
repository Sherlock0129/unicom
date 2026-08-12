"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type AlarmEvent = {
  id: string;
  start: number;
  end: number;
  level: "high";
  title: string;
  location: string;
  confidence: number;
  hookConfidence: number;
};

type EventPayload = {
  camera: string;
  duration: number;
  rule: { name: string; minDurationSeconds: number };
  events: AlarmEvent[];
};

const FALLBACK_EVENTS: AlarmEvent[] = [
  { id: "ALM-001", start: 11.4, end: 40, level: "high", title: "吊钩作业区未佩戴安全帽", location: "一号吊装作业区", confidence: 0.93, hookConfidence: 0.91 },
  { id: "ALM-002", start: 48.2, end: 49.2, level: "high", title: "吊钩作业区未佩戴安全帽", location: "一号吊装作业区", confidence: 0.84, hookConfidence: 0.84 },
  { id: "ALM-003", start: 52.6, end: 59.8, level: "high", title: "吊钩作业区未佩戴安全帽", location: "一号吊装作业区", confidence: 0.94, hookConfidence: 0.89 },
];

function formatTime(value: number) {
  const minutes = Math.floor(value / 60).toString().padStart(2, "0");
  const seconds = Math.floor(value % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function LogoMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <i /><i /><i /><i />
    </span>
  );
}

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const lastAlertRef = useRef<string | null>(null);
  const [events, setEvents] = useState<AlarmEvent[]>(FALLBACK_EVENTS);
  const [currentTime, setCurrentTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [notifications, setNotifications] = useState(false);
  const [acknowledged, setAcknowledged] = useState<string[]>([]);

  useEffect(() => {
    fetch("/events.json")
      .then((response) => response.json())
      .then((payload: EventPayload) => setEvents(payload.events.filter((event) => event.start > 1)))
      .catch(() => setEvents(FALLBACK_EVENTS));
  }, []);

  const activeEvent = useMemo(
    () => events.find((event) => currentTime >= event.start && currentTime <= event.end),
    [currentTime, events],
  );

  const visibleEvents = useMemo(
    () => [...events].filter((event) => event.start <= currentTime + 0.25).reverse(),
    [currentTime, events],
  );

  useEffect(() => {
    if (!activeEvent || lastAlertRef.current === activeEvent.id) return;
    lastAlertRef.current = activeEvent.id;

    if (notifications && "Notification" in window && Notification.permission === "granted") {
      new Notification("联通智安 · 高风险告警", {
        body: `${activeEvent.location}检测到未佩戴安全帽人员，请立即处置。`,
      });
    }

    if (!muted) {
      const audio = new AudioContext();
      const oscillator = audio.createOscillator();
      const gain = audio.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(760, audio.currentTime);
      gain.gain.setValueAtTime(0.0001, audio.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.11, audio.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.45);
      oscillator.connect(gain).connect(audio.destination);
      oscillator.start();
      oscillator.stop(audio.currentTime + 0.48);
    }
  }, [activeEvent, muted, notifications]);

  async function enableNotifications() {
    if (!("Notification" in window)) return;
    const permission = await Notification.requestPermission();
    setNotifications(permission === "granted");
  }

  function seekTo(time: number) {
    if (!videoRef.current) return;
    videoRef.current.currentTime = time;
    videoRef.current.play();
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <LogoMark />
          <div>
            <strong>中国联通</strong>
            <span>联通智安 · 工业视觉监测平台</span>
          </div>
        </div>
        <div className="top-actions">
          <div className="system-pill"><b />系统运行正常</div>
          <div className="clock">2026-08-12 <strong>09:42:18</strong></div>
          <button className="icon-button" onClick={() => setMuted((value) => !value)} aria-label={muted ? "打开告警音" : "关闭告警音"}>
            {muted ? "静音" : "告警音"}
          </button>
          <button className={`notify-button ${notifications ? "enabled" : ""}`} onClick={enableNotifications}>
            {notifications ? "通知已开启" : "开启系统通知"}
          </button>
        </div>
      </header>

      <section className="page-heading">
        <div>
          <p className="eyebrow">SAFETY VISION / LIVE</p>
          <h1>吊装作业安全监测</h1>
          <p>实时识别吊钩危险区内的人员与安全帽佩戴状态</p>
        </div>
        <div className="camera-select">
          <span>当前监控点</span>
          <strong>一号吊装作业区 · CAM-01</strong>
          <i>在线</i>
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="primary-column">
          <div className={`video-card ${activeEvent ? "is-alert" : ""}`}>
            <div className="video-head">
              <div><span className="live-dot" />LIVE <b>CAM-01</b></div>
              <div>模型 YOLO11n-v2 · 25 FPS · 1920×1080</div>
            </div>
            <div className="video-stage">
              <video
                ref={videoRef}
                src="/demo_result.mp4"
                playsInline
                onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onEnded={() => setPlaying(false)}
              >
                <track kind="captions" src="/captions-zh.vtt" srcLang="zh-CN" label="中文告警字幕" default />
              </video>
              <div className="danger-zone">
                <span>吊钩危险区</span>
                <i className="corner tl" /><i className="corner tr" /><i className="corner bl" /><i className="corner br" />
              </div>
              <div className={`alert-banner ${activeEvent ? "visible" : ""}`}>
                <span className="warning-icon">!</span>
                <div>
                  <strong>高风险 · 未佩戴安全帽</strong>
                  <p>吊钩作业区检测到违规人员，请立即停止危险区域作业</p>
                </div>
                <span className="alert-confidence">置信度 {Math.round((activeEvent?.confidence ?? 0) * 100)}%</span>
              </div>
              {!playing && (
                <button className="play-overlay" onClick={() => videoRef.current?.play()} aria-label="播放演示视频">
                  <span>▶</span><b>开始安全监测演示</b>
                </button>
              )}
            </div>
            <div className="video-controls">
              <button onClick={() => playing ? videoRef.current?.pause() : videoRef.current?.play()}>{playing ? "暂停" : "播放"}</button>
              <span>{formatTime(currentTime)} / 01:00</span>
              <input
                aria-label="视频进度"
                type="range"
                min="0"
                max="60"
                step="0.1"
                value={currentTime}
                onChange={(event) => seekTo(Number(event.target.value))}
              />
              <button onClick={() => seekTo(11.4)}>跳至告警</button>
            </div>
          </div>

          <div className="metric-row">
            <article><div className="metric-icon red">人</div><div><span>当前人员</span><strong>7</strong><small>作业区内实时检测</small></div></article>
            <article><div className="metric-icon green">帽</div><div><span>佩戴安全帽</span><strong>3</strong><small>合规人员</small></div></article>
            <article className={activeEvent ? "metric-alert" : ""}><div className="metric-icon orange">!</div><div><span>未佩戴</span><strong>{activeEvent ? "1" : "0"}</strong><small>{activeEvent ? "需要立即处置" : "当前无持续违规"}</small></div></article>
            <article><div className="metric-icon blue">钩</div><div><span>吊钩状态</span><strong className="word">作业中</strong><small>危险区规则已启用</small></div></article>
          </div>
        </div>

        <aside className="side-column">
          <section className={`status-card ${activeEvent ? "alert" : "safe"}`}>
            <div className="status-symbol">{activeEvent ? "!" : "✓"}</div>
            <div><span>当前安全状态</span><strong>{activeEvent ? "发现高风险行为" : "作业区状态正常"}</strong><p>{activeEvent ? "吊钩危险区内存在未佩戴安全帽人员" : "未发现持续违规事件"}</p></div>
          </section>

          <section className="rule-card">
            <div className="section-title"><div><span>ACTIVE RULE</span><h2>安全规则</h2></div><i>运行中</i></div>
            <div className="rule-visual">
              <div className="hook-line"><span /></div>
              <div className="rule-zone"><b>必须佩戴安全帽</b><small>吊钩下方及周边危险区域</small></div>
            </div>
            <ul>
              <li><b>触发条件</b><span>危险区内检测到 no_helmet</span></li>
              <li><b>持续时间</b><span>≥ 0.8 秒</span></li>
              <li><b>告警方式</b><span>界面 / 声音 / 系统通知</span></li>
            </ul>
          </section>

          <section className="event-card">
            <div className="section-title"><div><span>EVENT STREAM</span><h2>实时事件</h2></div><button onClick={() => seekTo(0)}>清屏重播</button></div>
            <div className="event-list">
              {visibleEvents.length === 0 ? (
                <div className="empty-events"><span>✓</span><p>暂无告警事件</p><small>系统正在持续分析画面</small></div>
              ) : visibleEvents.map((event) => {
                const isAck = acknowledged.includes(event.id);
                return (
                  <article key={event.id} className={activeEvent?.id === event.id ? "active" : ""}>
                    <div className="event-severity">高</div>
                    <button className="event-copy" onClick={() => seekTo(event.start)} aria-label={`跳转至 ${formatTime(event.start)} 的告警`}>
                      <strong>{event.title}</strong>
                      <span>{event.location} · {formatTime(event.start)}</span>
                      <small>人员置信度 {Math.round(event.confidence * 100)}% · 吊钩 {Math.round(event.hookConfidence * 100)}%</small>
                    </button>
                    <button
                      className={isAck ? "acknowledged" : ""}
                      onClick={(clickEvent) => {
                        clickEvent.stopPropagation();
                        setAcknowledged((items) => items.includes(event.id) ? items : [...items, event.id]);
                      }}
                    >{isAck ? "已确认" : "确认"}</button>
                  </article>
                );
              })}
            </div>
          </section>
        </aside>
      </section>

      <footer>
        <span>中国联通工业互联网 · AI 安全生产演示系统</span>
        <span>边缘节点：在线 · 模型延迟：25.8 ms · 数据仅用于演示</span>
      </footer>
    </main>
  );
}
