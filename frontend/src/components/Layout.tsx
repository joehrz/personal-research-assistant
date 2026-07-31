import { NavLink, Outlet } from "react-router-dom";
import {
  Inbox,
  StickyNote,
  CheckSquare,
  CalendarDays,
  FolderKanban,
  BookMarked,
  Sparkles,
  Search,
  Plus,
} from "lucide-react";
import clsx from "clsx";

const NAV = [
  { to: "/", label: "Inbox", icon: Inbox },
  { to: "/notes", label: "Notes", icon: StickyNote },
  { to: "/tasks", label: "Tasks", icon: CheckSquare },
  { to: "/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/sources", label: "Sources", icon: BookMarked },
  { to: "/review", label: "Review", icon: Sparkles },
];

export default function Layout({
  onCapture,
  onSearch,
}: {
  onCapture: () => void;
  onSearch: () => void;
}) {
  return (
    <div className="flex h-full">
      <aside className="w-56 shrink-0 border-r border-ink-800 bg-ink-900 flex flex-col">
        <div className="px-4 py-4 border-b border-ink-800">
          <h1 className="text-sm font-bold tracking-wide text-ink-100">
            Research<span className="text-accent-400"> Assistant</span>
          </h1>
        </div>
        <div className="p-3 space-y-1.5">
          <button
            onClick={onCapture}
            className="w-full flex items-center gap-2 rounded-lg bg-accent-500 hover:bg-accent-400 text-white text-sm font-medium px-3 py-2 transition-colors"
          >
            <Plus size={16} /> Capture
            <kbd className="ml-auto text-[10px] opacity-70 font-mono">C</kbd>
          </button>
          <button
            onClick={onSearch}
            className="w-full flex items-center gap-2 rounded-lg bg-ink-800 hover:bg-ink-700 text-ink-300 text-sm px-3 py-2 transition-colors"
          >
            <Search size={15} /> Search
            <kbd className="ml-auto text-[10px] opacity-70 font-mono">Ctrl K</kbd>
          </button>
        </div>
        <nav className="px-3 py-2 space-y-0.5">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-ink-800 text-ink-100 font-medium"
                    : "text-ink-300 hover:bg-ink-850 hover:text-ink-100",
                )
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-4 py-3 text-[11px] text-ink-500 border-t border-ink-800">
          Local-first · your data stays on disk
        </div>
      </aside>
      <main className="flex-1 min-w-0 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
