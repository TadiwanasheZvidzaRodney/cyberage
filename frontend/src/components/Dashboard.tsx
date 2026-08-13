import { useState } from 'react';

export default function Dashboard() {
  const [target, setTarget] = useState('example.com');
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggerAgent = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/agent/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          engagementId: '123e4567-e89b-12d3-a456-426614174000',
          target: target
        })
      });
      const data = await response.json();
      setLogs(prev => [...prev, data]);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="control-panel">
        <h2>Run V1 Recon</h2>
        <div className="input-group">
          <input 
            type="text" 
            value={target} 
            onChange={(e) => setTarget(e.target.value)}
            placeholder="Target domain..."
          />
          <button onClick={triggerAgent} disabled={loading}>
            {loading ? 'Running...' : 'Execute DNS Enum'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>

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
