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
        <div>
            <h2 className="text-center text-3xl font-bold p-4">
                Polar plot of LIDAR data
            </h2>
            <div className="flex justify-center p-4">
                <div className="flex items-center space-x-3">
                    <label>
                        <input
                            type="radio"
                            value="interpolated"
                            checked={useInterpolated}
                            onChange={handleToggle}
                            name="dataSelection"
                            className="form-radio"
                        />
                        <span className="text-lg">Use Interpolated Data</span>
                    </label>
                    <label>
                        <input
                            type="radio"
                            value="raw"
                            checked={!useInterpolated}
                            onChange={handleToggle}
                            name="dataSelection"
                            className="form-radio"
                        />
                        <span className="text-lg">Use Raw Data</span>
                    </label>
                </div>
            </div>
            <LIDARPlot lidarDataURL={lidarDataURL} />
        </div>
    );
};

export default LIDAR;
