import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';

// Suppress ResizeObserver error in development
const resizeObserverErrorHandler = (e: ErrorEvent) => {
  if (
    e.message.includes('ResizeObserver loop completed with undelivered notifications') ||
    e.message.includes('ResizeObserver loop limit exceeded')
  ) {
    e.stopImmediatePropagation();
  }
};

window.addEventListener('error', resizeObserverErrorHandler);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
