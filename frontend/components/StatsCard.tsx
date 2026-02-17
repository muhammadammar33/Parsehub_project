import { ReactNode } from "react";

interface StatsCardProps {
  title: string;
  value: number;
  icon: ReactNode;
  color: string;
}

export default function StatsCard({
  title,
  value,
  icon,
  color,
}: StatsCardProps) {
  const colorClasses = {
    "bg-blue-500": "from-blue-500 to-blue-600 shadow-blue-500/25",
    "bg-green-500": "from-emerald-500 to-emerald-600 shadow-emerald-500/25",
    "bg-yellow-500": "from-amber-500 to-amber-600 shadow-amber-500/25",
    "bg-purple-500": "from-purple-500 to-purple-600 shadow-purple-500/25",
  };

  const gradientClass =
    colorClasses[color as keyof typeof colorClasses] ||
    "from-slate-500 to-slate-600";

  return (
    <div className="group relative bg-gradient-to-br from-slate-800 to-slate-800/50 backdrop-blur-sm rounded-xl p-6 border border-slate-700/50 hover:border-slate-600/50 transition-all duration-300 hover:shadow-xl hover:shadow-slate-900/50 overflow-hidden">
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-slate-900/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

      <div className="relative flex items-center justify-between">
        <div className="flex-1">
          <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
            {title}
          </p>
          <p className="text-4xl font-bold text-white mt-1 bg-gradient-to-br from-white to-slate-300 bg-clip-text text-transparent">
            {value.toLocaleString()}
          </p>
        </div>
        <div
          className={`bg-gradient-to-br ${gradientClass} p-4 rounded-xl text-white shadow-lg transform group-hover:scale-110 transition-transform duration-300`}
        >
          {icon}
        </div>
      </div>

      {/* Bottom accent line */}
      <div
        className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${gradientClass} transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300`}
      ></div>
    </div>
  );
}
