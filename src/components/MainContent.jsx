import React, { useState, useEffect, useCallback, useRef } from 'react';
import image1 from '../assets/anh1.jpg';
import image2 from '../assets/anh2.jpg';
import image3 from '../assets/anh3.jpg';
import image4 from '../assets/anh4.jpg';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = "https://60f5-35-187-248-252.ngrok-free.app";
const CHAT_API_ENDPOINT = `${API_BASE_URL}/chat`;
const SLIDESHOW_INTERVAL = 5000;
const SLIDESHOW_TRANSITION = 300;

export default function MainContent({ message }) {
  const images = [image1, image2, image3, image4].filter(img => img);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [fade, setFade] = useState(true);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [displaySessionId, setDisplaySessionId] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);
  
  useEffect(() => {
    const lastMessage = chatMessages[chatMessages.length - 1];
    if (lastMessage && lastMessage.type === 'bot' && !isChatOpen) {
      setUnreadCount(prev => prev + 1);
    }
  }, [chatMessages, isChatOpen]);

  useEffect(() => {
    if (isChatOpen) {
      setUnreadCount(0);
    }
  }, [isChatOpen]);

  const nextSlide = useCallback(() => {
    if (images.length === 0) return;
    setFade(false);
    setTimeout(() => {
      setCurrentImageIndex((prevIndex) => (prevIndex + 1) % images.length);
      setFade(true);
    }, SLIDESHOW_TRANSITION);
  }, [images.length]);

  const prevSlide = useCallback(() => {
    if (images.length === 0) return;
    setFade(false);
    setTimeout(() => {
      setCurrentImageIndex((prevIndex) => (prevIndex - 1 + images.length) % images.length);
      setFade(true);
    }, SLIDESHOW_TRANSITION);
  }, [images.length]);

  useEffect(() => {
    if (images.length > 1) {
      const interval = setInterval(nextSlide, SLIDESHOW_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [images.length, nextSlide]);

  useEffect(() => {
    let sessionIdForDisplay = null;
    try {
      const storedUser = localStorage.getItem('currentUser');
      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        sessionIdForDisplay = parsedUser?.session_id;
        if (sessionIdForDisplay) {
          console.log("Session ID found in localStorage for display:", sessionIdForDisplay);
          setDisplaySessionId(sessionIdForDisplay);
        } else {
          console.warn("Session ID not found within stored user data.");
          navigate('/login');
        }
      } else {
         console.info("No 'currentUser' found in localStorage.");
         navigate('/login');
      }
    } catch (e) {
      console.error("Error reading or parsing 'currentUser' from localStorage:", e);
      localStorage.removeItem('currentUser');
      navigate('/login');
    }
  }, [navigate]);

  const handleSendMessage = useCallback(async () => {
    const queryToSend = newMessage.trim();
    if (queryToSend === '' || isLoading) {
      return;
    }

    const storedUser = localStorage.getItem('currentUser');
    let session_id = null;
    if (storedUser) {
      const parsedUser = JSON.parse(storedUser);
      session_id = parsedUser?.session_id;
    }

    if (!session_id) {
      console.error("Session ID not found. Redirecting to login.");
      navigate('/login');
      return;
    }

    const userMsg = { type: 'user', text: queryToSend };
    setChatMessages(prev => [...prev, userMsg]);
    setNewMessage('');
    setIsLoading(true);

    try {
      console.log("Sending query to backend:", queryToSend);
      const response = await fetch(CHAT_API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session_id}`,
        },
        body: JSON.stringify({
          query: queryToSend,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error(`API Error Response (${response.status}):`, data);
        const errorDetail = data.detail || `Yêu cầu thất bại với mã trạng thái ${response.status}`;
        throw new Error(errorDetail);
      }

      console.log("API Success Response:", data);

      const botReply = {
        type: 'bot',
        text: data.response || "Xin lỗi, tôi không nhận được phản hồi hợp lệ."
      };
      setChatMessages(prev => [...prev, botReply]);

      if (data.session_id && data.session_id !== displaySessionId) {
        setDisplaySessionId(data.session_id);
        const updatedUser = JSON.parse(localStorage.getItem('currentUser'));
        updatedUser.session_id = data.session_id;
        localStorage.setItem('currentUser', JSON.stringify(updatedUser));
      }

    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = error.message || "Đã xảy ra lỗi khi gửi tin nhắn.";
      setChatMessages(prev => [...prev, { type: 'bot', text: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  }, [newMessage, isLoading, navigate, displaySessionId]);

  const handleInputChange = (e) => {
    setNewMessage(e.target.value);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSendMessage();
    }
  };

  const formatTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
    if (!isChatOpen) {
      setUnreadCount(0);
      // Focus vào input khi mở chat
      setTimeout(() => {
        const inputElement = document.getElementById('chat-input');
        if (inputElement) inputElement.focus();
      }, 100);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Hero Section với Slideshow cải tiến */}
      <div className="relative w-full h-80 md:h-96 overflow-hidden shadow-md">
        {images.map((img, index) => (
          <img
            key={index}
            src={img}
            alt={`Slide ${index + 1}`}
            className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity duration-${SLIDESHOW_TRANSITION} ${index === currentImageIndex ? (fade ? 'opacity-100' : 'opacity-0') : 'opacity-0'}`}
          />
        ))}
        
        {/* Overlay gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 to-black/60 flex items-center justify-center">
          <div className="text-center text-white p-6 max-w-2xl">
            <h1 className="text-3xl md:text-4xl font-bold mb-4">Chào mừng đến trang web của viện bảo tàng lịch sử Việt Nam</h1>
            <p className="text-lg mb-6 text-gray-100">Hãy cùng nhau tìm hiểu về lịch sử</p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-full font-medium transition-colors duration-300 shadow-lg">
              Bắt đầu ngay
            </button>
          </div>
        </div>
        
        {/* Nút điều hướng cải tiến */}
        {images.length > 1 && (
          <>
            <button 
              onClick={prevSlide} 
              className="absolute top-1/2 left-4 transform -translate-y-1/2 bg-white bg-opacity-30 hover:bg-opacity-50 text-white rounded-full p-3 transition-all duration-300"
              aria-label="Previous slide"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </button>
            <button 
              onClick={nextSlide} 
              className="absolute top-1/2 right-4 transform -translate-y-1/2 bg-white bg-opacity-30 hover:bg-opacity-50 text-white rounded-full p-3 transition-all duration-300"
              aria-label="Next slide"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
              </svg>
            </button>
          </>
        )}
        
        {/* Indicators */}
        <div className="absolute bottom-4 left-0 right-0 flex justify-center space-x-2">
          {images.map((_, index) => (
            <button
              key={`indicator-${index}`}
              onClick={() => {
                setFade(false);
                setTimeout(() => {
                  setCurrentImageIndex(index);
                  setFade(true);
                }, SLIDESHOW_TRANSITION);
              }}
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                index === currentImageIndex 
                  ? 'bg-white w-6' 
                  : 'bg-white/50 hover:bg-white/80'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </div>

      {/* Nội dung chính của trang */}
      <div className="container mx-auto my-8 px-4 md:px-8 flex-1">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Các phần nội dung mẫu, có thể thay thế bằng nội dung thực */}
          <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800">Tính năng 1</h3>
            <p className="text-gray-600">Mô tả chi tiết về tính năng và lợi ích mà nó mang lại cho người dùng.</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800">Tính năng 2</h3>
            <p className="text-gray-600">Mô tả chi tiết về tính năng và lợi ích mà nó mang lại cho người dùng.</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-300">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold mb-2 text-gray-800">Tính năng 3</h3>
            <p className="text-gray-600">Mô tả chi tiết về tính năng và lợi ích mà nó mang lại cho người dùng.</p>
          </div>
        </div>
      </div>

      {/* Chat Widget */}
      <div 
        ref={chatContainerRef}
        className={`fixed bottom-5 right-5 flex flex-col z-50 transition-all duration-300 ease-in-out ${isChatOpen ? 'w-80 md:w-96 h-96 md:h-112' : 'w-16 h-16'}`}
      >
        {/* Chat Box */}
        {isChatOpen && (
          <div className="flex flex-col h-full bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-200 animate-fadeIn">
            {/* Chat Header */}
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
              <div className="flex items-center">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white/20 mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-medium text-sm">Trợ lý ảo</h3>
                  <div className="flex items-center text-xs text-blue-100">
                    <div className="w-2 h-2 rounded-full bg-green-400 mr-1"></div>
                    <span>Trực tuyến</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center">
                <button 
                  onClick={toggleChat}
                  className="p-1 rounded-full hover:bg-white/20 transition-colors"
                  aria-label="Minimize chat"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
              {chatMessages.length === 0 ? ( 
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <div className="w-16 h-16 mb-4 rounded-full bg-blue-100 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="text-center font-medium mb-1">Chào mừng bạn!</p>
                  <p className="text-center text-sm">Hãy đặt câu hỏi để bắt đầu trò chuyện</p>
                </div>
              ) : (
                chatMessages.map((msg, index) => (
                  <div key={index} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} mb-3`}>
                    {msg.type === 'bot' && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2 flex-shrink-0">
                        <span className="text-blue-600 text-xs font-bold">AI</span>
                      </div>
                    )}
                    <div 
                      className={`max-w-3/4 rounded-2xl py-2.5 px-4 ${
                        msg.type === 'user' 
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none shadow-sm' 
                          : 'bg-white text-gray-700 rounded-bl-none shadow-sm border border-gray-100'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                      <span className="block text-right mt-1 text-xs opacity-70">{formatTime()}</span>
                    </div>
                    {msg.type === 'user' && (
                      <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center ml-2 flex-shrink-0">
                        <span className="text-white text-xs font-bold">B</span>
                      </div>
                    )}
                  </div>
                ))
              )}
              {isLoading && (
                <div className="flex justify-start mb-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-2 flex-shrink-0">
                    <span className="text-blue-600 text-xs font-bold">AI</span>
                  </div>
                  <div className="bg-white text-gray-700 rounded-2xl rounded-bl-none py-2.5 px-4 shadow-sm border border-gray-100">
                    <div className="flex space-x-1.5 items-center h-5">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area */}
            <div className="border-t border-gray-100 p-3 bg-white">
              <div className="flex items-center bg-gray-100 rounded-full overflow-hidden pr-1.5 focus-within:ring-2 focus-within:ring-blue-300 focus-within:bg-white transition-all duration-300">
                <input
                  id="chat-input"
                  type="text"
                  className="flex-1 bg-transparent py-2.5 px-4 text-sm focus:outline-none"
                  placeholder="Nhập tin nhắn..."
                  value={newMessage}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                />
                <button
                  className={`rounded-full p-2.5 transition-all duration-300 ${isLoading || newMessage.trim() === '' 
                    ? 'bg-gray-300 text-gray-400 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:shadow-md'}`}
                  onClick={handleSendMessage}
                  disabled={isLoading || newMessage.trim() === ''}
                  aria-label="Gửi tin nhắn"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Chat Button - luôn hiển thị khi đóng */}
        {!isChatOpen && (
          <button 
            onClick={toggleChat}
            className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg hover:shadow-xl flex items-center justify-center hover:scale-105 transition-all duration-300 relative"
            aria-label="Mở chat"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            
            {/* Hiển thị số tin nhắn chưa đọc */}
            {unreadCount > 0 && (
              <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold w-6 h-6 flex items-center justify-center rounded-full border-2 border-white animate-pulse">
                {unreadCount}
              </div>
            )}
          </button>
        )}
      </div>
      
      {/* Session ID Badge */}
      {displaySessionId && (
        <div className="fixed top-4 right-4 z-10">
          <div className="bg-blue-50 text-blue-800 text-xs font-medium px-3 py-1.5 rounded-full border border-blue-200 flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
            <span>Session: {displaySessionId?.substring(0, 8)}...</span>
          </div>
        </div>
      )}
    </div>
  );
}