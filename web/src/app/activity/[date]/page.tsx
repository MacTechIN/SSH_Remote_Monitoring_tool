import { ActivityDateClient } from "./ActivityDateClient";

export function generateStaticParams() {
  const params: { date: string }[] = [];
  const today = new Date();
  for (let i = 0; i < 400; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    params.push({ date: d.toISOString().slice(0, 10) });
  }
  return params;
}

export default async function ActivityDatePage({
  params,
}: {
  params: Promise<{ date: string }>;
}) {
  const { date } = await params;
  return <ActivityDateClient date={date} />;
}
