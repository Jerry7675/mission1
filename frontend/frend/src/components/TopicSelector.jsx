import React, { useState, useRef, useEffect } from 'react';
import { useDebate } from '../contexts/DebateContext';
import logo from '../../public/vite.jpg';

const TopicSelector = () => {
  const [topic, setTopic] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [loadingTranscription, setLoadingTranscription] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [debateHistory, setDebateHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const wsRef = useRef(null);

  const { 
    setDebateTopic, 
    setMode, 
    isDebating, 
    transcript, 
    verdict, 
    topic: currentTopic, 
    error,
    mode 
  } = useDebate();

  // Health check on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  // WebSocket connection management
  useEffect(() => {
    if (isDebating && (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN)) {
      setConnectionStatus('connecting');
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
        setConnectionStatus('disconnected');
      }
    };
  }, [isDebating]);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      setHealthStatus(data);
    } catch (err) {
      setHealthStatus({ status: 'error', message: err.message });
    }
  };

  const connectWebSocket = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    wsRef.current = new WebSocket('ws://localhost:8000/ws/debate');

    wsRef.current.onopen = () => {
      setConnectionStatus('connected');
      console.log('WebSocket connected');
    };

    wsRef.current.onclose = () => {
      setConnectionStatus('disconnected');
      console.log('WebSocket disconnected');
    };

    wsRef.current.onerror = (error) => {
      setConnectionStatus('error');
      console.error('WebSocket error:', error);
    };

    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('WebSocket message:', message);

      switch (message.type) {
        case 'round_update':
          // handled in DebateContext
          break;
        case 'verdict':
          // handled in DebateContext
          break;
        case 'error':
          console.error('Debate error:', message.message);
          break;
        case 'history':
          setDebateHistory(message.data);
          break;
        default:
          console.warn('Unknown message type:', message.type);
      }
    };
  };

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
      
      // Stop all audio tracks
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      }
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

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Transcription failed');
      }

      const data = await response.json();
      if (data.text) {
        setTopic(data.text);
        setMode('user');
      } else {
        alert('No transcription returned');
      }
    } catch (err) {
      alert("Transcription error: " + err.message);
      console.error('Transcription error:', err);
    } finally {
      setLoadingTranscription(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) {
      connectWebSocket();
      setDebateTopic(topic.trim());
      setMode('user');
    }
  };

  const startRandomDebate = () => {
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
      "PC gamers vs. console gamers – who's more delusional?",
      "Would you rather fight 100 duck-sized horses or 1 horse-sized duck?",
      "Could a taco win a presidential election? Debate its campaign strategy.",
      "If animals could talk, which species would be the rudest?",
      "Who would win in a fight: a zombie apocalypse or Karens at a Black Friday sale?",
      "Your ex's LinkedIn bio vs. a used car sales pitch – which is funnier?",
      " Rost my friends with the worst insults possible",
      "A grammar nazi vs. a meme lord – who's more insufferable?",
      "ChatGPT vs. your smartest friend - who gives worse life advice?",
      "Your search history vs. an AI's - which is more concerning?",
      " The internet is just one big group chat that got out of hand"
    ];

    const random = predefinedTopics[Math.floor(Math.random() * predefinedTopics.length)];
    connectWebSocket();
    setDebateTopic(random);
    setMode('random');
  };

  const loadDebateHistory = async () => {
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'get_history' }));
      } else {
        // Fallback to REST API
        const response = await fetch('/api/history?limit=10');
        if (response.ok) {
          const data = await response.json();
          setDebateHistory(data);
        }
      }
      setShowHistory(true);
    } catch (err) {
      console.error('Failed to load history:', err);
      alert('Failed to load debate history');
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthStatusColor = () => {
    if (!healthStatus) return 'text-gray-500';
    return healthStatus.status === 'healthy' ? 'text-green-500' : 'text-red-500';
  };

  // If debate is active, show the debate interface
  if (isDebating || transcript.length > 0) {
    return (
      <div className="relative min-h-screen w-full bg-gradient-to-br from-indigo-100 via-blue-50 to-purple-100 p-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => window.location.reload()}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-all font-medium"
            >
              ← Back to Topics
            </button>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              <span className={`text-sm font-bold ${getConnectionStatusColor()}`}>
                {connectionStatus}
              </span>
            </div>
          </div>
          <img src={logo} alt="App Logo" className="h-12 w-auto drop-shadow-xl" />
        </div>

        {/* Current Topic */}
        <div className="bg-white shadow-lg rounded-lg p-4 mb-6">
          <h2 className="text-xl font-bold text-blue-700 mb-2">Current Topic:</h2>
          <p className="text-gray-700 text-lg">{currentTopic}</p>
          <div className="mt-2 text-sm text-gray-500">
            Mode: {mode === 'user' ? 'User Selected' : 'Random'}
          </div>
        </div>

        {/* Debate Status */}
        {isDebating && (
          <div className="bg-yellow-100 border border-yellow-400 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600"></div>
              <span className="text-yellow-800 font-medium">Debate in progress...</span>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-100 border border-red-400 rounded-lg p-4 mb-6">
            <div className="flex items-center gap-2">
              <span className="text-red-800 font-medium">Error: {error}</span>
            </div>
          </div>
        )}

        {/* Transcript Display */}
        {transcript.length > 0 && (
          <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Debate Transcript</h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {transcript.map((round, index) => {
                const isEvenRound = round.round_number % 2 === 0;
                const actualPro = isEvenRound ? round.con : round.pro;
                const actualCon = isEvenRound ? round.pro : round.con;

                return (
                  <div key={index} className="border-l-4 border-blue-400 pl-4">
                    <div className="font-semibold text-blue-700 mb-2">
                      Round {round.round_number}
                    </div>
                    <div className="space-y-3">
                      <div className="bg-green-50 p-3 rounded-md">
                        <span className="font-medium text-green-800">PRO:</span>
                        <p className="text-gray-700 mt-1">{actualPro}</p>
                      </div>
                      <div className="bg-red-50 p-3 rounded-md">
                        <span className="font-medium text-red-800">CON:</span>
                        <p className="text-gray-700 mt-1">{actualCon}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Verdict Display */}
        {verdict && (
          <div className="bg-white shadow-lg rounded-lg p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">🏆 Final Verdict</h3>
            <div className="bg-blue-50 p-4 rounded-md">
              <p className="text-gray-700 whitespace-pre-wrap">{verdict}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-100 via-blue-50 to-purple-100 p-4 overflow-hidden">
      {/* Floating animated background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute bg-pink-300 opacity-30 w-72 h-72 rounded-full top-10 left-10 animate-pulse" />
        <div className="absolute bg-purple-300 opacity-30 w-96 h-96 rounded-full bottom-10 right-10 animate-ping" />
      </div>

      {/* Status Bar */}
      <div className="absolute top-4 left-4 flex items-center gap-4">
        <div className="bg-white px-3 py-1 rounded-full shadow-md">
          <span className="text-xs font-medium">Backend:</span>
          <span className={`text-xs font-bold ml-1 ${getHealthStatusColor()}`}>
            {healthStatus?.status || 'checking...'}
          </span>
        </div>
        {healthStatus?.models_loaded && (
          <div className="bg-white px-3 py-1 rounded-full shadow-md">
            <span className="text-xs font-medium">Models:</span>
            <span className="text-xs font-bold ml-1 text-blue-600">
              {healthStatus.models_loaded.length}
            </span>
          </div>
        )}
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
            disabled={isDebating || loadingTranscription}
          />
          <button
            type="submit"
            disabled={loadingTranscription || isDebating || !topic.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-semibold transition-all"
          >
            {loadingTranscription ? 'Transcribing...' : isDebating ? 'Debating...' : 'Start Debate'}
          </button>
        </form>

        {/* Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={isDebating || loadingTranscription}
              className="bg-red-500 hover:bg-red-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-all font-medium"
            >
              🎙️ Record Topic
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-all font-medium animate-pulse"
            >
              ⏹️ Stop Recording
            </button>
          )}

          <button
            onClick={startRandomDebate}
            disabled={loadingTranscription || isDebating}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-all font-medium"
          >
            🎲 Random Topic
          </button>

          <button
            onClick={loadDebateHistory}
            disabled={loadingTranscription || isDebating}
            className="bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md transition-all font-medium"
          >
            📜 History
          </button>
        </div>

        {/* Connection Status */}
        <div className="text-center text-sm text-gray-600">
          WebSocket: <span className={`font-bold ${getConnectionStatusColor()}`}>{connectionStatus}</span>
        </div>
      </div>

      {/* History Modal */}
      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">Debate History</h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ×
              </button>
            </div>
            <div className="space-y-4 bg-auto p-4 rounded-lg shadow-md">
              {debateHistory.length > 0 ? (
                debateHistory.map((item, index) => (
                  <div key={index} className="border-l-4 border-blue-400 pl-4 py-2">
                    <div className="font-medium text-blue-700">{item.metadata?.topic || 'Unknown Topic'}</div>
                    <div className="text-sm text-gray-600">
                      Round {item.metadata?.round || 'N/A'} • {item.metadata?.timestamp || 'No timestamp'}
                    </div>
                    <div className="text-sm text-gray-700 mt-1">{item.content}</div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-8">
                  No debate history found
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TopicSelector;
