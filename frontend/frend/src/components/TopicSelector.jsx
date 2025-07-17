// src/components/TopicSelector.jsx
import { useState } from 'react';
import { useDebate } from '../contexts/DebateContext';
import React from 'react';

const predefinedTopics = [
  "Is AI more helpful or harmful?",
  "Should homework be banned?",
  "Can social media be trusted?",
  "Will automation kill more jobs than it creates?",
  "Is space exploration worth the cost?",
];

const TopicSelector = () => {
  const [topic, setTopic] = useState('');
  const { setDebateTopic, setMode } = useDebate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) {
      setDebateTopic(topic.trim());
      setMode('user');
    }
  };

  const startRandomDebate = () => {
    const random = predefinedTopics[Math.floor(Math.random() * predefinedTopics.length)];
    setDebateTopic(random);
    setMode('random');
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-x-2">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter debate topic"
          className="border p-2 rounded"
        />
        <button type="submit" className="bg-blue-500 text-white px-4 py-2 rounded">
          Start Debate
        </button>
      </form>

      <div className="text-center">
        <button
          onClick={startRandomDebate}
          className="bg-green-500 text-white px-4 py-2 rounded"
        >
          Start Random Debate
        </button>
      </div>
    </div>
  );
};

export default TopicSelector;
