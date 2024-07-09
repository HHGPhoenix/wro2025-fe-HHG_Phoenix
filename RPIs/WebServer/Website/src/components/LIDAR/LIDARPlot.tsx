import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';
import { io } from 'socket.io-client';

const LIDARPlot: React.FC = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const chartRef = useRef<Chart | null>(null);

    useEffect(() => {
        const socket = io();

        socket.on('connect', () => {
            console.log('WebSocket connection established');
        });

        socket.on('lidar_data', (data: any) => {
            const updatedData = data.map(
                (arr: [number, number, number]) => arr
            ); // Assuming data is now [angle, distance, intensity]
            updateChart(updatedData);
        });

        socket.on('disconnect', () => {
            console.log('WebSocket connection closed');
        });

        return () => {
            socket.disconnect();
            if (chartRef.current) {
                chartRef.current.destroy();
                chartRef.current = null;
            }
        };
    }, []);

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

        if (chartRef.current) {
            chartRef.current.data.labels = data.labels;
            chartRef.current.data.datasets[0].data = completeData;
            chartRef.current.data.datasets[0].borderColor = pointColors;
            chartRef.current.update();
        } else if (canvasRef.current) {
            const context = canvasRef.current.getContext('2d');
            if (context) {
                chartRef.current = new Chart(context, {
                    type: 'radar',
                    data: data,
                    options: {
                        scales: {
                            r: {
                                beginAtZero: true,
                                suggestedMin: 0,
                                suggestedMax: 2500,
                                angleLines: { display: true },
                                grid: { circular: true },
                            },
                        },
                        elements: {
                            line: { borderWidth: 0 },
                            point: { radius: 3 },
                        },
                        animation: {
                            duration: 0,
                        },
                        plugins: {
                            legend: { display: false },
                        },
                    },
                });
            }
        }
    };

    return (
        <div className="w-full h-auto max-w-3xl mx-auto p-4">
            <canvas ref={canvasRef} className="w-full h-full"></canvas>
        </div>
    );
};

export default LIDARPlot;
