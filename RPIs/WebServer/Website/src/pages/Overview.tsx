import React from 'react';
import LIDARPlot from '../components/LIDAR/LIDARPlot.js';

const Overview: React.FC = () => {
    return (
        <div>
            <div className="bg-white dark:bg-slate-800 text-black dark:text-white">
                Robot Overview
            </div>
            <div>
                <h2 className="text-center text-xl font-bold p-4">
                    Polar plot of LIDAR data
                </h2>
                <LIDARPlot />
            </div>
        </div>
    );
};

export default Overview;
