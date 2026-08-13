import { useState, useEffect } from 'react';
import AttackGraph from './AttackGraph';

export default function Dashboard() {
  const [target, setTarget] = useState('example.com');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [engagementId, setEngagementId] = useState<string | null>(null);

  useEffect(() => {
    if (!engagementId) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/agent/logs/${engagementId}`);
        const data = await response.json();
        setLogs(data);
        
        // Simple heuristic: if we haven't received a new log in a while, or if the last action was finish_engagement...
        // For V2, we'll just keep polling. The user can stop it or navigate away.
      } catch (err) {
        console.error("Error fetching logs:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [engagementId]);

  const triggerAgent = async () => {
    setLoading(true);
    setError(null);
    const newEngagementId = crypto.randomUUID();
    setEngagementId(newEngagementId);
    setLogs([]);
    
    try {
      await fetch('http://localhost:8000/api/agent/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          engagementId: newEngagementId,
          target: target
        })
      });
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="control-panel">
        <h2>CyberAge V2 - Autonomous Mode</h2>
        <div className="input-group">
          <input 
            type="text" 
            value={target} 
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Target domain..."
          />
          <button onClick={triggerAgent}>
            {engagementId ? 'Start New Engagement' : 'Launch Autonomous Agent'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>

      {engagementId && (
        <div style={{ marginBottom: '2rem' }}>
          <h2>Live Attack Graph</h2>
          <AttackGraph logs={logs} target={target} />
        </div>
      )}

      <div className="audit-trail">
        <h2>Immutable Audit Trail</h2>
        {logs.length === 0 ? (
          <p className="empty-state">No execution logs yet. Run the agent to start.</p>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="log-entry">
              <div className="log-step hypothesis">
                <strong>Hypothesis:</strong> {log.hypothesis}
              </div>
              <div className={`log-step policy ${log.policy?.status === 'APPROVED' ? 'approved' : 'blocked'}`}>
                <strong>Policy Check:</strong> {log.policy?.status} - {log.policy?.reason}
              </div>
              {log.execution && (
                <div className="log-step execution">
                  <strong>Execution Result:</strong>
                  <pre>{log.execution.output || JSON.stringify(log.execution)}</pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
