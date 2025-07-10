/**
 * Database Context - Manages current database server state across the app
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface DatabaseContextType {
  currentServer: string;
  setCurrentServer: (server: string) => void;
  switchServer: (server: string) => void;
}

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

interface DatabaseProviderProps {
  children: ReactNode;
}

export const DatabaseProvider: React.FC<DatabaseProviderProps> = ({ children }) => {
  const [currentServer, setCurrentServerState] = useState<string>('');

  const setCurrentServer = useCallback((server: string) => {
    setCurrentServerState(server);
  }, []);

  const switchServer = useCallback((server: string) => {
    // Simply update the current server selection
    setCurrentServerState(server);
  }, []);

  const value: DatabaseContextType = {
    currentServer,
    setCurrentServer,
    switchServer,
  };

  return (
    <DatabaseContext.Provider value={value}>
      {children}
    </DatabaseContext.Provider>
  );
};

export const useDatabaseContext = (): DatabaseContextType => {
  const context = useContext(DatabaseContext);
  if (context === undefined) {
    throw new Error('useDatabaseContext must be used within a DatabaseProvider');
  }
  return context;
};

export default DatabaseContext;