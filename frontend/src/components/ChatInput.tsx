import React, { useState } from "react";

interface Props {
  onSend: (msg: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<Props> = ({ onSend, disabled }) => {
  const [value, setValue] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex gap-2 border-t border-gray-200 dark:border-gray-700 p-3 bg-white dark:bg-gray-800"
    >
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Ask something…"
        className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none"
        disabled={disabled}
      />
      <button
        disabled={disabled}
        className="bg-brand-primary disabled:opacity-40 text-white rounded px-4 py-1 text-sm"
      >
        Send
      </button>
    </form>
  );
};
export default ChatInput;