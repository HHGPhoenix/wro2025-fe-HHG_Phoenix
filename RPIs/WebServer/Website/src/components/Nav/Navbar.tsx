import React from 'react';
import { Link } from 'react-router-dom';

const Navbar: React.FC = () => {
    return (
        <nav className="fixed top-0 left-0 h-full w-32 font-bold text-lg bg-slate-300 dark:bg-slate-800 text-black dark:text-white rounded-r-lg shadow-lg p-4">
            <ul className="space-y-6">
                <li>
                    <Link
                        to="/"
                        className="block py-2 px-4 rounded hover:bg-slate-400 dark:hover:bg-slate-700 transition duration-300"
                    >
                        Home
                    </Link>
                </li>
                <li>
                    <Link
                        to="/stream"
                        className="block py-2 px-4 rounded hover:bg-slate-400 dark:hover:bg-slate-700 transition duration-300"
                    >
                        Stream
                    </Link>
                </li>
                <li>
                    <Link
                        to="/lidar"
                        className="block py-2 px-4 rounded hover:bg-slate-400 dark:hover:bg-slate-700 transition duration-300"
                    >
                        LIDAR
                    </Link>
                </li>
                <li>
                    <Link
                        to="/log"
                        className="block py-2 px-4 rounded hover:bg-slate-400 dark:hover:bg-slate-700 transition duration-300"
                    >
                        Log
                    </Link>
                </li>
                <li>
                    <Link
                        to="/system"
                        className="block py-2 px-4 rounded hover:bg-slate-400 dark:hover:bg-slate-700 transition duration-300"
                    >
                        System
                    </Link>
                </li>
            </ul>
        </nav>
    );
};

export default Navbar;
