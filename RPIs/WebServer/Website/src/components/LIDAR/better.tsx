import React, { useEffect, useRef, useCallback } from 'react';
import Chart from 'chart.js/auto';

const LIDARPlot: React.FC<{ lidarDataURL: string }> = ({ lidarDataURL }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const chartInstanceRef = useRef<Chart | null>(null);

    // Using useCallback to memoize the fetch function
    const fetchLidarData = useCallback(async () => {
        try {
            const response = await fetch(lidarDataURL);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return await response.json();
        } catch (error) {
            console.error(
                'There has been a problem with your fetch operation:',
                error
            );
            return null;
        }
    }, [lidarDataURL]); // useCallback dependency array

    useEffect(() => {
        const drawPolarPlot = async () => {
            const lidarData = await fetchLidarData();
            if (!lidarData) return;

            const completeData = new Array(360).fill(null);
            lidarData.forEach((point: [number, number]) => {
                const angle = Math.round(point[0]);
                if (angle >= 0 && angle < 360) {
                    completeData[angle] = point[1];
                }
            });

            const data = {
                labels: completeData.map((_, index) => index),
                datasets: [
                    {
                        label: 'LIDAR Data Points',
                        data: completeData,
                        backgroundColor: 'rgba(255, 99, 132, 0)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                        pointBorderColor: 'rgba(255, 99, 132, 1)',
                        pointRadius: 3,
                        showLine: false,
                    },
                ],
            };

            const config = {
                type: 'radar' as const,
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
                    startAngle: 0,
                },
            };

            if (canvasRef.current) {
                const context = canvasRef.current.getContext('2d');
                if (context) {
                    if (chartInstanceRef.current !== null) {
                        chartInstanceRef.current.destroy();
                    }
                    chartInstanceRef.current = new Chart(context, config);
                }
            }
        };

        drawPolarPlot();
        const interval = setInterval(drawPolarPlot, 200);

        return () => {
            clearInterval(interval);
            if (chartInstanceRef.current !== null) {
                chartInstanceRef.current.destroy();
            }
        };
    }, [fetchLidarData]); // useEffect dependency array includes fetchLidarData

    return (
        <div className="w-full h-auto max-w-3xl mx-auto p-4">
            <canvas ref={canvasRef} className="w-full h-full"></canvas>
        </div>
    );
};

export default LIDARPlot;
