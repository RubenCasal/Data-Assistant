import React from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';  // Use BrowserRouter consistently

import Home from './pages/Home.tsx'
import Chatbot from './pages/Chatbot.tsx';

export interface IApplicationProps {}

const App: React.FunctionComponent<IApplicationProps> = (props) => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chatbot/:userId" element={<Chatbot />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
