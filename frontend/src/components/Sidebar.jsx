export default function Sidebar({ riskScores, fires, plumes, alerts, hours, setHours, loading }) {
  const fireCount = fires?.metadata?.count || 0;
  const plumeCount = plumes?.metadata?.count || 0;
  const districtsAffected = riskScores?.length || 0;
  const criticalAlerts = alerts?.filter(a => a.alert_level === 'CRITICAL').length || 0;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>Agri-Fire Tracker</h1>
        <p>Real-time satellite fire monitoring across India</p>
      </div>

      <div className="sidebar-content">
        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card fire">
            <div className="stat-label">Active Fires</div>
            <div className="stat-value">{loading ? '-' : fireCount.toLocaleString()}</div>
          </div>
          <div className="stat-card alert">
            <div className="stat-label">Alerts</div>
            <div className="stat-value">{loading ? '-' : criticalAlerts}</div>
          </div>
          <div className="stat-card district">
            <div className="stat-label">Districts</div>
            <div className="stat-value">{loading ? '-' : districtsAffected}</div>
          </div>
          <div className="stat-card plume">
            <div className="stat-label">Plumes</div>
            <div className="stat-value">{loading ? '-' : plumeCount.toLocaleString()}</div>
          </div>
        </div>

        {/* Time filter */}
        <div className="section">
          <div className="section-title">Time Window</div>
          <div className="filter-row">
            {[6, 12, 24, 48].map(h => (
              <button
                key={h}
                className={`filter-btn ${hours === h ? 'active' : ''}`}
                onClick={() => setHours(h)}
              >
                {h}h
              </button>
            ))}
          </div>
        </div>

        {/* Risk Scores */}
        <div className="section">
          <div className="section-title">
            District Risk Scores ({riskScores?.length || 0})
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[1,2,3,4,5].map(i => (
                <div key={i} className="loading-skeleton" style={{ height: 44 }} />
              ))}
            </div>
          ) : riskScores?.length > 0 ? (
            <div className="risk-list">
              {riskScores.slice(0, 20).map((r, i) => (
                <div className="risk-item" key={i}>
                  <div>
                    <div className="district-name">{r.district}</div>
                    {r.state && <div className="district-state">{r.state}</div>}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="fire-count">{r.fire_count}</span>
                    <span className={`risk-badge ${r.risk_level}`}>
                      {r.risk_level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>
              No fire activity detected in this time window.
              <br />
              <span style={{ fontSize: '0.7rem' }}>Try increasing the time range.</span>
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
