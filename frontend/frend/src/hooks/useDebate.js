import { useContext } from 'react';
import { DebateContext } from '../contexts/DebateContext';

export const useDebate = () => {
  const context = useContext(DebateContext);
  if (!context) {
    throw new Error('useDebate must be used within a DebateContext.Provider');
  }
  return context;
};
