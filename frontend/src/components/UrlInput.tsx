import { useState } from "react";

interface UrlInputProps {
  onSubmit: (url: string) => void;
  disabled: boolean;
}

export function UrlInput({ onSubmit, disabled }: UrlInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (trimmed) onSubmit(trimmed);
  };

  return (
    <form className="url-input" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Paste a YouTube video or playlist link…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !value.trim()}>
        Fetch
      </button>
    </form>
  );
}
