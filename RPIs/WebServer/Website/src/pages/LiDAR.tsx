import React from 'react';
import LIDARPlot from '../components/LIDAR/LIDARPlot.js';

const LIDAR: React.FC = () => {
    return (
        <div>
            <h2 className="text-center text-3xl font-bold p-4">
                Polar plot of LIDAR data
            </h2>
            <LIDARPlot />
        </div>
    );
};

export default LIDAR;
