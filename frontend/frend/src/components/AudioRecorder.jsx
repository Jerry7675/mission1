import { useState, useRef } from 'react';
import React from 'react';

const AudioRecorder = ({ onTranscription }) => {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    mediaRecorderRef.current.ondataavailable = (e) => chunksRef.current.push(e.data);
    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('file', blob, 'audio.wav');
      const res = await fetch('http://localhost:8000/transcribe', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      onTranscription(data.transcript);
      chunksRef.current = [];
    };
    mediaRecorderRef.current.start();
    setRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setRecording(false);
  };

  return (
    <div className="space-x-2">
      <button onClick={startRecording} disabled={recording} className="bg-green-500 text-white px-4 py-2 rounded">Start</button>
      <button onClick={stopRecording} disabled={!recording} className="bg-red-500 text-white px-4 py-2 rounded">Stop</button>
    </div>
  );
};

export default AudioRecorder;