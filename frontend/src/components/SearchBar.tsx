/**
 * SearchBar — input field and submit button for entering a research question.
 * Disabled while the agent is running to prevent concurrent requests.
 */

import React, { FormEvent, useState } from "react";

interface SearchBarProps {
  onSearch: (question: string) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length >= 5) {
      onSearch(trimmed);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <input
        type="text"
        className="search-input"
        placeholder="Enter a research question, e.g. 'How does RLHF improve LLM alignment?'"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        disabled={isLoading}
        minLength={5}
        maxLength={1000}
        aria-label="Research question"
      />
      <button
        type="submit"
        className="search-button"
        disabled={isLoading || question.trim().length < 5}
        aria-label="Start research"
      >
        {isLoading ? (
          <span className="spinner" aria-hidden="true" />
        ) : (
          "Research"
        )}
      </button>
    </form>
  );
}
