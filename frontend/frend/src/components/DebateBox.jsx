import { useState, useEffect } from 'react';
import React from 'react';
import { connect, send } from '../api/socket';
import AudioPlayer from './AudioPlayer';

export default function DebateBox() {
  const [agents, setAgents] = useState({
    agent1: { text: '', speaking: false },
    agent2: { text: '', speaking: false }
  });
  const [currentAudioUrl, setCurrentAudioUrl] = useState(null); // <-- Added this line

  // Connect on component mount
  useEffect(() => {
    const socket = connect();
    
    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'agent_response') {
        // Update agent text
        setAgents(prev => ({
          ...prev,
          [data.agent]: { 
            text: data.text, 
            speaking: true 
          }
        }));

        // Generate audio for this response
        const audioResponse = await fetch('/api/audio/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: data.text })
        });
        const audioBlob = await audioResponse.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        setCurrentAudioUrl(audioUrl);
      }
    };

    return () => disconnect();
  }, []);

  const startDebate = () => {
    send({ 
      action: 'start_debate',
      mode: 'random' // or 'custom'
    });
  };

  return (
    <div>
      {/* Agent displays */}
      <div className="flex gap-4 mb-4">
        <div className={`p-4 border rounded ${agents.agent1.speaking ? 'bg-yellow-100' : 'bg-white'}`}>
          {agents.agent1.text || "Waiting..."}
        </div>
        <div className={`p-4 border rounded ${agents.agent2.speaking ? 'bg-yellow-100' : 'bg-white'}`}>
          {agents.agent2.text || "Waiting..."}
        </div>
      </div>
      
      {/* Audio player */}
      <AudioPlayer audioUrl={currentAudioUrl} />
      
      {/* Controls */}
      <button 
        onClick={startDebate}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Start Debate
      </button>
    </div>
  );
}