import '@testing-library/jest-dom';

// Mock ResizeObserver for Recharts in JSDOM environment
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = ResizeObserverMock;
