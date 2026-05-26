/**
 * ResearchReport — renders the final verified markdown research report.
 * Confidence badges [HIGH], [MEDIUM], [LOW] are rendered as styled inline chips.
 * Uses react-markdown + remark-gfm for full GitHub-flavored markdown support.
 */

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

interface ResearchReportProps {
  report: string;
}

/** Replace confidence label text with styled badge spans. */
function insertConfidenceBadges(text: string): React.ReactNode[] {
  const parts = text.split(/(\[HIGH\]|\[MEDIUM\]|\[LOW\])/g);
  return parts.map((part, i) => {
    if (part === "[HIGH]") {
      return (
        <span key={i} className="badge badge-high" title="High confidence">
          HIGH
        </span>
      );
    }
    if (part === "[MEDIUM]") {
      return (
        <span key={i} className="badge badge-medium" title="Medium confidence">
          MED
        </span>
      );
    }
    if (part === "[LOW]") {
      return (
        <span key={i} className="badge badge-low" title="Low confidence">
          LOW
        </span>
      );
    }
    return part;
  });
}

/** Custom renderers so confidence badges appear inside paragraphs and list items. */
const markdownComponents: Components = {
  p({ children }) {
    const processChild = (child: React.ReactNode): React.ReactNode => {
      if (typeof child === "string") {
        return insertConfidenceBadges(child);
      }
      return child;
    };

    const processed = React.Children.map(children, processChild);
    return <p>{processed}</p>;
  },
  li({ children }) {
    const processChild = (child: React.ReactNode): React.ReactNode => {
      if (typeof child === "string") {
        return insertConfidenceBadges(child);
      }
      return child;
    };

    const processed = React.Children.map(children, processChild);
    return <li>{processed}</li>;
  },
};

export default function ResearchReport({ report }: ResearchReportProps) {
  if (!report) return null;

  return (
    <article className="research-report">
      <h1 className="report-title">Research Report</h1>
      <div className="report-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={markdownComponents}
        >
          {report}
        </ReactMarkdown>
      </div>
    </article>
  );
}
