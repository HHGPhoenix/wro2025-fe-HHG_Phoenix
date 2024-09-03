import '../tailwind.css';
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from '../components/Nav/Navbar.js';
import Overview from '../pages/Overview.js';
import StreamSite from '../pages/Vidstreams.js';
import LIDAR from '../pages/LiDAR.js';
import Header from '../components/Misc/Header.js';
import Log from '../pages/Log.js';
import System from '../pages/System.js';

const App: React.FC = () => {
    return (
        <Router>
            <div className="App flex bg-white dark:bg-slate-700 h-screen">
                <Navbar />
                <div className="flex-grow ml-32 p-2">
                    <Header />
                    <Routes>
                        <Route path="/" element={<Overview />} />
                        <Route path="/stream" element={<StreamSite />} />
                        <Route path="/lidar" element={<LIDAR />} />
                        <Route path="/log" element={<Log />} />
                        <Route path="/system" element={<System />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
};

export default App;
