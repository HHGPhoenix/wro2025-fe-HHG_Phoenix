import React, { useState, useEffect } from 'react';

const LastLog: React.FC<{ logAmount: number }> = ({ logAmount }) => {
    const [logData, setLogData] = useState<string>('');

    async function fetchLastLog() {
        try {
            const response = await fetch(`/log/data/${logAmount}`);
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
        fetchLastLog();
    }, []);

    return (
        <div className="max-h-500px border border-black p-4">
            <pre>{logData}</pre>
        </div>
    );
};

export default LastLog;
