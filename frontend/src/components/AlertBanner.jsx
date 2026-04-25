export default function AlertBanner({ alerts }) {
  // Only show if there are critical unacknowledged alerts
  const critical = alerts?.filter(a => a.alert_level === 'CRITICAL' && !a.acknowledged_at);

  if (!critical || critical.length === 0) return null;

  const latest = critical[0];

  return (
    <div className="alert-banner" id="alert-banner">
      <div className="alert-icon" />
      <span className="alert-text">
        {latest.message} | {critical.length} critical alert{critical.length > 1 ? 's' : ''} active
      </span>
    </div>
  );
}
