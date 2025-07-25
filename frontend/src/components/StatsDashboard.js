// src/components/StatsDashboard.js - Updated with sidebar layout
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

// Stats Dashboard Component
const StatsDashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('overview');
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'ai',
      message: `Hello ${user?.full_name || 'there'}! I'm your Life Rank AI coach. I'm here to help you analyze your stats and improve your life score. What would you like to discuss today?`,
      timestamp: new Date().toISOString()
    }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  // Sample stats data - you'll replace this with real data from your API
  const [stats, setStats] = useState({
    overallScore: 7.2,
    categories: {
      health: { score: 8.1, trend: 'up', data: [6.5, 7.2, 7.8, 8.1] },
      career: { score: 6.8, trend: 'up', data: [5.2, 6.1, 6.5, 6.8] },
      relationships: { score: 7.5, trend: 'stable', data: [7.3, 7.6, 7.4, 7.5] },
      finances: { score: 6.2, trend: 'down', data: [7.1, 6.8, 6.5, 6.2] },
      personal: { score: 8.0, trend: 'up', data: [7.1, 7.5, 7.8, 8.0] },
      social: { score: 7.3, trend: 'stable', data: [7.1, 7.2, 7.4, 7.3] }
    },
    weeklyProgress: [6.8, 7.0, 6.9, 7.1, 7.2, 7.1, 7.2],
    goals: [
      { id: 1, title: 'Exercise 4x per week', progress: 75, category: 'health' },
      { id: 2, title: 'Save $500 monthly', progress: 60, category: 'finances' },
      { id: 3, title: 'Read 2 books per month', progress: 90, category: 'personal' },
      { id: 4, title: 'Network with 5 professionals', progress: 40, category: 'career' }
    ]
  });

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      message: newMessage,
      timestamp: new Date().toISOString()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setNewMessage('');
    setIsTyping(true);

    // Simulate AI response - you'll replace this with actual AI API call
    setTimeout(() => {
      const aiResponse = generateAIResponse(newMessage, stats);
      const aiMessage = {
        id: Date.now() + 1,
        sender: 'ai',
        message: aiResponse,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userMessage, userStats) => {
    // Simple AI response logic - replace with actual AI integration
    const message = userMessage.toLowerCase();
    
    if (message.includes('health') || message.includes('fitness')) {
      return `Great question about health! I see your health score is ${userStats.categories.health.score}/10, which is excellent and trending upward. You're at 75% completion on your exercise goal. Keep up the momentum!`;
    } else if (message.includes('career') || message.includes('work')) {
      return `Your career score is ${userStats.categories.career.score}/10 and trending upward - that's fantastic progress! Your networking goal is at 40% completion. Would you like some tips on professional networking?`;
    } else if (message.includes('finances') || message.includes('money')) {
      return `I notice your finance score has dipped to ${userStats.categories.finances.score}/10. Your savings goal is at 60% completion. Let's discuss strategies to improve your financial health.`;
    } else if (message.includes('goals') || message.includes('progress')) {
      return `Looking at your goals, you're crushing your reading goal at 90% completion! Your exercise routine is strong at 75%. The areas that could use attention are networking (40%) and savings (60%). Which would you like to focus on?`;
    } else {
      return `Thanks for sharing that! Based on your overall Life Rank score of ${userStats.overallScore}/10, you're doing well. Your strongest areas are health and personal development. Is there a specific area you'd like to improve?`;
    }
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      default: return '➡️';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Overall Score */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
        <h3 className="text-lg font-semibold mb-2">Your Life Rank Score</h3>
        <div className="flex items-center justify-between">
          <div className="text-4xl font-bold">{stats.overallScore}/10</div>
          <div className="text-right">
            <div className="text-sm opacity-80">This Week</div>
            <div className="text-lg">📈 +0.1</div>
          </div>
        </div>
      </div>

      {/* Category Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Object.entries(stats.categories).map(([category, data]) => (
          <div key={category} className="bg-white p-4 rounded-lg shadow border">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold capitalize">{category}</h4>
              <span className="text-lg">{getTrendIcon(data.trend)}</span>
            </div>
            <div className={`text-2xl font-bold ${getScoreColor(data.score)}`}>
              {data.score}/10
            </div>
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(data.score / 10) * 100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Goals Progress */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Current Goals</h3>
        <div className="space-y-4">
          {stats.goals.map(goal => (
            <div key={goal.id} className="border-l-4 border-blue-500 pl-4">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium">{goal.title}</span>
                <span className="text-sm text-gray-600">{goal.progress}%</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${goal.progress}%` }}
                ></div>
              </div>
              <span className="text-xs text-gray-500 capitalize">{goal.category}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Progress Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Weekly Progress</h3>
        <div className="flex items-end space-x-2 h-32">
          {stats.weeklyProgress.map((score, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div 
                className="w-full bg-blue-500 rounded-t transition-all duration-300"
                style={{ height: `${(score / 10) * 100}%` }}
              ></div>
              <span className="text-xs text-gray-600 mt-1">
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][index]}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderChat = () => (
    <div className="bg-white rounded-lg shadow h-full flex flex-col">
      {/* Chat Header */}
      <div className="border-b p-4">
        <h3 className="font-semibold flex items-center">
          🤖 Life Rank AI Coach
          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Online</span>
        </h3>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.map(message => (
          <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
              message.sender === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              <p className="text-sm">{message.message}</p>
              <p className="text-xs opacity-70 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about your stats, goals, or get advice..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button
            onClick={handleSendMessage}
            disabled={!newMessage.trim() || isTyping}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 text-sm"
          >
            Send
          </button>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {['How can I improve my health score?', 'Show me my progress', 'What should I focus on?'].map(suggestion => (
            <button
              key={suggestion}
              onClick={() => setNewMessage(suggestion)}
              className="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded-full text-gray-600"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const sidebarTabs = [
    {
      id: 'overview',
      name: 'Overview',
      icon: '📊',
      component: renderOverview
    },
    {
      id: 'chat',
      name: 'AI Coach',
      icon: '💬',
      component: renderChat
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Life Rank Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt="Profile" className="w-8 h-8 rounded-full" />
                ) : (
                  <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-white text-sm">
                    {user?.full_name?.charAt(0) || user?.email?.charAt(0).toUpperCase()}
                  </div>
                )}
                <span className="text-sm text-gray-700">
                  {user?.full_name || user?.email}
                </span>
              </div>
              <button
                onClick={logout}
                className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Layout with Sidebar */}
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-64 bg-white shadow-lg border-r border-gray-200">
          <div className="p-4">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Dashboard</h2>
            <nav className="space-y-2">
              {sidebarTabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'bg-indigo-100 text-indigo-700 border-l-4 border-indigo-500'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <span className="text-lg mr-3">{tab.icon}</span>
                  <span className="font-medium">{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full p-6">
            <div className="h-full bg-gray-50 rounded-lg overflow-y-auto">
              <div className="p-6">
                {sidebarTabs.find(tab => tab.id === activeTab)?.component()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatsDashboard;