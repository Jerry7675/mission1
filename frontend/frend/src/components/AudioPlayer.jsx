import { useState, useEffect, useRef } from 'react';
import React from 'react';
export default function AudioPlayer({ audioUrl }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Handle audio playback when URL changes
  useEffect(() => {
    if (!audioUrl) return;

    const audio = audioRef.current;
    
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);

    // Auto-play when audio URL changes
    audio.play().catch(e => console.error("Auto-play failed:", e));

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [audioUrl]);

  const togglePlayback = () => {
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(e => console.error("Play failed:", e));
    }
  };

  return (
    <div className="fixed bottom-4 right-4 bg-white p-3 rounded-lg shadow-md">
      {/* Hidden audio element */}
      <audio 
        ref={audioRef} 
        src={audioUrl} 
        preload="auto"
      />
      
      {/* Play/Pause button (only shows when audio is available) */}
      {audioUrl && (
        <button
          onClick={togglePlayback}
          className={`p-2 rounded-full ${isPlaying ? 'bg-red-500' : 'bg-green-500'}`}
        >
          {isPlaying ? (
            <span className="text-white">■ Stop</span>
          ) : (
            <span className="text-white">▶ Play</span>
          )}
        </button>
      )}
    </div>
  );
}