import { useDebate } from '../contexts/DebateContext';
import React from 'react';

const DebateUI = () => {
  const { transcript, verdict } = useDebate();

  const proText = transcript
    .filter((round) => round.speaker === 'Pro')
    .map((round) => round.content)
    .join('\n');

  const conText = transcript
    .filter((round) => round.speaker === 'Con')
    .map((round) => round.content)
    .join('\n');

  return (
    <div className="p-4 max-w-screen-xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Pro Section */}
        <div className="flex flex-col">
          <label className="font-bold mb-1">Pro</label>
          <textarea
            value={proText}
            readOnly
            className="flex-grow min-h-[200px] resize-y p-3 border rounded bg-gray-100"
          />
        </div>

        {/* Con Section */}
        <div className="flex flex-col">
          <label className="font-bold mb-1">Con</label>
          <textarea
            value={conText}
            readOnly
            className="flex-grow min-h-[200px] resize-y p-3 border rounded bg-gray-100"
          />
        </div>
      </div>

      {/* Judge Section */}
      {verdict && (
        <div className="flex flex-col">
          <label className="font-bold mb-1">Judge's Verdict</label>
          <textarea
            value={verdict}
            readOnly
            className="w-full min-h-[150px] resize-y p-3 border rounded bg-green-100"
          />
        </div>
      )}
    </div>
  );
};

export default DebateUI;
