import React, { useState, useEffect } from 'react';

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
}

const FullLog: React.FC = () => {
    const [logEntries, setLogEntries] = useState<LogEntry[]>([]);

    async function fetchFullLog() {
        try {
            const response = await fetch('/log/full_data');
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.text(); // Assuming the data is plain text
            console.log('Raw data:', data); // Log the raw data
            const parsedEntries = parseLogData(data);
            parsedEntries.pop(); // Remove the last parsed entry
            setLogEntries(parsedEntries);
        } catch (error) {
            console.error(
                'There has been a problem with your fetch operation:',
                error
            );
        }
    }

    function parseLogData(data: string): LogEntry[] {
        // Remove the opening quotation mark and the last weird part
        data = data.replace(/^"|"[^"]*$/, '');
        // Ensure that the newline characters are properly recognized
        const lines = data.split('\\n');
        console.log('Parsed lines:', lines); // Log the parsed lines
        return lines
            .filter((line) => line.trim() !== '')
            .map((line) => {
                const [timestamp, level, ...messageParts] = line.split(' - ');
                console.log('Parsed line:', { timestamp, level, messageParts }); // Log each parsed line
                return {
                    timestamp,
                    level,
                    message: messageParts.join(' - '),
                };
            });
    }

    useEffect(() => {
        fetchFullLog();
        const intervalId = setInterval(fetchFullLog, 1000); // Fetch every second

        return () => clearInterval(intervalId); // Cleanup interval on unmount
    }, []);

    return (
        <div className="h-full flex-col">
            <div className="overflow-y-scroll scrollbar-thin scrollbar-thumb-rounded scrollbar-thumb-gray-500 scrollbar-track-gray-200 dark:scrollbar-thumb-gray-600 dark:scrollbar-track-gray-700 p-4 bg-slate-300 dark:bg-slate-800 rounded flex-grow">
                {logEntries.map((entry, index) => (
                    <div key={index} className="log-entry mb-2">
                        <div>
                            <strong>{entry.timestamp}</strong> -{' '}
                            <em>{entry.level}</em> - {entry.message}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default FullLog;
