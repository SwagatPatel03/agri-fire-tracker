import { useState } from 'react';
import { useFireData } from './hooks/useFireData';
import FireMap from './components/FireMap';
import Sidebar from './components/Sidebar';
import AlertBanner from './components/AlertBanner';

export default function App() {
  const [hours, setHours] = useState(24);
  const { fires, plumes, riskScores, alerts, loading, error } = useFireData(hours);

  return (
    <div className="app-layout">
      <Sidebar
        riskScores={riskScores}
        fires={fires}
        plumes={plumes}
        alerts={alerts}
        hours={hours}
        setHours={setHours}
        loading={loading}
      />
      <FireMap fires={fires} plumes={plumes} />
      <AlertBanner alerts={alerts} />
    </div>
  );
}
