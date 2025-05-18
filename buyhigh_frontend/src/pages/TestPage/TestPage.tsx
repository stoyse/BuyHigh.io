import React, { useEffect, useState } from 'react';
import { GetUserInfo } from '../../apiService';

const TestPage: React.FC = () => {
  const [userData, setUserData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const data = await GetUserInfo('1'); // Beispiel-User-ID
        setUserData(data);
      } catch (err) {
        setError('Fehler beim Abrufen der Benutzerdaten.');
        console.error(err);
      }
    };

    fetchUserData();
  }, []);

  return (
    <div>
      <h1>Testseite</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {userData ? (
        <pre>{JSON.stringify(userData, null, 2)}</pre>
      ) : (
        <p>Benutzerdaten werden geladen...</p>
      )}
    </div>
  );
};

export default TestPage;
