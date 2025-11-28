interface SeverityBadgeProps {
  severity: string;
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  const severityLower = severity.toLowerCase();

  let bgColor = "bg-slate-700/50";
  let textColor = "text-slate-300";
  let borderColor = "border-slate-600";

  if (severityLower === "critical") {
    bgColor = "bg-red-900/30";
    textColor = "text-red-400";
    borderColor = "border-red-700";
  } else if (severityLower === "major") {
    bgColor = "bg-orange-900/30";
    textColor = "text-orange-400";
    borderColor = "border-orange-700";
  } else if (severityLower === "minor") {
    bgColor = "bg-yellow-900/30";
    textColor = "text-yellow-400";
    borderColor = "border-yellow-700";
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${bgColor} ${textColor} ${borderColor}`}
    >
      {severity}
    </span>
  );
}
