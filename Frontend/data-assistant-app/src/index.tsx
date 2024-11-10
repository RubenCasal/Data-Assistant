import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App.tsx';
import reportWebVitals from './reportWebVitals.ts';
import { ThemeProvider, createTheme } from '@mui/material/styles'; // Import ThemeProvider and createTheme

// Create a theme (you can customize it if needed)
const theme = createTheme();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Wrap <App /> in <ThemeProvider>
root.render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);

reportWebVitals();
