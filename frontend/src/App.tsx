import React, { useState } from 'react';
import { FarmProvider } from './context/FarmContext';
import { Layout } from './components/layout/Layout';
import { TabId } from './components/layout/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { FarmSetupPage } from './pages/FarmSetupPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { CropDetailPage } from './pages/CropDetailPage';
import { SimulatorPage } from './pages/SimulatorPage';

export const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const [selectedCrop, setSelectedCrop] = useState<string>('rice');

  const handleSelectCrop = (cropName: string) => {
    setSelectedCrop(cropName);
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'dashboard' && (
        <DashboardPage
          onNavigate={setActiveTab}
          onSelectCrop={handleSelectCrop}
        />
      )}
      {activeTab === 'setup' && (
        <FarmSetupPage onNavigate={setActiveTab} />
      )}
      {activeTab === 'recommendations' && (
        <RecommendationsPage
          onNavigate={setActiveTab}
          onSelectCrop={handleSelectCrop}
        />
      )}
      {activeTab === 'details' && (
        <CropDetailPage
          selectedCrop={selectedCrop}
          onSelectCrop={handleSelectCrop}
          onNavigate={setActiveTab}
        />
      )}
      {activeTab === 'simulator' && (
        <SimulatorPage
          onNavigate={setActiveTab}
          onSelectCrop={handleSelectCrop}
        />
      )}
    </Layout>
  );
};

export const App: React.FC = () => {
  return (
    <FarmProvider>
      <AppContent />
    </FarmProvider>
  );
};

export default App;
