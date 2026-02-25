import { NavLink, Outlet } from "react-router-dom";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/portfolio", label: "Portfolio", icon: "💼" },
  { to: "/advisor", label: "AI Advisor", icon: "🤖" },
  { to: "/trades", label: "Trades", icon: "📋" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Layout() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-lg font-bold text-white">
            🤖 AI Broker
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">Paper Trading Simulator</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                )
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800 text-xs text-gray-600">
          Paper trading only — no real money
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
