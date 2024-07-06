import React from 'react';
import phoenixLogo from '../../assets/phoenix_logo.png'; // Adjust the path as necessary

const Header: React.FC = () => {
    return (
        <header className="bg-gray-800 text-white p-5">
            <div className="container mx-auto flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold">HHG_Phoenix</h1>
                    <p className="text-xl mt-2">Robot Information Interface</p>
                </div>
                <img src={phoenixLogo} alt="Phoenix Logo" className="h-16" />
            </div>
        </header>
    );
};

export default Header;
