import React, { useState, useEffect } from 'react';

interface LogEntry {
    timestamp: string;
    level: string;
    message: string;
}

const LastLog: React.FC<{ logAmount: number }> = ({ logAmount }) => {
    const [logEntries, setLogEntries] = useState<LogEntry[]>([]);

    async function fetchLastLog() {
        try {
            const response = await fetch(`/log/data/${logAmount}`);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data: string[] = await response.json(); // Assuming the data is an array of log entries
            console.log('Raw data:', data); // Log the raw data
            const parsedEntries = parseLogData(data);
            // parsedEntries.pop(); // Remove the last parsed entry
            setLogEntries(parsedEntries);
        } catch (error) {
            console.error(
                'There has been a problem with your fetch operation:',
                error
            );
        }
    }

    function parseLogData(data: string[]): LogEntry[] {
        return data
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
        fetchLastLog();
    }, [logAmount]);

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

export default LastLog;
