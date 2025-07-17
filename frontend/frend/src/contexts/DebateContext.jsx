// src/contexts/DebateContext.jsx
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

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      wsRef.current = new WebSocket('ws://localhost:8000/ws/debate');
    }

    wsRef.current.onopen = () => {
      wsRef.current.send(JSON.stringify({ action: 'start_debate', topic: newTopic, rounds: 3 }));
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'round_update') {
        setTranscript((prev) => [...prev, message.data]);
      } else if (message.type === 'verdict') {
        setVerdict(message.data.verdict);
        setIsDebating(false);
      } else if (message.type === 'error') {
        setError(message.message);
        setIsDebating(false);
      }
    };

    wsRef.current.onerror = () => {
      setError('WebSocket error');
      setIsDebating(false);
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
