// App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginAdmin from "../pages/LoginAdmin.tsx";
import Admin from "../pages/Admin.tsx";
import AnimeAdd from "../pages/AnimeAdd.tsx";


const App = () => {
  return (
    <Router>
      <div>
        <h1>Welcome to My App</h1>
        <Routes>
            <Route path="/anime-add" element={<AnimeAdd />} />
          <Route path="/login" element={<LoginAdmin />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
