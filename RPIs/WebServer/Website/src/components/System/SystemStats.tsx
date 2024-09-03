import React, { useState, useEffect } from 'react';

function getSystemInfo(
    setCpuUsage: React.Dispatch<React.SetStateAction<number>>,
    setRamUsage: React.Dispatch<React.SetStateAction<number>>,
    setDiskUsage: React.Dispatch<React.SetStateAction<number>>
) {
    fetch('/system/usage')
        .then((response) => response.json())
        .then((data) => {
            setCpuUsage(data.cpu_usage);
            setRamUsage(data.memory_usage[2]); // Assuming the third element is the percentage
            setDiskUsage(data.disk_usage[3]); // Assuming the fourth element is the percentage
        });
}

const Bar: React.FC<{ percentage: number; label: string }> = ({
    percentage,
    label,
}) => {
    return (
        <div style={{ marginBottom: '10px' }}>
            <div>
                {label}: {percentage}%
            </div>
            <div
                style={{
                    background: '#ccc',
                    width: '100%',
                    height: '20px',
                    borderRadius: '5px',
                }}
            >
                <div
                    style={{
                        background: '#4caf50',
                        width: `${percentage}%`,
                        height: '100%',
                        borderRadius: '5px',
                    }}
                ></div>
            </div>
        </div>
    );
};

const SystemStats: React.FC = () => {
    const [cpuUsage, setCpuUsage] = useState(0);
    const [ramUsage, setRamUsage] = useState(0);
    const [diskUsage, setDiskUsage] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            getSystemInfo(setCpuUsage, setRamUsage, setDiskUsage);
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="text-black dark:text-white">
            <Bar percentage={cpuUsage} label="CPU Usage" />
            <Bar percentage={ramUsage} label="RAM Usage" />
            <Bar percentage={diskUsage} label="Disk Usage" />
        </div>
    );
};

export default SystemStats;
