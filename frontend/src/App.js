import { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    // Отправляем всегда, даже пустую строку – бэкенд сам проверит
    const userMessage = { role: "user", content: input || "(пустое сообщение)" };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      let aiContent = "";
      if (data.error) {
        // Если бэкенд вернул ошибку
        aiContent = `❌ Ошибка: ${data.error}`;
      } else {
        // Успешный ответ – показываем текст и длину
        aiContent = `${data.response} (длина: ${data.length} символов)`;
        if (data.count) {
          aiContent +=  `\n📊 ${data.count}`;
        }
      }

      const aiMessage = { role: "ai", content: aiContent };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      const errorMessage = { role: "ai", content: "❌ Не удалось соединиться с сервером" };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInput("");
  };

  const clearChat = async () => {
    try {
      await fetch("http://localhost:8000/reset", { method: "POST" });
    } catch (err) {
      console.error('Не удалось сбросить щетчик ' ,err)
    }
    setMessages([]);
  };

  return (
    <div className="container">
      <div className="chat">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "user" : "ai"}>
            {msg.content}
          </div>
        ))}
      </div>

      <div className="input-box">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напиши сообщение..."
        />
        <button onClick={sendMessage}>Send</button>
        <button onClick={clearChat} >Clear chat full</button>
      </div>
    </div>
  );
}

export default App;