import React, { useState } from 'react';

// Define the video streams array with both full and short labels
const videoStreams = [
    {
        label: 'Raw Video Stream',
        shortLabel: 'Raw',
        url: '/cam/raw_video_stream',
    },
    {
        label: 'Simplified Video Stream',
        shortLabel: 'Simple',
        url: '/cam/simplified_video_stream',
    },
    {
        label: 'Object Video Stream',
        shortLabel: 'Object',
        url: '/cam/object_video_stream',
    },
    // Add more streams here if needed
];

const StreamSite: React.FC = () => {
    const [currentStream, setCurrentStream] = useState<string>(
        videoStreams[0].url
    );

    return (
        <div className="p-6 flex flex-col justify-center">
            <h1 className="text-2xl font-bold mb-4">Video Stream Switcher</h1>
            <div className="space-x-2 mb-6">
                {/* Dynamically generate buttons based on the videoStreams array */}
                {videoStreams.map((stream, index) => (
                    <button
                        key={index}
                        onClick={() => setCurrentStream(stream.url)}
                        className="bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition duration-300"
                    >
                        {/* Use full label by default and short label on small screens */}
                        <span className="hidden sm:inline">{stream.label}</span>
                        <span className="inline md:hidden">
                            {stream.shortLabel}
                        </span>
                    </button>
                ))}
            </div>
            <div className="flex w-full justify-center">
                <VideoStream url={`${currentStream}`} />
            </div>
        </div>
    );
};

interface VideoStreamProps {
    url: string;
}

const VideoStream: React.FC<VideoStreamProps> = ({ url }) => {
    return (
        <div className="flex w-full justify-center">
            {/* Display the video stream */}
            <img src={url} alt="Video Stream" className="w-full max-h-full" />
        </div>
    );
};

export default StreamSite;
