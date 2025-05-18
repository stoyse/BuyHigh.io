import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import BaseLayout from '../../components/Layout/BaseLayout';
import './Home.css';

const funnyTips = [
  "If the chart goes down, just flip your monitor. Problem solved!",
  "Buy high, sell low. That's the BuyHigh.io promise!",
  "Don't let minor things like 'fundamentals' or 'profit warnings' distract you.",
  "Your portfolio is only diversified when half is in the red and the other half is even deeper in the red.",
  "When someone tells you to HODL, they probably mean hold back your tears.",
  "A good trader needs three monitors: one for charts, one for Reddit, and one for job applications.",
  "Our new app feature: The panic button! Automatically sells everything at the day's lowest price."
];

const Home: React.FC = () => {
  const [tip, setTip] = useState("");
  
  useEffect(() => {
    setTip(funnyTips[Math.floor(Math.random() * funnyTips.length)]);
  }, []);

  // Easter egg: Konami code implementation
  useEffect(() => {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;
    
    const checkKonami = (e: KeyboardEvent) => {
      if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
          // Reset for next time
          konamiIndex = 0;
          // Show the easter egg message
          const hint = atob('U0VMTExPVyBpcyB0aGUga2V5IHRvIHJpY2hlcw==');
          alert(`🧙‍♂️ You found a secret! Use '${hint.split(' ')[0]}' for extra credits!`);
        }
      } else {
        konamiIndex = 0;
      }
    };
    
    document.addEventListener('keydown', checkKonami);
    
    return () => {
      document.removeEventListener('keydown', checkKonami);
    };
  }, []);
  
  return (
    <BaseLayout title="BuyHigh.io - Buy High, Sell Low">
      {/* Hero Section */}
      <div className="relative min-h-[70vh] flex flex-col items-center justify-center text-center py-16 overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute inset-0 -z-10">
          {Array.from({ length: 20 }).map((_, i) => {
            const size = Math.random() * 10 + 5;
            return (
              <div 
                key={i}
                className="absolute rounded-full blur-xl opacity-10 animate-float"
                style={{
                  backgroundColor: ['#8b5cf6', '#3b82f6', '#06b6d4', '#ec4899'][Math.floor(Math.random() * 4)],
                  width: `${size}rem`,
                  height: `${size}rem`,
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 5}s`,
                  animationDuration: `${Math.random() * 10 + 10}s`,
                }}
              />
            );
          })}
        </div>
        
        <div className="relative z-10 max-w-4xl mx-auto">
          <div className="mb-6 relative inline-block">
            <div className="relative h-24 w-24 mx-auto rounded-2xl flex items-center justify-center bg-neo-purple/10 backdrop-blur-sm overflow-hidden neon-border">
              <div className="absolute inset-0 bg-gradient-neo opacity-30 animate-gradient"></div>
              <span className="font-pixel text-neo-purple text-3xl relative z-10">B</span>
            </div>
          </div>
          
          <h1 className="text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-neo-purple via-neo-blue to-neo-cyan leading-tight">
            BuyHigh.io
          </h1>
          <p className="text-2xl font-light mb-10 text-gray-700 dark:text-gray-300">
            The art of buying at the worst possible time
          </p>
          
          <div className="flex flex-wrap justify-center gap-5 mb-16">
            <Link to="/trade" className="neo-button rounded-lg px-8 py-4 text-white bg-neo-purple hover:bg-purple-600 transition-all duration-300 text-lg font-medium shadow-lg hover:shadow-neo-purple/30">
              Start Trading
            </Link>
            <Link to="/dashboard" className="neo-button rounded-lg px-8 py-4 text-neo-blue bg-neo-blue/10 border border-neo-blue/30 hover:bg-neo-blue hover:text-white transition-all duration-300 text-lg font-medium">
              Dashboard
            </Link>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="glass-card p-6 rounded-xl hover:shadow-neo-lg transition-all duration-300 hover:scale-105 text-left">
              <div className="w-12 h-12 rounded-lg bg-pink-500/20 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z"></path>
                </svg>
              </div>
              <h2 className="text-xl font-bold mb-2">Buy High</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Our state-of-the-art algorithm helps you buy stocks exactly when they're at their most expensive.
              </p>
            </div>
            
            <div className="glass-card p-6 rounded-xl hover:shadow-neo-lg transition-all duration-300 hover:scale-105 text-left">
              <div className="w-12 h-12 rounded-lg bg-neo-blue/20 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-neo-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
                </svg>
              </div>
              <h2 className="text-xl font-bold mb-2">Sell Low</h2>
              <p className="text-gray-600 dark:text-gray-400">
                Panic selling made easy. We'll help you exit at the absolute bottom.
              </p>
            </div>
            
            <div className="glass-card p-6 rounded-xl hover:shadow-neo-lg transition-all duration-300 hover:scale-105 text-left">
              <div className="w-12 h-12 rounded-lg bg-neo-emerald/20 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-neo-emerald" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
              </div>
              <h2 className="text-xl font-bold mb-2">Lose Money</h2>
              <p className="text-gray-600 dark:text-gray-400">
                The only trading service that proudly advertises its negative returns!
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Daily Tip */}
      <div className="mt-12 p-6 glass-card max-w-lg mx-auto rounded-xl bg-gray-900/10 dark:bg-gray-800/20 text-center">
        <h2 className="text-xl font-bold mb-4 text-neo-blue">Daily Investment Tip:</h2>
        <p className="text-gray-700 dark:text-gray-300 italic text-lg">
          "{tip}"
        </p>
      </div>

      {/* Casino Ad Section */}
      <div className="mt-20 relative overflow-hidden rounded-xl p-8 bg-gradient-to-br from-pink-500/20 to-purple-500/20 border border-pink-500/20">
        <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-pink-500 opacity-20 blur-[60px]"></div>
        <div className="flex flex-col md:flex-row items-center justify-between relative z-10">
          <div className="md:w-2/3 mb-8 md:mb-0 md:pr-8">
            <h2 className="text-3xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-purple-500">
              Try Our Casino!
            </h2>
            <p className="text-gray-700 dark:text-gray-300 mb-6">
              Why lose money slowly with stocks when you can do it quickly at our casino? Our casino offers the same thrills as the stock market, but with brighter colors!
            </p>
            <Link 
              to="/casino" 
              className="neo-button rounded-lg px-8 py-3 text-white bg-pink-500 hover:bg-pink-600 transition-all duration-300 shadow-lg hover:shadow-pink-500/30 font-medium inline-flex items-center"
            >
              <span className="mr-2">Play Now</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
          <div className="md:w-1/3 flex justify-center">
            <div className="relative animate-spin-slow">
              <span className="text-8xl">🎰</span>
            </div>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default Home;
