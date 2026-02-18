"use client";

interface StatCardProps {
  label: string;
  value: string;
  subtitle: string;
  color: string;
}

export function StatCard({ label, value, subtitle, color }: StatCardProps) {
  return (
    <div className="rounded-xl border border-[#162638] bg-[#060d14]/50 p-6 text-center">
      <p className="font-[family-name:var(--font-space-mono)] text-[10px] uppercase tracking-wider text-[#e8f4ff]/30">
        {label}
      </p>
      <p
        className="mt-2 font-[family-name:var(--font-syne)] text-4xl font-extrabold"
        style={{ color }}
      >
        {value}
      </p>
      <p className="mt-2 font-[family-name:var(--font-crimson-pro)] text-xs text-[#e8f4ff]/40 leading-relaxed">
        {subtitle}
      </p>
    </div>
  );
}
