import React, { useState, useEffect, useRef } from 'react';
import { Send, User, Bot, LogOut, Loader2, Lock, Mail, MessageSquare, AlertCircle } from 'lucide-react';


const AUTH_API_BASE = "http://localhost:8001"; 
const LOGIN_ENDPOINT = `${AUTH_API_BASE}/api/auth/login`; 
const REGISTER_ENDPOINT = `${AUTH_API_BASE}/api/auth/register`; 
const CHAT_ENDPOINT = "http://localhost:8100/v1/chat";


const generateSessionId = () => {
  return 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
};

const Spinner = () => <Loader2 className="w-5 h-5 animate-spin" />;

export default function App() {
  const [userToken, setUserToken] = useState(localStorage.getItem('access_token'));
  const [view, setView] = useState(userToken ? 'chat' : 'login');
  
  const [sessionId, setSessionId] = useState(localStorage.getItem('session_id') || '');
  const [messages, setMessages] = useState([
    { id: 1, sender: 'bot', text: 'Xin chào! Tôi có thể giúp gì cho bạn hôm nay? 🍜' }
  ]);
  const [inputText, setInputText] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auth Handlers
  const handleLoginSuccess = (token) => {
    localStorage.setItem('access_token', token);
    setUserToken(token);
    
    // Nếu chưa có session_id thì tạo mới
    let currentSession = localStorage.getItem('session_id');
    if (!currentSession) {
        currentSession = generateSessionId();
        localStorage.setItem('session_id', currentSession);
    }
    setSessionId(currentSession);
    
    setView('chat');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('session_id');
    setUserToken(null);
    setSessionId('');
    setMessages([{ id: 1, sender: 'bot', text: 'Xin chào! Tôi có thể giúp gì cho bạn hôm nay? 🍜' }]);
    setView('login');
  };

  // Chat Handler (Real Fetch)
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isSending) return;

    const userMsgText = inputText;
    setInputText(''); // Clear input

    const newUserMsg = { id: Date.now(), sender: 'user', text: userMsgText };
    setMessages(prev => [...prev, newUserMsg]);
    setIsSending(true);

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          message: userMsgText,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        if (response.status === 401) {
            handleLogout(); // Token hết hạn -> Logout
            throw new Error("Phiên đăng nhập hết hạn.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      const data = await response.json();
      
      // Giả sử server trả về { response: "..." } hoặc { output: "..." }
      const botMsgText = data.response || data.output || JSON.stringify(data);
      
      const newBotMsg = { id: Date.now() + 1, sender: 'bot', text: botMsgText };
      setMessages(prev => [...prev, newBotMsg]);

    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg = { 
        id: Date.now() + 1, 
        sender: 'bot', 
        text: `⚠️ Lỗi: ${error.message}. Vui lòng thử lại.` 
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  // Render Views
  if (view === 'login') {
    return <AuthForm type="login" onSwitch={() => setView('register')} onSuccess={handleLoginSuccess} />;
  }

  if (view === 'register') {
    return <AuthForm type="register" onSwitch={() => setView('login')} onSuccess={() => setView('login')} />;
  }

  // Chat View
  return (
    <div className="flex flex-col h-screen bg-gray-50 font-sans text-gray-800">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2.5 rounded-xl text-white shadow-blue-200 shadow-md">
            <MessageSquare size={22} />
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-lg leading-tight">Food Assistant</h1>
            <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <p className="text-xs text-gray-500 font-mono">ID: {sessionId.slice(0, 8)}</p>
            </div>
          </div>
        </div>
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 text-gray-500 hover:text-red-600 hover:bg-red-50 px-3 py-2 rounded-lg transition-all text-sm font-medium"
        >
          <LogOut size={18} />
          <span className="hidden sm:inline">Đăng xuất</span>
        </button>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 bg-gray-50">
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex max-w-[85%] md:max-w-[70%] gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar */}
              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm ${
                msg.sender === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white border border-gray-200 text-emerald-600'
              }`}>
                {msg.sender === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>

              {/* Bubble */}
              <div className={`p-3.5 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed whitespace-pre-wrap ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
              }`}>
                {msg.text}
              </div>
            </div>
          </div>
        ))}
        
        {/* Loading State */}
        {isSending && (
          <div className="flex justify-start w-full">
             <div className="flex max-w-[80%] gap-3">
               <div className="w-9 h-9 rounded-full bg-white border border-gray-200 text-emerald-600 flex items-center justify-center shadow-sm">
                 <Bot size={18} />
               </div>
               <div className="bg-white border border-gray-200 p-4 rounded-2xl rounded-tl-none flex items-center gap-2 shadow-sm">
                 <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                 <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                 <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
               </div>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="bg-white p-4 border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
        <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Bạn muốn ăn gì hôm nay? (Ví dụ: 1 phần cơm tấm...)"
            className="flex-1 bg-gray-100 border border-transparent text-gray-900 text-sm rounded-full focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent block w-full p-4 pl-6 outline-none transition-all"
            disabled={isSending}
          />
          <button 
            type="submit" 
            disabled={!inputText.trim() || isSending}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-full w-14 h-14 flex items-center justify-center transition-all shadow-lg hover:shadow-blue-200 active:scale-95"
          >
            {isSending ? <Spinner /> : <Send size={22} />}
          </button>
        </form>
      </footer>
    </div>
  );
}

// --- AUTH COMPONENT (REAL FETCH) ---
function AuthForm({ type, onSwitch, onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const isLogin = type === 'login';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    const url = isLogin ? LOGIN_ENDPOINT : REGISTER_ENDPOINT;
    

    const payload = { email, password };

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json' 
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        // Xử lý lỗi từ server trả về (Validation Error hoặc Auth Error)
        const errorMessage = data.detail || data.message || "Thao tác thất bại. Vui lòng kiểm tra lại.";
        throw new Error(errorMessage);
      }

      // Xử lý thành công
      if (isLogin) {
        // Login trả về: { access_token: "...", token_type: "bearer" }
        if (data.access_token) {
            onSuccess(data.access_token);
        } else {
            throw new Error("Không nhận được token từ server.");
        }
      } else {
        // Register trả về message
        setSuccessMsg(data.message || "Đăng ký thành công! Đang chuyển hướng...");
        setTimeout(() => {
            // Reset form và chuyển sang Login
            setEmail('');
            setPassword('');
            onSwitch(); 
        }, 1500);
      }

    } catch (err) {
      console.error("Auth Error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4 font-sans">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-gray-100">
        <div className="bg-blue-600 p-8 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-blue-600 to-blue-800 opacity-90"></div>
          <div className="relative z-10">
            <h2 className="text-3xl font-bold text-white mb-2">{isLogin ? 'Đăng Nhập' : 'Đăng Ký'}</h2>
            <p className="text-blue-100 text-sm opacity-90">
                {isLogin ? 'Chào mừng bạn quay trở lại với Food Assistant!' : 'Tạo tài khoản mới trong vài giây.'}
            </p>
          </div>
        </div>

        <div className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="email"
                  required
                  className="block w-full pl-11 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Mật khẩu</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="password"
                  required
                  className="block w-full pl-11 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            {/* Error & Success Messages */}
            {error && (
                <div className="flex items-start gap-2 text-red-600 text-sm bg-red-50 p-3 rounded-lg border border-red-100">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span>{error}</span>
                </div>
            )}
            {successMsg && (
                <div className="text-emerald-600 text-sm bg-emerald-50 p-3 rounded-lg border border-emerald-100 text-center font-medium">
                    {successMsg}
                </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-3.5 px-4 border border-transparent rounded-lg shadow-md text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-70 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {loading && <Spinner />}
              {isLogin ? 'Đăng Nhập' : 'Đăng Ký Tài Khoản'}
            </button>
          </form>

          <div className="mt-8 text-center pt-6 border-t border-gray-100">
            <p className="text-sm text-gray-600">
              {isLogin ? "Chưa có tài khoản? " : "Đã có tài khoản? "}
              <button 
                type="button" // Important to prevent form submit
                onClick={onSwitch}
                className="font-bold text-blue-600 hover:text-blue-800 focus:outline-none hover:underline transition-colors"
              >
                {isLogin ? 'Đăng ký ngay' : 'Đăng nhập ngay'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}