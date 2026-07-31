import { useEffect, useState } from "react";
import { Route, Routes, useSearchParams } from "react-router-dom";
import Layout from "./components/Layout";
import CommandPalette from "./components/CommandPalette";
import QuickCapture from "./components/QuickCapture";
import InboxView from "./views/InboxView";
import NotesView from "./views/NotesView";
import TasksView from "./views/TasksView";
import CalendarView from "./views/CalendarView";
import ProjectsView from "./views/ProjectsView";
import SourcesView from "./views/SourcesView";
import ReviewView from "./views/ReviewView";
import MobileCaptureView from "./views/MobileCaptureView";

export default function App() {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [captureOpen, setCaptureOpen] = useState(false);
  const [searchParams] = useSearchParams();

  // The desktop shell opens the app with ?capture=1 from the global hotkey.
  useEffect(() => {
    if (searchParams.get("capture") === "1") setCaptureOpen(true);
  }, [searchParams]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      const typing =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      } else if (!typing && e.key === "c" && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        setCaptureOpen(true);
      } else if (e.key === "Escape") {
        setPaletteOpen(false);
        setCaptureOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <Routes>
        <Route path="capture" element={<MobileCaptureView />} />
        <Route element={<Layout onCapture={() => setCaptureOpen(true)} onSearch={() => setPaletteOpen(true)} />}>
          <Route index element={<InboxView />} />
          <Route path="notes" element={<NotesView />} />
          <Route path="notes/:noteId" element={<NotesView />} />
          <Route path="tasks" element={<TasksView />} />
          <Route path="calendar" element={<CalendarView />} />
          <Route path="projects" element={<ProjectsView />} />
          <Route path="sources" element={<SourcesView />} />
          <Route path="review" element={<ReviewView />} />
        </Route>
      </Routes>
      {paletteOpen && <CommandPalette onClose={() => setPaletteOpen(false)} />}
      {captureOpen && <QuickCapture onClose={() => setCaptureOpen(false)} />}
    </>
  );
}
