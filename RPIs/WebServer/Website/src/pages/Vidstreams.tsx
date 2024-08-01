import React, { useState } from 'react';

// Define the video streams array
const videoStreams = [
    { label: 'Raw Video Stream', url: '/cam/raw_video_stream' },
    { label: 'Simplified Video Stream', url: '/cam/simplified_video_stream' },
    { label: 'Object Video Stream', url: '/cam/object_video_stream' },
    // Add more streams here if needed
];

const StreamSite: React.FC = () => {
    // Initialize state with the first video stream URL
    const [currentStream, setCurrentStream] = useState<string>(
        videoStreams[0].url
    );

    return (
        <div>
            <h1>Video Stream Switcher</h1>
            <div>
                {/* Dynamically generate buttons based on the videoStreams array */}
                {videoStreams.map((stream, index) => (
                    <button
                        key={index}
                        onClick={() => setCurrentStream(stream.url)}
                    >
                        {stream.label}
                    </button>
                ))}
            </div>
            <div style={{ marginTop: '20px' }}>
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
        <div>
            {/* Display the video stream */}
            <img
                src={url}
                alt="Video Stream"
                style={{ width: '640px', height: '360px' }}
            />
        </div>
    );
};

export default StreamSite;
