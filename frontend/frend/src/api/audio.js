export const getAudio = async (text) => {
  const response = await fetch('/api/audio/generate', {
    method: 'POST',
    body: JSON.stringify({ text })
  })
  return await response.blob()
}