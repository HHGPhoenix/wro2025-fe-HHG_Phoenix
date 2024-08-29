import React from 'react';
import FullLog from '../components/LOG/FullLog.js';
import LastLog from '../components/LOG/LastLog.js';

const Log: React.FC = () => {
    return (
        <div className="bg-white dark:bg-slate-700 text-black dark:text-white">
            <h2 className="text-center text-3xl font-bold p-4">Log</h2>
            <FullLog />
            {/* <LastLog logAmount={10} /> */}
        </div>
    );
};

export default Log;
