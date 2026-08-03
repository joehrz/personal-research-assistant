import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router";
import App from "./App";
import "./index.css";

// Forward uncaught frontend errors to the backend log file so crashes during
// real use leave a trace in <data_dir>/logs/pra.log.
export function reportClientError(message: string, context = "") {
  try {
    void fetch("/api/logs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level: "error", message: message.slice(0, 4000), context }),
    }).catch(() => {});
  } catch {
    /* never let logging itself throw */
  }
}

window.addEventListener("error", (e) =>
  reportClientError(`window.onerror: ${e.message}`, `${e.filename}:${e.lineno}:${e.colno}`),
);
window.addEventListener("unhandledrejection", (e) =>
  reportClientError(`unhandledrejection: ${String(e.reason).slice(0, 1000)}`),
);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HashRouter>
      <App />
    </HashRouter>
  </StrictMode>,
);

// PWA install support (skipped in dev where sw.js isn't served from root)
if ("serviceWorker" in navigator && !import.meta.env.DEV) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  });
}
