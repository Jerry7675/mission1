import { useState } from 'react';
import { useDebate } from '../hooks/useDebate'; // ✅ FIXED PATH
import React from 'react';
const TopicSelector = () => {
  const [topic, setTopic] = useState('');
  const { setDebateTopic } = useDebate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) setDebateTopic(topic.trim());
  };

  return (
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
  );
};

export default TopicSelector;
