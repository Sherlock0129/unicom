import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3000";
  const protocol =
    requestHeaders.get("x-forwarded-proto") ??
    (host.startsWith("localhost") || host.startsWith("127.0.0.1") ? "http" : "https");
  const previewImage = `${protocol}://${host}/og.png`;

  return {
    title: "联通智安 · 工业视觉监测平台",
    description: "基于 AI 视觉识别的吊装作业安全帽监测演示系统",
    openGraph: {
      title: "联通智安 · 吊装作业安全监测",
      description: "自动识别吊钩周围未佩戴安全帽人员，并实时发出安全预警。",
      type: "website",
      locale: "zh_CN",
      images: [{ url: previewImage, width: 1536, height: 1024, alt: "联通智安工业视觉监测平台" }],
    },
    twitter: {
      card: "summary_large_image",
      title: "联通智安 · 吊装作业安全监测",
      description: "AI 视觉识别与实时安全预警演示",
      images: [previewImage],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}