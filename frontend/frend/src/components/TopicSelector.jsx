import React, { useState, useRef, useEffect } from 'react';
import { useDebate } from '../contexts/DebateContext';
import logo from '../vite.jpg';

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
              className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white px-6 py-2 rounded-lg transition-all font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              ← Back to Topics
            </button>
            <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-full shadow-md">
              <span className="text-sm font-medium">Status:</span>
              <span className={`text-sm font-bold ${getConnectionStatusColor()}`}>
                {connectionStatus}
              </span>
            </div>
          </div>
          <img src={logo} alt="App Logo" className="h-12 w-auto drop-shadow-xl rounded-lg" />
        </div>

        {/* Current Topic */}
        <div className="bg-white shadow-xl rounded-2xl p-6 mb-6 border border-gray-100">
          <h2 className="text-xl font-bold text-blue-700 mb-3 flex items-center gap-2">
            <span className="text-2xl">💭</span>
            Current Topic:
          </h2>
          <p className="text-gray-700 text-lg leading-relaxed">{currentTopic}</p>
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm text-gray-500">Mode:</span>
            <span className={`text-sm font-medium px-2 py-1 rounded-full ${
              mode === 'user' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
            }`}>
              {mode === 'user' ? '👤 User Selected' : '🎲 Random'}
            </span>
          </div>
        </div>

        {/* Debate Status */}
        {isDebating && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-400 rounded-2xl p-4 mb-6 shadow-md">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-yellow-600 border-t-transparent"></div>
              <span className="text-yellow-800 font-medium">Debate in progress...</span>
              <div className="flex gap-1 ml-auto">
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-gradient-to-r from-red-50 to-pink-50 border border-red-400 rounded-2xl p-4 mb-6 shadow-md">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <span className="text-red-800 font-medium">Error: {error}</span>
            </div>
          </div>
        )}

        {/* Transcript Display */}
        {transcript.length > 0 && (
          <div className="bg-white shadow-xl rounded-2xl p-6 mb-6 border border-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">📝</span>
              Debate Transcript
            </h3>
            <div className="space-y-6 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {transcript.map((round, index) => {
                const isEvenRound = round.round_number % 2 === 0;
                const actualPro = isEvenRound ? round.con : round.pro;
                const actualCon = isEvenRound ? round.pro : round.con;

                return (
                  <div key={index} className="border-l-4 border-blue-400 pl-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-r-xl p-4">
                    <div className="font-semibold text-blue-700 mb-3 flex items-center gap-2">
                      <span className="bg-blue-100 px-2 py-1 rounded-full text-sm">Round {round.round_number}</span>
                    </div>
                    <div className="space-y-4">
                      <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-xl border border-green-200 shadow-sm">
                        <span className="font-bold text-green-800 flex items-center gap-2 mb-2">
                          <span className="text-lg">✅</span>
                          PRO:
                        </span>
                        <p className="text-gray-700 leading-relaxed">{actualPro}</p>
                      </div>
                      <div className="bg-gradient-to-r from-red-50 to-rose-50 p-4 rounded-xl border border-red-200 shadow-sm">
                        <span className="font-bold text-red-800 flex items-center gap-2 mb-2">
                          <span className="text-lg">❌</span>
                          CON:
                        </span>
                        <p className="text-gray-700 leading-relaxed">{actualCon}</p>
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
          <div className="bg-white shadow-xl rounded-2xl p-6 border border-gray-100">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-2xl">🏆</span>
              Final Verdict
            </h3>
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-200 shadow-inner">
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{verdict}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative min-h-screen w-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-100 via-blue-50 to-purple-100 p-4 overflow-hidden">
      {/* Enhanced floating animated background blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
        <div className="absolute bg-gradient-to-r from-pink-300 to-rose-300 opacity-20 w-72 h-72 rounded-full top-10 left-10 animate-pulse blur-xl" />
        <div className="absolute bg-gradient-to-r from-purple-300 to-indigo-300 opacity-20 w-96 h-96 rounded-full bottom-10 right-10 animate-ping blur-xl" />
        <div className="absolute bg-gradient-to-r from-blue-300 to-cyan-300 opacity-15 w-64 h-64 rounded-full top-1/2 left-1/3 animate-bounce blur-2xl" />
      </div>

      {/* Enhanced Status Bar */}
      <div className="absolute top-4 left-4 flex items-center gap-3">
        <div className="bg-white backdrop-blur-sm bg-opacity-90 px-4 py-2 rounded-full shadow-lg border border-white border-opacity-20">
          <span className="text-xs font-medium text-gray-600">Backend:</span>
          <span className={`text-xs font-bold ml-1 ${getHealthStatusColor()}`}>
            {healthStatus?.status || 'checking...'}
          </span>
        </div>
        {healthStatus?.models_loaded && (
          <div className="bg-white backdrop-blur-sm bg-opacity-90 px-4 py-2 rounded-full shadow-lg border border-white border-opacity-20">
            <span className="text-xs font-medium text-gray-600">Models:</span>
            <span className="text-xs font-bold ml-1 text-blue-600">
              {healthStatus.models_loaded.length}
            </span>
          </div>
        )}
      </div>

      {/* Enhanced Logo */}
      <div className="absolute top-4 right-4">
        <img src={logo} alt="App Logo" className="h-16 w-auto drop-shadow-2xl rounded-2xl border-2 border-white border-opacity-30" />
      </div>

      {/* Enhanced Main Card */}
      <div className="bg-white bg-opacity-95 backdrop-blur-sm shadow-2xl border border-white border-opacity-30 rounded-3xl p-8 w-full max-w-2xl space-y-8 animate-fadeInUp">
        <h2 className="text-4xl font-extrabold text-center bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent tracking-wide">
          🎤 Start Your Debate Journey
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter debate topic or use voice"
            className="border-2 border-gray-200 p-3 rounded-xl flex-1 shadow-inner focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all duration-200 bg-gray-50 hover:bg-white"
            disabled={isDebating || loadingTranscription}
          />
          <button
            type="submit"
            disabled={loadingTranscription || isDebating || !topic.trim()}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
          >
            {loadingTranscription ? (
              <span className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Transcribing...
              </span>
            ) : isDebating ? (
              <span className="flex items-center gap-2">
                <div className="animate-pulse w-2 h-2 bg-white rounded-full"></div>
                Debating...
              </span>
            ) : 'Start Debate'}
          </button>
        </form>

        {/* Enhanced Action Buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          {!isRecording ? (
            <button
              onClick={startRecording}
              disabled={isDebating || loadingTranscription}
              className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              🎙️ Record Topic
            </button>
          ) : (
            <button
              onClick={stopRecording}
              className="bg-gradient-to-r from-gray-600 to-gray-700 hover:from-gray-700 hover:to-gray-800 text-white px-6 py-3 rounded-xl transition-all duration-200 font-medium animate-pulse shadow-lg hover:shadow-xl"
            >
              ⏹️ Stop Recording
            </button>
          )}

          <button
            onClick={startRandomDebate}
            disabled={loadingTranscription || isDebating}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
          >
            🎲 Random Topic
          </button>

          <button
            onClick={loadDebateHistory}
            disabled={loadingTranscription || isDebating}
            className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
          >
            📜 History
          </button>
        </div>

        {/* Enhanced Connection Status */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-gray-50 px-4 py-2 rounded-full border border-gray-200 shadow-sm">
            <span className="text-sm text-gray-600">WebSocket:</span>
            <span className={`font-bold text-sm ${getConnectionStatusColor()}`}>
              {connectionStatus}
            </span>
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' : 
              connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
            }`}></div>
          </div>
        </div>
      </div>

      {/* Enhanced History Modal - Fixed black background issue */}
      {showHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 p-6 max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-2">
                <span className="text-2xl">📜</span>
                Debate History
              </h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center transition-all duration-200"
              >
                ×
              </button>
            </div>
            
            {/* Fixed: Changed from bg-auto to proper background styling */}
            <div className="space-y-4 bg-gradient-to-br from-gray-50 to-blue-50 p-6 rounded-xl shadow-inner max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
              {debateHistory.length > 0 ? (
                debateHistory.map((item, index) => (
                  <div key={index} className="bg-white border-l-4 border-purple-400 rounded-r-lg pl-6 pr-4 py-4 shadow-sm hover:shadow-md transition-all duration-200">
                    <div className="font-bold text-purple-700 text-lg mb-2 flex items-center gap-2">
                      <span className="text-xl">💭</span>
                      {item.metadata?.topic || 'Unknown Topic'}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                      <span className="bg-gray-100 px-2 py-1 rounded-full">
                        Round {item.metadata?.round || 'N/A'}
                      </span>
                      <span className="bg-blue-100 px-2 py-1 rounded-full text-blue-700">
                        {item.metadata?.timestamp || 'No timestamp'}
                      </span>
                    </div>
                    <div className="text-gray-700 leading-relaxed bg-gray-50 p-3 rounded-lg">
                      {item.content}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🤔</div>
                  <div className="text-gray-500 text-lg font-medium">
                    No debate history found
                  </div>
                  <div className="text-gray-400 text-sm mt-2">
                    Start your first debate to see history here!
                  </div>
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