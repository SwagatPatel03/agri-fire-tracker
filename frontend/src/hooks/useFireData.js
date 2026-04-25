import { useState, useEffect, useCallback } from 'react';
import { fetchFires, fetchPlumes, fetchRiskScores, fetchAlerts } from '../api';

export function useFireData(hours = 24, refreshInterval = 300000) {
  const [fires, setFires] = useState(null);
  const [plumes, setPlumes] = useState(null);
  const [riskScores, setRiskScores] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      console.log('[useFireData] Fetching data for', hours, 'hours...');

      const [fireData, plumeData, riskData, alertData] = await Promise.allSettled([
        fetchFires(hours),
        fetchPlumes(hours),
        fetchRiskScores(hours),
        fetchAlerts(),
      ]);

      console.log('[useFireData] Results:', {
        fires: fireData.status === 'fulfilled' ? `${fireData.value?.metadata?.count} fires` : fireData.reason?.message,
        plumes: plumeData.status === 'fulfilled' ? `${plumeData.value?.metadata?.count} plumes` : plumeData.reason?.message,
        risk: riskData.status === 'fulfilled' ? `${riskData.value?.length} districts` : riskData.reason?.message,
        alerts: alertData.status === 'fulfilled' ? `${alertData.value?.length} alerts` : alertData.reason?.message,
      });

      if (fireData.status === 'fulfilled') setFires(fireData.value);
      else console.error('[useFireData] Fires failed:', fireData.reason);

      if (plumeData.status === 'fulfilled') setPlumes(plumeData.value);
      else console.error('[useFireData] Plumes failed:', plumeData.reason);

      if (riskData.status === 'fulfilled') setRiskScores(riskData.value);
      else console.error('[useFireData] Risk scores failed:', riskData.reason);

      if (alertData.status === 'fulfilled') setAlerts(alertData.value);
      else console.error('[useFireData] Alerts failed:', alertData.reason);

    } catch (err) {
      console.error('[useFireData] Fatal error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, refreshInterval);
    return () => clearInterval(interval);
  }, [loadData, refreshInterval]);

  return { fires, plumes, riskScores, alerts, loading, error, refetch: loadData };
}
