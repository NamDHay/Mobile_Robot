import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await fetch('https://60f5-35-187-248-252.ngrok-free.app/register/', { // Endpoint đăng ký
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.status === 201) { // Backend trả về 201 khi đăng ký thành công
        // Lưu session_id nhận được từ backend
        localStorage.setItem('currentUser', JSON.stringify({
          username: username,
          session_id: data.session_id,
        }));
        navigate('/login'); // Chuyển hướng đến trang đăng nhập sau khi đăng ký thành công
      } else {
        setError(data.detail || 'Đăng ký không thành công!');
        console.error('Registration failed', data);
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Đã xảy ra lỗi khi đăng ký');
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-100">
      <form onSubmit={handleRegister} className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-center">Đăng ký</h2>
        {error && <div className="mb-4 p-2 bg-red-100 text-red-700 rounded">{error}</div>}
        <input
          type="text"
          placeholder="Tên đăng nhập"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full px-3 py-2 mb-4 border rounded"
          required
        />
        <input
          type="password"
          placeholder="Mật khẩu"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-3 py-2 mb-4 border rounded"
          required
        />
        <button type="submit" className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600">
          Đăng ký
        </button>
        <p className="mt-4 text-center">
          Đã có tài khoản? <Link to="/login" className="text-blue-500">Đăng nhập</Link>
        </p>
      </form>
    </div>
  );
}