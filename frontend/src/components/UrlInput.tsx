import { useState } from "react";

const STYLES = {
  form: "flex gap-2.5 mb-6 max-w-xl mx-auto",
  input: "flex-1 min-w-0 bg-surface border border-border text-text text-sm px-3 py-2.5 rounded-lg placeholder:text-text-muted focus:outline-2 focus:outline-accent focus:outline-offset-1 disabled:opacity-40 disabled:cursor-not-allowed",
  pasteBtn: "bg-transparent border border-border text-text-muted text-sm font-medium px-4 py-2.5 rounded-lg transition-colors hover:border-accent hover:text-accent disabled:opacity-40 disabled:cursor-not-allowed",
  submitBtn: "bg-accent text-white text-sm font-medium px-4 py-2.5 rounded-lg transition-colors hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed",
};

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

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) setValue(text.trim());
    } catch {
      // Clipboard access denied or unavailable; user can still paste manually.
    }
  };

  return (
    <form className={STYLES.form} onSubmit={handleSubmit}>
      <input
        type="text"
        className={STYLES.input}
        placeholder="Paste a YouTube or Spotify link…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
      />
      <button
        type="button"
        className={STYLES.pasteBtn}
        onClick={handlePaste}
        disabled={disabled}
      >
        Paste
      </button>
      <button type="submit" className={STYLES.submitBtn} disabled={disabled || !value.trim()}>
        Load
      </button>
    </form>
  );
}
