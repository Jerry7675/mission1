import { useState, useEffect, useRef } from 'react';
import { DebateContext } from './contexts/DebateContext';
import  TopicSelector  from './components/TopicSelector';
import  DebateUi  from './components/DebateUi';
import  AudioRecorder  from './components/AudioRecorder';
import './App.css';
import React from 'react';

function App() {
  const [isDebating, setIsDebating] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [verdict, setVerdict] = useState('');
  const [topic, setTopic] = useState('');
  const [error, setError] = useState(null);

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

    wsRef.current.onerror = (err) => {
      setError('WebSocket error');
      setIsDebating(false);
    };
  };

  return (
    <DebateContext.Provider value={{ setDebateTopic, isDebating, transcript, verdict, topic, error }}>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">AI Debate Platform</h1>
        <TopicSelector />
        <AudioRecorder />
        <DebateUi />
      </div>
    </DebateContext.Provider>
  );
}

export default App;
