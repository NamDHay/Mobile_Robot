import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/logo.png';
import userIcon from '../assets/user-icon.png';

export default function Navbar({ onLogout }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
   try {
    setIsLoggingOut(true);

   // Get current user from localStorage to get both id and session_id
   const currentUser = JSON.parse(localStorage.getItem('currentUser'));

   if (currentUser && currentUser.id && currentUser.session_id) {
    // Call logout endpoint with Authorization header
    const response = await fetch(`https://60f5-35-187-248-252.ngrok-free.app/logout/${currentUser.id}`, {
     method: 'POST',
     headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${currentUser.session_id}`, // Add Authorization header
     },
    });

    if (response.ok) {
     // Remove user from local storage
     localStorage.removeItem('currentUser');

     // Call the onLogout callback if provided
     if (onLogout) {
      onLogout();
     }

     // Redirect to login page
     navigate('/login');
    } else {
     console.error('Logout failed');
     const errorData = await response.json();
     alert(`Đã xảy ra lỗi khi đăng xuất: ${errorData.message || 'Lỗi không xác định'}`);
    }
   } else {
    console.warn('User data or session ID not found in localStorage.');
    // If no user data or session, just clear localStorage and redirect
    localStorage.removeItem('currentUser');
    navigate('/login');
   }
  } catch (error) {
   console.error('Error during logout:', error);
   alert('Đã xảy ra lỗi khi đăng xuất');
  } finally {
   setIsLoggingOut(false);
   setIsDropdownOpen(false);
  }
 };

 return (
  <nav className="bg-white text-gray-800 px-8 py-5 flex justify-between items-center shadow-md relative text-base h-20 font-sans">
   <div>
    <img src={logo} alt="Logo" className="h-14 cursor-pointer" onClick={() => navigate('/home')} />
   </div>
   <div className="space-x-10 font-semibold">
    <button onClick={() => navigate('/home')} className="hover:text-blue-600 transition-colors duration-300">Home</button>
    <a href="#" className="hover:text-blue-600 transition-colors duration-300">Status</a>
    <a href="#" className="hover:text-blue-600 transition-colors duration-300">About</a>
   </div>
   <div className="relative">
    <button onClick={() => setIsDropdownOpen(!isDropdownOpen)}>
     <img src={userIcon} alt="User" className="w-12 h-12 rounded-full border-2 border-gray-300 hover:scale-105 transition-transform" />
    </button>
    {isDropdownOpen && (
     <div className="absolute right-0 mt-2 w-52 bg-white shadow-lg rounded-lg py-2 text-gray-800 z-10 animate-fade-in font-medium">
      <button
       onClick={handleLogout}
       className="block w-full text-left px-4 py-3 hover:bg-gray-100 rounded-t-lg disabled:text-gray-400"
       disabled={isLoggingOut}
      >
       {isLoggingOut ? 'Đang đăng xuất...' : 'Đăng xuất'}
      </button>
      <button className="block w-full text-left px-4 py-3 hover:bg-gray-100">Thay đổi tài khoản</button>
      <button className="block w-full text-left px-4 py-3 hover:bg-gray-100 rounded-b-lg">Cài đặt</button>
     </div>
    )}
   </div>
  </nav>
 );
}