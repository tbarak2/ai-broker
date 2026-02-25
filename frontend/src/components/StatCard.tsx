import clsx from "clsx";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  className?: string;
}

export default function StatCard({ label, value, sub, trend, className }: StatCardProps) {
  return (
    <div className={clsx("card", className)}>
      <p className="text-sm text-gray-400 mb-1">{label}</p>
      <p
        className={clsx("text-2xl font-bold", {
          "text-green-400": trend === "up",
          "text-red-400": trend === "down",
          "text-white": trend === "neutral" || !trend,
        })}
      >
        {value}
      </p>
      {sub && <p className="text-sm text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}
