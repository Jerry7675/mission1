export const startDebate = async (mode, topic) => {
  const response = await fetch('/api/debate/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode, topic })
  })
  return await response.json()
}