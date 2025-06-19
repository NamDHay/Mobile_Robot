// File: pages/Admin.jsx
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function Admin() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-6">MAP</h1>

        {/* Giả lập bản đồ */}
        <div className="w-full max-w-4xl h-[400px] bg-gray-100 border-2 border-gray-300 rounded-lg shadow-md mb-6 flex items-center justify-center">
          <p className="text-gray-500 italic">(Bản đồ hiển thị vị trí và đường đi của robot sẽ được tích hợp tại đây)</p>
        </div>

        {/* Nút quay lại */}
        <button
          onClick={() => navigate('/home')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg shadow hover:bg-blue-700 transition"
        >
          Quay lại Trang Chính
        </button>
      </main>
      <Footer />
    </div>
  );
}
