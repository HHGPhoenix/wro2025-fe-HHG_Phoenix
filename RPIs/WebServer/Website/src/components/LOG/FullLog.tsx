import React, { useState, useEffect } from 'react';

const FullLog: React.FC = () => {
    const [logData, setLogData] = useState<string>('');

    async function fetchFullLog() {
        try {
            const response = await fetch('/log/full_data');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setLogData(JSON.stringify(data, null, 2)); // Assuming the data is JSON and converting it to a formatted string
        } catch (error) {
            console.error(
                'There has been a problem with your fetch operation:',
                error
            );
        }
    }

    useEffect(() => {
        fetchFullLog();
    }, []);

    return (
        <div className="max-h-500px overflow-y-scroll border border-black p-4">
            <pre>{logData}</pre>
        </div>
    );
};

export default FullLog;
