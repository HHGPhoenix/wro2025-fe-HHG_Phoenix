import React, { useState } from 'react';
import LIDARPlot from '../components/LIDAR/LIDARPlot.js';

const LIDAR: React.FC = () => {
    const [useInterpolated, setUseInterpolated] = useState(false);

    const handleToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
        setUseInterpolated(event.target.value === 'interpolated');
    };

    const lidarDataURL = useInterpolated
        ? '/lidar/interpolated_data'
        : '/lidar/data';

    return (
        <div className="bg-white dark:bg-slate-700 text-black dark:text-white">
            <h2 className="text-center text-3xl font-bold p-4">
                Polar plot of LIDAR data
            </h2>
            <LIDARPlot />
        </div>
    );
};

export default LIDAR;
