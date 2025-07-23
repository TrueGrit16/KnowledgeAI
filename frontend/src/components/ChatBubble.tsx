import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from 'remark-gfm';

interface Props {
  role: "user" | "assistant" | "error";
  content: string;
}

const ChatBubble: React.FC<Props> = ({ role, content }) => {
  const base =
    "max-w-lg rounded-lg px-4 py-3 text-sm whitespace-pre-wrap leading-relaxed";
  const scheme = {
    user: "bg-primary text-white ml-auto",
    assistant: "bg-white dark:bg-gray-800 dark:text-gray-100 border border-gray-200 dark:border-gray-700",
    error:
      "bg-red-50 border border-red-300 text-red-800 dark:bg-red-900 dark:text-red-100 ml-auto"
  }[role];

  return (
    <div className={`${base} ${scheme} shadow-sm`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        className="prose prose-invert max-w-none"
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
export default ChatBubble;