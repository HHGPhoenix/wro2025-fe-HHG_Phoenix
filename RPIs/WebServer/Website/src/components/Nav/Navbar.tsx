import React from 'react';
import { Link } from 'react-router-dom';

const Navbar: React.FC = () => {
    return (
        <nav className="fixed top-0 left-0 h-full w-32 bg-gray-800 text-white rounded-r-lg shadow-lg p-4">
            <ul className="space-y-6">
                <li>
                    <Link
                        to="/"
                        className="block py-2 px-4 rounded hover:bg-gray-700 transition duration-300"
                    >
                        Home
                    </Link>
                </li>
                <li>
                    <Link
                        to="/stream"
                        className="block py-2 px-4 rounded hover:bg-gray-700 transition duration-300"
                    >
                        Stream
                    </Link>
                </li>
                <li>
                    <Link
                        to="/lidar"
                        className="block py-2 px-4 rounded hover:bg-gray-700 transition duration-300"
                    >
                        LIDAR
                    </Link>
                </li>
            </ul>
        </nav>
    );
};

export default Navbar;
