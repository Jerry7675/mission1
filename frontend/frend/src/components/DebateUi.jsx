import { useDebate } from '../contexts/DebateContext';
import React from 'react';

const DebateUI = () => {
  const { transcript, verdict } = useDebate();

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-2">Debate Transcript</h2>
      <div className="space-y-2">
        {transcript.map((round, idx) => (
          <div key={idx} className="border p-2 rounded bg-gray-100">
            <p>{round.content}</p>
          </div>
        ))}
      </div>
      {verdict && (
        <div className="mt-4 p-4 bg-green-100 border rounded">
          <strong>Judge's Verdict:</strong> {verdict}
        </div>
      )}
    </div>
  );
};

export default DebateUI;