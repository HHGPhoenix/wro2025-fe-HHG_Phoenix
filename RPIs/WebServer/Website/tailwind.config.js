/** @type {import('tailwindcss').Config} */
export default {
    content: [
        './src/**/*.{js,jsx,ts,tsx}', // This includes all JavaScript, TypeScript, and JSX/TSX files in your src folder
    ],
    theme: {
        extend: {
            colors: {
                darkBackground: '#1f2937', // Custom dark background color
                lightGray: '#d1d5db', // Custom light gray color for hover effects
            },
        },
    },
    plugins: [],
};
