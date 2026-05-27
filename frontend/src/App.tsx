/**
 * App — root component that orchestrates the research UI.
 *
 * Layout:
 *   - Header with branding
 *   - SearchBar (always visible; disabled while running)
 *   - Two-column body (agent log sidebar + report content area)
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import AgentLog from "./components/AgentLog";
import ResearchReport from "./components/ResearchReport";
import SearchBar from "./components/SearchBar";
import {
  AgentEvent,
  ResearchWebSocket,
} from "./services/websocket";
import "./index.css";

type AppState = "idle" | "running" | "done" | "error";

export default function App() {
  const [appState, setAppState] = useState<AppState>("idle");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [report, setReport] = useState<string>("");
  // Holds the question that triggers the WebSocket effect.
  // Changing this value is the only way to start a new connection.
  const [activeQuestion, setActiveQuestion] = useState<string | null>(null);
  // Stable ref so the effect's callbacks always see current state setters
  // without needing them as effect dependencies.
  const appStateRef = useRef(appState);
  appStateRef.current = appState;

  // One WebSocket per activeQuestion. useEffect cleanup stops the previous
  // socket before opening a new one, so StrictMode double-invocation and
  // rapid re-searches never produce more than one live connection.
  useEffect(() => {
    if (!activeQuestion) return;

    const ws = new ResearchWebSocket({
      onEvent(event: AgentEvent) {
        setEvents((prev) => [...prev, event]);

        if (event.type === "report") {
          const data = event.data as { report?: string } | undefined;
          if (data?.report) {
            setReport(data.report);
          }
        }

        if (event.type === "done") {
          setAppState("done");
        }

        if (event.type === "error") {
          setAppState("error");
        }
      },
      onClose() {
        // Only flip to "done" if we're still actively running (not already
        // transitioned to "done" or "error" via an explicit event).
        setAppState((prev) => (prev === "running" ? "done" : prev));
      },
      onError() {
        setEvents((prev) => [
          ...prev,
          { type: "error", message: "WebSocket connection error." },
        ]);
        setAppState("error");
      },
    });

    ws.start(activeQuestion);

    // Cleanup: called by React before re-running the effect or on unmount.
    return () => {
      ws.stop();
    };
  }, [activeQuestion]);

  const handleSearch = useCallback((question: string) => {
    // Reset UI state before the effect fires the new connection.
    setEvents([]);
    setReport("");
    setAppState("running");
    // Setting a new question value triggers the effect above.
    // If the user submits the same question twice, append a timestamp so
    // the effect dependency actually changes and re-runs.
    setActiveQuestion((prev) =>
      prev === question ? `${question} ` : question
    );
  }, []);

  const isLoading = appState === "running";
  // Show the two-column layout as soon as a search is in progress or complete,
  // even before the first event arrives so the log panel is immediately visible.
  const showLog = appState !== "idle";
  const showReport = Boolean(report);

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-inner">
          <span className="header-logo" aria-hidden="true">
            &#128269;
          </span>
          <div>
            <h1 className="header-title">Research Assistant</h1>
            <p className="header-subtitle">
              AI-powered academic research with real-time synthesis
            </p>
          </div>
        </div>
      </header>

      {/* ── Search Bar ─────────────────────────────────────────── */}
      <main className="app-main">
        <section className="search-section">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
          {appState === "running" && (
            <p className="status-text">
              Researching&hellip; this may take 30–90 seconds.
            </p>
          )}
          {appState === "error" && (
            <p className="status-text status-error">
              An error occurred. See the agent log for details.
            </p>
          )}
        </section>

        {/* ── Two-column body ────────────────────────────────── */}
        {showLog && (
          <div className="content-layout">
            {/* Sidebar: agent log */}
            <AgentLog events={events} />

            {/* Main: report */}
            <div className="report-area">
              {showReport ? (
                <ResearchReport report={report} />
              ) : (
                <div className="report-placeholder">
                  <div className="placeholder-icon" aria-hidden="true">
                    &#128196;
                  </div>
                  <p>The research report will appear here when ready.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Empty state ────────────────────────────────────── */}
        {!showLog && appState === "idle" && (
          <div className="empty-state">
            <div className="empty-icon" aria-hidden="true">
              &#128300;
            </div>
            <h2>Ask a research question</h2>
            <p>
              The agent will search ArXiv, retrieve relevant paper sections,
              synthesize a report, and verify every claim.
            </p>
            <ul className="example-questions">
              <li>How does RLHF improve alignment in large language models?</li>
              <li>What are the latest advances in diffusion model architectures?</li>
              <li>How do graph neural networks handle heterogeneous data?</li>
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}
