import React, { useState, useRef } from 'react';
import { useDebate } from '../contexts/DebateContext';
import logo from '../../public/vite.jpg';

const TopicSelector = () => {
  const [topic, setTopic] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [loadingTranscription, setLoadingTranscription] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const { setDebateTopic, setMode } = useDebate();

  const startRecording = async () => {
    setTopic('');
    setIsRecording(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendAudioToTranscribe(audioBlob);
      };

      mediaRecorderRef.current.start();
    } catch (err) {
      alert("Could not start recording: " + err.message);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToTranscribe = async (blob) => {
    setLoadingTranscription(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'topic_audio.webm');

      const response = await fetch('/api/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Transcription failed');

      const data = await response.json();
      if (data.text) {
        setTopic(data.text);
        setMode('user');
        setDebateTopic(data.text);
      } else {
        alert('No transcription returned');
      }
    } catch (err) {
      alert("Transcription error: " + err.message);
    } finally {
      setLoadingTranscription(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) {
      setDebateTopic(topic.trim());
      setMode('user');
    }
  };

  const predefinedTopics = [
    "Should homework be banned?",
    "Will automation kill more jobs than it creates?",
    "Is space exploration worth the cost?",
    "Who would win in a rap battle: Shakespeare or Eminem?",
    "Your favorite rapper vs. a random squirrel – who spits better bars?",
    "Diss each other using only food puns – let the roast begin!",
    "Who had the worse downfall: Fyre Festival or your last relationship?",
    "Rap Battle between you two Lets go!",
    "Tell the worst dad joke possible – winner gets imaginary dad points.",
    "Roast each other using only compliments (backhanded battle).",
    "Who is the most overrated fictional character? Fight for your pick!",
    "Convince me that pineapple DOES belong on pizza (joke arguments only).",
    "Roast Each other to the fullest ",
    "Would Batman survive in the Among Us universe?",
    "Fortnite dances vs. TikTok trends – which is cringier?",
    "PC gamers vs. console gamers – who’s more delusional?",
    "Would you rather fight 100 duck-sized horses or 1 horse-sized duck?",
    "Could a taco win a presidential election? Debate its campaign strategy.",
    "If animals could talk, which species would be the rudest?",
    "Who would win in a fight: a zombie apocalypse or Karens at a Black Friday sale?",
    "Your ex’s LinkedIn bio vs. a used car sales pitch – which is funnier?",
    " Rost my friends with the worst insults possible",
    "A grammar nazi vs. a meme lord – who’s more insufferable?",
    "ChatGPT vs. your smartest friend - who gives worse life advice?",
    "Your search history vs. an AI's - which is more concerning?",
    " The internet is just one big group chat that got out of hand"
  ];

  const startRandomDebate = () => {
    const random = predefinedTopics[Math.floor(Math.random() * predefinedTopics.length)];
    setDebateTopic(random);
    setMode('random');
  };

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-100 via-blue-50 to-purple-100 p-4 overflow-hidden">

      {/* Floating animated background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute bg-pink-300 opacity-30 w-72 h-72 rounded-full top-10 left-10 animate-pulse" />
        <div className="absolute bg-purple-300 opacity-30 w-96 h-96 rounded-full bottom-10 right-10 animate-ping" />
      </div>

      {/* Logo */}
      <div className="absolute top-4 right-4">
        <img src={logo} alt="App Logo" className="h-16 w-auto drop-shadow-xl" />
      </div>

      {/* Main Card */}
      <div className="bg-white shadow-2xl border border-gray-200 rounded-3xl p-8 w-full max-w-2xl space-y-6 animate-fadeInUp">
        <h2 className="text-3xl font-extrabold text-center text-blue-700 tracking-wide">
          🎤 Start Your Debate Journey
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter debate topic or use voice"
            className="border border-gray-300 p-2 rounded-md flex-1 shadow-inner focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            type="submit"
            disabled={loadingTranscription}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md font-semibold transition-all"
          >
            {loadingTranscription ? 'Transcribing...' : 'Start Debate'}
          </button>
        </form>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          {!isRecording ? (
            <button
              onClick={startRecording}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md transition-all font-medium"
            >
              🎙️ Record Topic
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-all font-medium"
            >
              ⏹️ Stop Recording
            </button>
          )}

          <button
            onClick={startRandomDebate}
            disabled={loadingTranscription}
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md transition-all font-medium"
          >
            🎲 Random Topic
          </button>
        </div>
      </div>
    </div>
  );
};

export default TopicSelector;
