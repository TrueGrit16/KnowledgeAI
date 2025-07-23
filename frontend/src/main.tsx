// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import Chat from "./components/Chat";   // or `App` if it wraps Chat
import "./styles/index.css";

// One root, one render call
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Chat />
  </React.StrictMode>,
);