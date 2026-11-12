import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { MarketAnalysisPage } from './pages/MarketAnalysisPage';
import { SkillExplorerPage } from './pages/SkillExplorerPage';
import { CareerMatchingPage } from './pages/CareerMatchingPage';
import { AssistantPage } from './pages/AssistantPage';
import { DataManagementPage } from './pages/DataManagementPage';
import { ModelPerformancePage } from './pages/ModelPerformancePage';
import { AboutPage } from './pages/AboutPage';

export function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/market" element={<MarketAnalysisPage />} />
          <Route path="/skills" element={<SkillExplorerPage />} />
          <Route path="/career" element={<CareerMatchingPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/datasets" element={<DataManagementPage />} />
          <Route path="/models" element={<ModelPerformancePage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
