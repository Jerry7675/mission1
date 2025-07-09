let socket = null;

export const connect = () => {
  socket = new WebSocket('ws://localhost:8000/ws'); // Match your FastAPI endpoint

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'agent_response') {
      // Handle agent messages
      return { agent: data.agent, text: data.text };
    }
    if (data.type === 'judge_result') {
      // Handle final verdict
      return { verdict: data.verdict };
    }
  };

  return socket;
};

export const send = (message) => {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(message));
  }
};

export const disconnect = () => {
  socket?.close();
};