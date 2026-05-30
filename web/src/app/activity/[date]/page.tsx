"use client";

import { use } from "react";
import { LoginGate } from "@/components/auth/LoginGate";

export default function ActivityDatePage({ params }: { params: Promise<{ date: string }> }) {
  const { date } = use(params);
  return (
    <LoginGate>
      <div>
        <h1>{date} — 시간대 상세</h1>
        <p style={{ color: "var(--color-text-secondary)" }}>
          Recharts 24h 차트는 Figma 수령 후 ActivityDayChartView로 연결됩니다.
        </p>
      </div>
    </LoginGate>
  );
}
