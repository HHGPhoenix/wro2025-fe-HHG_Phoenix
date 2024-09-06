import React from 'react';
import LIDARPlot from '../components/LIDAR/LIDARPlot.js';
import StreamSite from './Vidstreams.js';
import LastLog from '../components/LOG/LastLog.js';
import SystemStats from '../components/System/SystemStats.js';

const Overview: React.FC = () => {
    return (
        <div className="text-black dark:text-white">
            <div className="grid grid-cols-2 gap-4 p-4">
                <div className="w-full h-full flex justify-center">
                    <div className="w-2/3 h-2/3">
                        <h2 className="text-center text-3xl font-bold p-4">
                            Polar plot of LIDAR data
                        </h2>
                        <LIDARPlot />
                    </div>
                </div>
                <div className="flex flex-col items-center">
                    <h2 className="text-center text-3xl font-bold p-4">
                        Video Streams
                    </h2>
                    <StreamSite />
                </div>
                <div>
                    <h2 className="text-center text-3xl font-bold p-4">
                        Last Log
                    </h2>
                    <LastLog logAmount={5} />
                </div>
                <div>
                    <h2 className="text-center text-3xl font-bold p-4">
                        System Stats
                    </h2>
                    <SystemStats />
                </div>
            </div>
        </div>
    );
};

export default Overview;
