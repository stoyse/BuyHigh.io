import React, { useState, useRef, useEffect } from 'react';
import BaseLayout from '../../components/Layout/BaseLayout';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
}

const ChatbotPage: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: "Hello! I'm your BuyHigh.io trading assistant. I can help you with market analysis, trading strategies, and answer questions about our platform. How can I assist you today?",
            sender: 'bot',
            timestamp: new Date()
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const simulateBotResponse = (userMessage: string): string => {
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('price') || lowerMessage.includes('stock')) {
            return "I can help you with stock prices! However, I don't have real-time data access right now. For live prices, please check our Trade page or use our market dashboard.";
        }
        
        if (lowerMessage.includes('buy') || lowerMessage.includes('sell')) {
            return "Remember our motto: Buy High, Sell Low! 😄 But seriously, I recommend doing thorough research before making any trades. Check out our News section for market insights.";
        }
        
        if (lowerMessage.includes('casino') || lowerMessage.includes('gamble')) {
            return "Our Casino section offers some fun trading games! Remember to only risk what you can afford to lose. It's all about entertainment and learning.";
        }
        
        if (lowerMessage.includes('help') || lowerMessage.includes('support')) {
            return "I'm here to help! You can ask me about trading strategies, platform features, or general market questions. What specific topic interests you?";
        }
        
        if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
            return "Hello there! Great to see you on BuyHigh.io. What trading adventure can I help you with today?";
        }
        
        return "That's an interesting question! While I'm still learning, I'd recommend checking our News section for the latest market insights or visiting our Social page to discuss with other traders.";
    };

    const handleSendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            text: inputMessage,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsTyping(true);

        // Simulate API delay
        setTimeout(() => {
            const botResponse: Message = {
                id: (Date.now() + 1).toString(),
                text: simulateBotResponse(inputMessage),
                sender: 'bot',
                timestamp: new Date()
            };
            
            setMessages(prev => [...prev, botResponse]);
            setIsTyping(false);
        }, 1000 + Math.random() * 2000);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <BaseLayout title="AI Trading Assistant">
            <div className="h-[calc(100vh-200px)] flex flex-col">
                {/* Chat Header */}
                <div className="flex items-center space-x-3 p-4 border-b border-gray-200/20 dark:border-gray-700/30">
                    <div className="relative">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-neo-purple to-neo-blue flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white dark:border-gray-800"></div>
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-800 dark:text-gray-200">BuyHigh.io Assistant</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Online • Ready to help</p>
                    </div>
                </div>

                {/* Messages Container */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`flex space-x-2 max-w-xs lg:max-w-md ${message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                                {/* Avatar */}
                                <div className="flex-shrink-0">
                                    {message.sender === 'bot' ? (
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neo-purple to-neo-blue flex items-center justify-center">
                                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neo-cyan to-neo-blue flex items-center justify-center">
                                            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                            </svg>
                                        </div>
                                    )}
                                </div>

                                {/* Message Bubble */}
                                <div className={`rounded-2xl px-4 py-2 ${
                                    message.sender === 'user'
                                        ? 'bg-neo-blue text-white'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                                }`}>
                                    <p className="text-sm">{message.text}</p>
                                    <p className={`text-xs mt-1 ${
                                        message.sender === 'user' 
                                            ? 'text-blue-100' 
                                            : 'text-gray-500 dark:text-gray-400'
                                    }`}>
                                        {formatTime(message.timestamp)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Typing Indicator */}
                    {isTyping && (
                        <div className="flex justify-start">
                            <div className="flex space-x-2 max-w-xs lg:max-w-md">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-neo-purple to-neo-blue flex items-center justify-center">
                                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-2">
                                    <div className="flex space-x-1">
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="border-t border-gray-200/20 dark:border-gray-700/30 p-4">
                    <div className="flex space-x-4">
                        <div className="flex-1 relative">
                            <input
                                ref={inputRef}
                                type="text"
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="Ask me about trading, market analysis, or platform features..."
                                className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-neo-purple focus:border-transparent text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400"
                                disabled={isTyping}
                            />
                        </div>
                        <button
                            onClick={handleSendMessage}
                            disabled={!inputMessage.trim() || isTyping}
                            className="px-6 py-3 bg-neo-purple text-white rounded-xl hover:bg-neo-purple/80 focus:outline-none focus:ring-2 focus:ring-neo-purple focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                    
                    {/* Quick Actions */}
                    <div className="flex flex-wrap gap-2 mt-3">
                        <button
                            onClick={() => setInputMessage("What's the current market trend?")}
                            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                            Market Trends
                        </button>
                        <button
                            onClick={() => setInputMessage("How do I start trading?")}
                            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                            Trading Guide
                        </button>
                        <button
                            onClick={() => setInputMessage("Tell me about risk management")}
                            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                            Risk Management
                        </button>
                        <button
                            onClick={() => setInputMessage("What features does BuyHigh.io offer?")}
                            className="px-3 py-1 text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                            Platform Features
                        </button>
                    </div>
                </div>
            </div>
        </BaseLayout>
    );
};

export default ChatbotPage;