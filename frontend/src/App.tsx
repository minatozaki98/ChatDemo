// frontend/src/App.tsx
import { useState } from "react";
import { sendMessage } from "./api";
import { ChatWindow } from "./components/ChatWindow";
import { InputBar } from "./components/InputBar";
import type { Message } from "./types";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (text: string) => {
    const userMessage: Message = { role: "user", content: text };
    const updated = [...messages, userMessage];
    setMessages(updated);
    setLoading(true);
    setError(null);

    try {
      const reply = await sendMessage(updated);
      setMessages([...updated, { role: "assistant", content: reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen flex-col bg-white">
      <header className="border-b px-6 py-4">
        <h1 className="text-lg font-semibold text-gray-900">ChatDemo</h1>
      </header>
      <ChatWindow messages={messages} />
      {error && (
        <p className="px-4 pb-2 text-center text-sm text-red-500">{error}</p>
      )}
      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
