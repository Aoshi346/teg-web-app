interface BadgeProps {
  label: string;
  tone?: "neutral" | "warning" | "success";
}

const TONES = {
  neutral: "bg-slate-100 text-slate-700",
  warning: "bg-amber-100 text-amber-800",
  success: "bg-emerald-100 text-emerald-800",
};

export function Badge({ label, tone = "warning" }: BadgeProps) {
  return <span className={`rounded px-2 py-0.5 text-xs ${TONES[tone]}`}>{label}</span>;
}
