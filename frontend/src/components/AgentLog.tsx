/**
 * AgentLog — scrolling real-time log of streaming agent events.
 * Auto-scrolls to the bottom as new events arrive.
 * Each event type has distinct visual styling.
 */

import React, { useEffect, useRef } from "react";
import type { AgentEvent } from "../services/websocket";

interface AgentLogProps {
  events: AgentEvent[];
}

/** Maps event types to CSS class names for styling. */
const EVENT_CLASS: Record<string, string> = {
  thinking: "log-thinking",
  tool_call: "log-tool-call",
  result: "log-result",
  report: "log-report",
  error: "log-error",
  done: "log-done",
};

/** Human-readable prefix labels for each event type. */
const EVENT_LABEL: Record<string, string> = {
  thinking: "Thinking",
  tool_call: "Tool Call",
  result: "Result",
  report: "Report Ready",
  error: "Error",
  done: "Done",
};

export default function AgentLog({ events }: AgentLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest event whenever the list grows
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) return null;

  return (
    <aside className="agent-log">
      <h2 className="log-header">Agent Activity</h2>
      <div className="log-body">
        {events.map((event, idx) => (
          <div
            key={idx}
            className={`log-entry ${EVENT_CLASS[event.type] ?? ""}`}
          >
            <span className="log-label">[{EVENT_LABEL[event.type] ?? event.type}]</span>
            <span className="log-message">{event.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </aside>
  );
}
