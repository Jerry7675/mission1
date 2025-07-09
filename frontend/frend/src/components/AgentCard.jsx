export default function AgentCard({ agent }) {
  return (
    <div className={`border rounded-lg p-4 flex-1 ${agent.speaking ? 'bg-yellow-50' : 'bg-white'}`}>
      <div className="min-h-32">
        {agent.text || "Waiting for response..."}
      </div>
    </div>
  )
}