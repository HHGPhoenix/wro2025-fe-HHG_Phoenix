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
        <div className="h-customfull min-h-customfull bg-white dark:bg-slate-700">
            <Router>
                <div className="App flex min-h-screen">
                    <Navbar />
                    <div className="flex-grow p-2 ml-32">
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
        </div>
    );
};

export default App;
