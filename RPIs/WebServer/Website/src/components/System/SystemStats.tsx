import React, { useState, useEffect } from 'react';

function getSystemInfo(
    setPi5CpuUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi5RamUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi5DiskUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi5Temperature: React.Dispatch<React.SetStateAction<number>>,
    setPi4CpuUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi4RamUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi4DiskUsage: React.Dispatch<React.SetStateAction<number>>,
    setPi4Temperature: React.Dispatch<React.SetStateAction<number>>,
    setVoltage: React.Dispatch<React.SetStateAction<number>>
) {
    fetch('/system/usage')
        .then((response) => response.json())
        .then((data) => {
            setPi5CpuUsage(data.pi5_cpu_usage);
            setPi5RamUsage(data.pi5_memory_usage); // Assuming the third element is the percentage
            setPi5DiskUsage(data.pi5_disk_usage); // Assuming the fourth element is the percentage
            setPi5Temperature(data.pi5_temperature);

            setPi4CpuUsage(data.pi4_cpu_usage);
            setPi4RamUsage(data.pi4_memory_usage); // Assuming the third element is the percentage
            setPi4DiskUsage(data.pi4_disk_usage); // Assuming the fourth element is the percentage
            setPi4Temperature(data.pi4_temperature);

            setVoltage(data.voltage);
        });
}

const Bar: React.FC<{
    percentage: number;
    label: string;
    symbol?: string;
    shown_value?: number;
}> = ({ percentage, label, symbol, shown_value }) => {
    let displayed_value: number;

    if (symbol == null) {
        symbol = '%';
    }

    if (percentage < 0) {
        percentage = 0;
    } else if (percentage > 100) {
        percentage = 100;
    }

    if (shown_value == null) {
        displayed_value = percentage;
    } else {
        displayed_value = shown_value;
    }

    return (
        <div style={{ marginBottom: '10px' }}>
            <div>
                {label}: {displayed_value}
                {symbol}
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

const PercentageBar: React.FC<{
    low_number: number;
    high_number: number;
    current_number: number;
    title: string;
    symbol: string; // Add symbol prop
}> = ({ low_number, high_number, current_number, title, symbol }) => {
    const calculatePercentage = (
        low: number,
        high: number,
        current: number
    ) => {
        if (high === low) return 0;
        return ((current - low) / (high - low)) * 100;
    };

    const percentage = calculatePercentage(
        low_number,
        high_number,
        current_number
    );

    return (
        <div>
            <Bar
                percentage={percentage}
                label={title}
                symbol={symbol}
                shown_value={current_number}
            />{' '}
            {/* Pass symbol prop */}
        </div>
    );
};

const SystemStats: React.FC = () => {
    const [Pi5cpuUsage, setPi5CpuUsage] = useState(0);
    const [Pi5ramUsage, setPi5RamUsage] = useState(0);
    const [Pi5diskUsage, setPi5DiskUsage] = useState(0);
    const [Pi5temperature, setPi5Temperature] = useState(0);

    const [Pi4cpuUsage, setPi4CpuUsage] = useState(0);
    const [Pi4ramUsage, setPi4RamUsage] = useState(0);
    const [Pi4diskUsage, setPi4DiskUsage] = useState(0);
    const [Pi4temperature, setPi4Temperature] = useState(0);

    const [voltage, setVoltage] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            getSystemInfo(
                setPi5CpuUsage,
                setPi5RamUsage,
                setPi5DiskUsage,
                setPi5Temperature,
                setPi4CpuUsage,
                setPi4RamUsage,
                setPi4DiskUsage,
                setPi4Temperature,
                setVoltage
            );
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <>
            <div className="text-black dark:text-white">
                <h1 className="text-2xl pt-6">RPi 5</h1>
                <Bar percentage={Pi5cpuUsage} label="CPU Usage" />
                <Bar percentage={Pi5ramUsage} label="RAM Usage" />
                <Bar percentage={Pi5diskUsage} label="Disk Usage" />
                <PercentageBar
                    low_number={30}
                    high_number={70}
                    current_number={Pi5temperature}
                    title="Temperature"
                    symbol="°C"
                />
            </div>
            <div className="text-black dark:text-white">
                <h1 className="text-2xl pt-6">RPi 4</h1>
                <Bar percentage={Pi4cpuUsage} label="CPU Usage" />
                <Bar percentage={Pi4ramUsage} label="RAM Usage" />
                <Bar percentage={Pi4diskUsage} label="Disk Usage" />
                <PercentageBar
                    low_number={30}
                    high_number={70}
                    current_number={Pi4temperature}
                    title="Temperature"
                    symbol="°C"
                />
            </div>
            <div className="text-black dark:text-white pt-6">
                <PercentageBar
                    low_number={11.1}
                    high_number={12.6}
                    current_number={voltage}
                    title="Voltage"
                    symbol="V"
                />
            </div>
        </>
    );
};

export default SystemStats;
