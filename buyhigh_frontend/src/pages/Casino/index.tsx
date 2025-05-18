import React from 'react';
import './Casino.css';
import BaseLayout from '../../components/Layout/BaseLayout';

const Casino = () => {
  // Generiere zufällige animierte Elemente
  const generateRandomElements = () => {
    const elements = [];
    for (let i = 0; i < 20; i++) {
      const emojis = ['💰', '🎲', '🎰', '💎', '🃏', '🎯', '🍀', '💸'];
      const colors = ['pink', 'purple', 'yellow', 'green', 'blue', 'red'];
      const left = Math.random() * 100;
      const top = Math.random() * 100;
      const delay = Math.random();
      const duration = Math.random() * 5 + 3;
      
      elements.push(
        <div 
          key={i}
          className="absolute animate-float" 
          style={{
            left: `${left}%`,
            top: `${top}%`,
            animationDelay: `${delay}s`,
            animationDuration: `${duration}s`
          }}
        >
          <span className={`text-${colors[Math.floor(Math.random() * colors.length)]}-500 text-opacity-30 text-6xl`}>
            {emojis[Math.floor(Math.random() * emojis.length)]}
          </span>
        </div>
      );
    }
    return elements;
  };

  return (
    <BaseLayout title="BuyHigh Casino - Lose Money Faster!">
      {/* Hero Section with Animated Elements */}
      <div className="relative overflow-hidden py-8 mb-8 text-center">
        {/* Animated background elements */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          {generateRandomElements()}
        </div>
        
        <h1 className="text-5xl font-bold mb-2 animate-pulse bg-clip-text text-transparent bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500">
          BUY HIGH CASINO
        </h1>
        <p className="text-2xl italic mb-4 animate-bounce text-pink-500 dark:text-pink-400">
          Where financial degenerates come to play!
        </p>
        <div className="animate-spin-slow inline-block mb-4">
          <span className="text-6xl">🎰</span>
        </div>
        <p className="max-w-md mx-auto text-yellow-500 dark:text-yellow-400 bg-purple-900/30 p-3 rounded-lg glass-card animate-pulse border-2 border-yellow-500 dark:border-yellow-600">
          Warning: These games are designed to separate you from your virtual money even faster than your terrible investment strategies!
        </p>
      </div>

      {/* Games Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <GameCard 
          title="COIN FLIP"
          description="Heads you lose, tails we win! 50% chance of doubling your money!"
          buttonText="FLIP TO WIN"
          buttonColor="yellow"
          borderColor="yellow-500"
          gradientFrom="yellow-500/20"
          gradientTo="orange-500/20"
          darkGradientFrom="yellow-600/30"
          darkGradientTo="orange-600/30"
        >
          <div className="absolute inset-0 coin-flip-animation">
            <div className="absolute inset-0 bg-yellow-500 rounded-full m-12 border-8 border-yellow-600 flex items-center justify-center text-4xl">
              <span className="front">🪙</span>
              <span className="back">💰</span>
            </div>
          </div>
        </GameCard>
        
        <GameCard 
          title="ROULETTE"
          description="Red, black, or green? Math says you'll lose eventually!"
          buttonText="SPIN THE WHEEL"
          buttonColor="red"
          borderColor="red-500"
          gradientFrom="red-500/20"
          gradientTo="pink-500/20"
          darkGradientFrom="red-600/30"
          darkGradientTo="pink-600/30"
          animationDelay="0.1s"
          hoverRotate="-rotate-1"
        >
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full border-4 border-red-500 animate-spin-slow relative">
              <div className="absolute inset-0 rounded-full flex items-center justify-center">
                <span className="text-5xl">🎯</span>
              </div>
            </div>
          </div>
        </GameCard>
        
        <GameCard 
          title="SLOTS"
          description="Pull the lever! The house edge is only... a lot!"
          buttonText="SPIN TO WIN"
          buttonColor="purple"
          borderColor="purple-500"
          gradientFrom="purple-500/20"
          gradientTo="blue-500/20"
          darkGradientFrom="purple-600/30"
          darkGradientTo="blue-600/30"
          animationDelay="0.2s"
        >
          <div className="flex space-x-2 transform scale-90">
            <div className="w-16 h-24 bg-gray-800 border-2 border-purple-500 rounded-lg flex items-center justify-center overflow-hidden">
              <div className="animate-slot text-4xl">🍒</div>
            </div>
            <div className="w-16 h-24 bg-gray-800 border-2 border-purple-500 rounded-lg flex items-center justify-center overflow-hidden">
              <div className="animate-slot-2 text-4xl">💎</div>
            </div>
            <div className="w-16 h-24 bg-gray-800 border-2 border-purple-500 rounded-lg flex items-center justify-center overflow-hidden">
              <div className="animate-slot-3 text-4xl">7️⃣</div>
            </div>
          </div>
        </GameCard>
        
        <GameCard 
          title="DICE ROLL"
          description="Roll the dice and pray! Set your own odds!"
          buttonText="ROLL THE DICE"
          buttonColor="green"
          borderColor="green-500"
          gradientFrom="green-500/20"
          gradientTo="teal-500/20"
          darkGradientFrom="green-600/30"
          darkGradientTo="teal-600/30"
          animationDelay="0.3s"
          hoverRotate="-rotate-1"
        >
          <div className="animate-bounce-slow transform rotate-12">
            <span className="text-7xl">🎲</span>
          </div>
          <div className="animate-bounce-slow-delay transform -rotate-12 absolute top-16 left-24">
            <span className="text-5xl">🎲</span>
          </div>
        </GameCard>
        
        <GameCard 
          title="CRASH"
          description="Cash out before it crashes! Greed is your enemy!"
          buttonText="TO THE MOON"
          buttonColor="blue"
          borderColor="blue-500"
          gradientFrom="blue-500/20"
          gradientTo="indigo-500/20"
          darkGradientFrom="blue-600/30"
          darkGradientTo="indigo-600/30"
          animationDelay="0.4s"
        >
          <div className="crash-animation">
            <div className="text-6xl">🚀</div>
            <div className="absolute text-7xl opacity-0 boom">💥</div>
          </div>
        </GameCard>
        
        <GameCard 
          title="BLACKJACK"
          description="Hit me! The classics never get old!"
          buttonText="DEAL ME IN"
          buttonColor="pink"
          borderColor="pink-500"
          gradientFrom="pink-500/20"
          gradientTo="rose-500/20"
          darkGradientFrom="pink-600/30"
          darkGradientTo="rose-600/30"
          animationDelay="0.5s"
          hoverRotate="-rotate-1"
        >
          <div className="flex transform rotate-12 blackjack-animation">
            <div className="w-16 h-20 bg-white rounded-lg shadow-lg ml-4 -mr-8 flex items-center justify-center text-4xl">
              🂮
            </div>
            <div className="w-16 h-20 bg-white rounded-lg shadow-lg flex items-center justify-center text-4xl">
              🂡
            </div>
          </div>
        </GameCard>
      </div>
      
      {/* Funny Disclaimer */}
      <div className="max-w-2xl mx-auto p-6 glass-card rounded-xl bg-gray-900/50 dark:bg-black/50 text-center mb-10">
        <h3 className="text-2xl font-bold mb-2 text-red-400 dark:text-red-500">DISCLAIMER</h3>
        <p className="text-gray-300 dark:text-gray-400">
          These games are rigged just like real markets! At least here we're honest about it!
        </p>
        <p className="mt-3 text-xs text-gray-500 dark:text-gray-600">
          Not responsible for addictive behavior, tears, broken keyboards, or empty virtual wallets. Play responsibly or don't - we still win! 😈
        </p>
      </div>
    </BaseLayout>
  );
};

interface GameCardProps {
  title: string;
  description: string;
  buttonText: string;
  buttonColor: string;
  borderColor: string;
  gradientFrom: string;
  gradientTo: string;
  darkGradientFrom: string;
  darkGradientTo: string;
  animationDelay?: string;
  hoverRotate?: string;
  children: React.ReactNode;
}

const GameCard: React.FC<GameCardProps> = ({ 
  title, 
  description, 
  buttonText, 
  buttonColor, 
  borderColor,
  gradientFrom,
  gradientTo,
  darkGradientFrom,
  darkGradientTo,
  animationDelay,
  hoverRotate = "rotate-1",
  children 
}) => {
  return (
    <div 
      className={`game-card glass-card rounded-xl overflow-hidden border-2 border-${borderColor} hover:border-pink-500 transition-all duration-300 hover:scale-105 hover:${hoverRotate} hover:shadow-[0_0_30px_rgba(236,72,153,0.5)] animate-blur-in bg-gradient-to-br from-${gradientFrom} to-${gradientTo} dark:from-${darkGradientFrom} dark:to-${darkGradientTo}`}
      style={{ animationDelay }}
    >
      <a href="#" className="block h-full">
        <div className="relative h-48 overflow-hidden flex justify-center items-center bg-black/20">
          {children}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
            <h3 className="text-3xl font-extrabold text-white text-center">{title}</h3>
          </div>
        </div>
        <div className="p-5 text-center">
          <p className="mb-4 text-gray-700 dark:text-gray-300">{description}</p>
          <div className={`neo-button text-${buttonColor}-400 bg-${buttonColor}-900/30 hover:bg-${buttonColor}-400 hover:text-black border border-${buttonColor}-400/50 p-2 rounded-lg font-bold`}>
            {buttonText}
          </div>
        </div>
      </a>
    </div>
  );
};

export default Casino;
