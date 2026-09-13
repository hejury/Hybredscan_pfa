"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { VERDICT_LABELS } from "@/lib/utils";
import type { VerdictBreakdown } from "@/lib/api/dashboard";

const COLORS: Record<keyof VerdictBreakdown, string> = {
  sain: "var(--color-healthy)",
  malveillant: "var(--color-malicious)",
  indetermine: "var(--color-warning)",
};

export function VerdictDonut({ breakdown }: { breakdown: VerdictBreakdown }) {
  const data = (Object.keys(breakdown) as Array<keyof VerdictBreakdown>).map((key) => ({
    key,
    name: VERDICT_LABELS[key],
    value: breakdown[key],
  }));
  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return <p className="py-8 text-center text-sm text-ink-muted">Aucune analyse pour le moment.</p>;
  }

  return (
    <div>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={80} paddingAngle={2}>
              {data.map((d) => (
                <Cell key={d.key} fill={COLORS[d.key]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-2 flex flex-col gap-2">
        {data.map((d) => (
          <li key={d.key} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2 text-ink-secondary">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[d.key] }} />
              {d.name}
            </span>
            <span className="font-bold text-ink">{d.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
