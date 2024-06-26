import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from '../components/Nav/Navbar.js';
import Home from '../pages/Home.js';
import About from '../pages/About.js';
import Contact from '../pages/Contact.js';
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
