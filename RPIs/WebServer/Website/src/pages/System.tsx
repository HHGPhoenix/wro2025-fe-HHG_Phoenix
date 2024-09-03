import React from 'react';
import SystemStats from '../components/System/SystemStats.js';

const System: React.FC = () => {
    return (
        <div className="flex items-center justify-center">
            <div className="w-6/12 self-center">
                <h2 className="text-center text-3xl font-bold p-4 text-black dark:text-white">
                    System Information
                </h2>
                <SystemStats />
            </div>
        </div>
    );
};

export default System;
