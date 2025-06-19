import React from 'react';
import background from '../assets/background.jpg';

export default function Layout({ children }) {
  return (
    <div
      className="min-h-screen bg-cover bg-center"
      style={{ backgroundImage: `url(${background})` }}
    >
      {/* Nền trắng mờ để dễ đọc nội dung */}
      <div className="bg-white bg-opacity-80 min-h-screen">
        {children}
      </div>
    </div>
  );
}
