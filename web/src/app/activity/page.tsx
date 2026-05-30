"use client";

import { LoginGate } from "@/components/auth/LoginGate";
import { ActivityHeatmapContainer } from "@/components/features/ActivityHeatmap/ActivityHeatmapContainer";

export default function ActivityPage() {
  return (
    <LoginGate>
      <ActivityHeatmapContainer />
    </LoginGate>
  );
}
