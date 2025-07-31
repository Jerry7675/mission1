
import React, { createContext, useContext, useState, useRef } from 'react';

const DebateContext = createContext();

export const DebateProvider = ({ children }) => {
  const [isDebating, setIsDebating] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [verdict, setVerdict] = useState('');
  const [topic, setTopic] = useState('');
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('user');

  const wsRef = useRef(null);

const setDebateTopic = (newTopic) => {
  if (!newTopic) return;
  setTranscript([]);
  setVerdict('');
  setIsDebating(true);
  setTopic(newTopic);
  setError(null); 

  // Create new WebSocket
  const ws = new WebSocket('ws://localhost:8000/ws/debate');
  wsRef.current = ws;

  // When connected
  ws.onopen = () => {
    console.log("WebSocket connected");
    ws.send(JSON.stringify({ action: 'start_debate', topic: newTopic, rounds: 5 }));
  };

  // Handle messages
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'round_update') {
      setTranscript((prev) => [...prev, message.data]);
    } else if (message.type === 'verdict') {
      setVerdict(message.data.verdict);
      setIsDebating(false);
      ws.close();
    } else if (message.type === 'error') {
      setError(message.message);
      setIsDebating(false);
      ws.close();
    }
  };

  ws.onerror = (err) => {
    console.error("WebSocket error", err);
    setError('WebSocket error occurred.');
    setIsDebating(false);
  };

  ws.onclose = () => {
    console.log("WebSocket closed");
  };
};


  return (
    <DebateContext.Provider
      value={{
        setDebateTopic,
        isDebating,
        transcript,
        verdict,
        topic,
        error,
        mode,
        setMode
      }}
    >
      {children}
    </DebateContext.Provider>
  );
};

export const useDebate = () => useContext(DebateContext);
