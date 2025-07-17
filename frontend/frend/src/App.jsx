import React from 'react';
import { DebateProvider } from './contexts/DebateContext';
import TopicSelector from './components/TopicSelector';
import DebateUi from './components/DebateUi';
import './App.css';

function App() {
  return (
    <DebateProvider>
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">AI Debate Platform</h1>
        <TopicSelector />
       
        <DebateUi />
      </div>
    </DebateProvider>
  );
}

export default App;
