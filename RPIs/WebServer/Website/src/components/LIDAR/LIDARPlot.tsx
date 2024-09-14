import React, { useEffect, useRef, useState } from 'react';
import Chart from 'chart.js/auto';
import { io } from 'socket.io-client';
import { color } from 'chart.js/helpers';

const LIDARPlot: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const chartRef = useRef<Chart | null>(null);
    const [dataType, setDataType] = useState<'normal' | 'interpolated'>(
        'normal'
    );

    useEffect(() => {
        const socket = io();

        socket.on('connect', () => {
            console.log('WebSocket connection established');
        });

        const handleLidarData = (data: any) => {
            const updatedData = data.map(
                (arr: [number, number, number]) => arr
            );
            updateChart(updatedData);
        };

        if (dataType === 'normal') {
            socket.on('lidar_data', handleLidarData);
            socket.off('interpolated_lidar_data');
        } else {
            socket.on('interpolated_lidar_data', handleLidarData);
            socket.off('lidar_data');
        }

        socket.on('disconnect', () => {
            console.log('WebSocket connection closed');
        });

        // Cleanup on component unmount
        return () => {
            socket.disconnect();
        };
    }, [dataType]);

    const interpolateColor = (
        startColor: number[],
        endColor: number[],
        factor: number
    ) => {
        const result = startColor.map((start, index) =>
            Math.round(start + factor * (endColor[index] - start))
        );
        return `rgba(${result[0]}, ${result[1]}, ${result[2]}, 1)`;
    };

    const updateChart = (lidarData: [number, number, number][]) => {
        const completeData = new Array(360).fill(null);
        const pointColors = new Array(360).fill('rgba(255, 99, 132, 1)');

        lidarData.forEach((point: [number, number, number]) => {
            const angle = Math.round(point[0]);
            const distance = point[1];
            const intensity = point[2];

            if (angle >= 0 && angle < 360) {
                completeData[359 - angle] = distance;

                // Generate color based on intensity
                const startColor = [255, 0, 0]; // Red
                const endColor = [0, 0, 255]; // Blue
                const factor = intensity / 50; // Assuming max intensity value is 50
                const intensityColor = interpolateColor(
                    startColor,
                    endColor,
                    factor
                );
                pointColors[359 - angle] = intensityColor;
            }
        });

        const data = {
            labels: completeData.map((_, index) => 360 - index),
            datasets: [
                {
                    label: 'LIDAR Data Points',
                    data: completeData,
                    backgroundColor: 'rgba(255, 99, 132, 0)',
                    pointBackgroundColor: pointColors,
                    borderColor: pointColors,
                    borderWidth: 1,
                    pointRadius: 3,
                    showLine: false,
                },
            ],
        };

        const colorMode = window.matchMedia('(prefers-color-scheme: dark)');

        const lightModeOptions = {
            type: 'radar',
            data: data,
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        suggestedMin: 0,
                        suggestedMax: 2500,
                        pointLabels: {
                            display: false,
                        },
                        angleLines: { display: true },
                        grid: {
                            circular: true,
                            color: 'rgba(0, 0, 0, 0.1)',
                        },
                        ticks: { color: 'black' },
                    },
                },
                elements: {
                    line: { borderWidth: 0 },
                    point: { radius: 3 },
                },
                animation: {
                    duration: 0, // Disable animation
                },
                plugins: {
                    legend: { display: false },
                    labels: { color: 'black' },
                },
            },
        };

        const darkModeOptions = {
            type: 'radar',
            data: data,
            options: {
                scales: {
                    r: {
                        beginAtZero: true,
                        suggestedMin: 0,
                        suggestedMax: 2500,
                        pointLabels: {
                            display: false,
                        },
                        angleLines: {
                            display: true,
                            color: 'rgba(255, 255, 255, 0.15)',
                        },
                        grid: {
                            circular: true,
                            color: 'rgba(255, 255, 255, 0.3)',
                        },
                        ticks: {
                            color: 'white',
                            backdropColor: 'rgba(0, 0, 0, 0.5)',
                        },
                    },
                },
                elements: {
                    line: { borderWidth: 0 },
                    point: { radius: 3 },
                },
                animation: {
                    duration: 0, // Disable animation
                },
                plugins: {
                    legend: { display: false },
                    labels: {
                        color: 'white',
                        font: { size: 14 },
                        backgroundColor: 'rgba(0, 0, 0, 1)',
                        display: false,
                    },
                },
            },
        };

        const options = colorMode.matches
            ? darkModeOptions.options
            : lightModeOptions.options;

        if (chartRef.current) {
            chartRef.current.data = data;
            chartRef.current.options = options;
            chartRef.current.update();
        } else if (canvasRef.current) {
            const context = canvasRef.current.getContext('2d');
            if (context) {
                chartRef.current = new Chart(context, {
                    type: 'radar',
                    data,
                    options,
                });
            }
        }
    };

    return (
        <div className="w-full h-auto max-w-3xl mx-auto p-4 bg-white dark:bg-slate-700 text-black dark:text-white">
            <div className="flex justify-evenly mb-4">
                <label className="flex flex-nowrap">
                    <input
                        type="radio"
                        name="lidar-data-type"
                        value="normal"
                        checked={dataType === 'normal'}
                        onChange={() => setDataType('normal')}
                    />
                    <div className="pl-3 text-lg">Normal Data</div>
                </label>
                <label className="flex flex-nowrap">
                    <input
                        type="radio"
                        name="lidar-data-type"
                        value="interpolated"
                        checked={dataType === 'interpolated'}
                        onChange={() => setDataType('interpolated')}
                    />
                    <div className="pl-3 text-lg">Interpolated Data</div>
                </label>
            </div>
            <canvas ref={canvasRef} className="w-full h-full"></canvas>
        </div>
    );
};

export default LIDARPlot;
