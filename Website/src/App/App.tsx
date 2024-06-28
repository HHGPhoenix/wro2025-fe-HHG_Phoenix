import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from '../components/Nav/Navbar.js';
import Home from '../pages/LiDAR.js';
import About from '../pages/Vidstreams.js';
import Contact from '../pages/CarControl.js';
import '../tailwind.css';

const App: React.FC = () => {
    return (
        <Router>
            <div className="App flex">
                <Navbar />
                <div className="flex-grow ml-64 p-4">
                    <h1 className="text-4xl font-bold text-center p-4">
                        React Router Example
                    </h1>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/about" element={<About />} />
                        <Route path="/contact" element={<Contact />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
};

export default App;
