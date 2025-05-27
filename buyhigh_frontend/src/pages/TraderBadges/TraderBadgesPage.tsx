import React from 'react';
import BaseLayout from '../../components/Layout/BaseLayout';

interface BadgeItemProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  badgeText: string;
  badgeColor: string;
  iconBgColor: string;
}

const BadgeItem: React.FC<BadgeItemProps> = ({ 
  icon, 
  title, 
  description, 
  badgeText, 
  badgeColor, 
  iconBgColor 
}) => (
  <div className="badge-item glass-card hover:bg-gray-100/10 dark:hover:bg-gray-700/20 rounded-xl shadow-sm hover:shadow-neo border border-gray-200/20 dark:border-gray-700/20 p-4 text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
    <div className="flex flex-col items-center">
      <div className={`badge-icon w-12 h-12 p-2 rounded-full mb-2 flex items-center justify-center transition-transform duration-300 hover:scale-110 ${iconBgColor}`}>
        {icon}
      </div>
      <span className={`badge text-xs px-3 py-1 rounded-full font-medium ${badgeColor}`}>
        {badgeText}
      </span>
      <div className="badge-title font-semibold text-center text-sm mt-2">{title}</div>
      <div className="badge-description text-xs text-gray-600 dark:text-gray-400 text-center mt-1">
        {description}
      </div>
    </div>
  </div>
);

interface BadgeSectionProps {
  title: string;
  categoryBadge: {
    text: string;
    icon: React.ReactNode;
    bgColor: string;
  };
  sectionIcon: React.ReactNode;
  children: React.ReactNode;
  decorativeColor: string;
  animationDelay: string;
}

const BadgeSection: React.FC<BadgeSectionProps> = ({ 
  title, 
  categoryBadge, 
  sectionIcon, 
  children, 
  decorativeColor,
  animationDelay 
}) => (
  <div 
    className="badge-section glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 mb-8 relative overflow-hidden animate-float transition-all duration-500 hover:-translate-y-1" 
    style={{ animationDelay }}
  >
    {/* Decorative elements */}
    <div className={`absolute -top-16 -right-16 w-32 h-32 ${decorativeColor} rounded-full opacity-20 blur-3xl`}></div>
    
    <div className="flex justify-between items-center mb-6">
      <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 flex items-center">
        {sectionIcon}
        {title}
      </h2>
      <div className={`category-badge px-3 py-2 rounded-lg text-xs font-medium flex items-center ${categoryBadge.bgColor}`}>
        {categoryBadge.icon}
        {categoryBadge.text}
      </div>
    </div>
    
    <div className="badge-container grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 mb-6">
      {children}
    </div>
  </div>
);

const TraderBadgesPage: React.FC = () => {
  return (
    <BaseLayout title="Trader Badges - BuyHigh.io">
      <div className="container mx-auto max-w-7xl px-4">
        {/* Badge Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold gradient-text mb-2 flex justify-center items-center">
            <svg className="w-8 h-8 mr-2 animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path>
            </svg>
            Trader Badges
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm max-w-2xl mx-auto">
            Alle verfügbaren Trader-Badges auf BuyHigh.io – sammle sie durch aktiven Handel und Community-Engagement
          </p>
        </header>

        {/* Experience Level Badges */}
        <BadgeSection
          title="Experience Levels"
          categoryBadge={{
            text: "Trading Experience",
            icon: <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>,
            bgColor: "bg-blue-500/10 text-blue-500"
          }}
          sectionIcon={<svg className="w-6 h-6 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>}
          decorativeColor="bg-green-500"
          animationDelay="0.1s"
        >
          <BadgeItem
            icon={<svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>}
            title="Beginner"
            description="Weniger als 6 Monate Trading-Erfahrung"
            badgeText="Beginner"
            badgeColor="bg-green-500 text-white"
            iconBgColor="bg-green-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>}
            title="Advanced"
            description="6-24 Monate Trading-Erfahrung"
            badgeText="Advanced"
            badgeColor="bg-blue-500 text-white"
            iconBgColor="bg-blue-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>}
            title="Experienced"
            description="2-5 Jahre Trading-Erfahrung"
            badgeText="Experienced"
            badgeColor="bg-purple-500 text-white"
            iconBgColor="bg-purple-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"></path></svg>}
            title="Expert"
            description="Mehr als 5 Jahre Trading-Erfahrung"
            badgeText="Expert"
            badgeColor="bg-yellow-500 text-black"
            iconBgColor="bg-yellow-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>}
            title="Veteran"
            description="Über 10 Jahre Trading-Erfahrung"
            badgeText="Veteran"
            badgeColor="bg-red-500 text-white"
            iconBgColor="bg-red-500/10"
          />
        </BadgeSection>

        {/* Performance Badges */}
        <BadgeSection
          title="Performance Badges"
          categoryBadge={{
            text: "Performance",
            icon: <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>,
            bgColor: "bg-emerald-500/10 text-emerald-500"
          }}
          sectionIcon={<svg className="w-6 h-6 mr-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>}
          decorativeColor="bg-emerald-500"
          animationDelay="0.2s"
        >
          <BadgeItem
            icon={<svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>}
            title="Top Performer"
            description="Top 5% Rendite im letzten Monat"
            badgeText="Top Performer"
            badgeColor="bg-green-500 text-white"
            iconBgColor="bg-green-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>}
            title="Risk Trader"
            description="Trading mit hoher Volatilität"
            badgeText="Risk Trader"
            badgeColor="bg-red-500 text-white"
            iconBgColor="bg-red-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>}
            title="Consistent Return"
            description="Positive Rendite über 3+ Monate"
            badgeText="Consistent Return"
            badgeColor="bg-yellow-500 text-black"
            iconBgColor="bg-yellow-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>}
            title="Diversifier"
            description="Portfolio über mehrere Anlageklassen"
            badgeText="Diversifier"
            badgeColor="bg-blue-500 text-white"
            iconBgColor="bg-blue-500/10"
          />
        </BadgeSection>

        {/* Specialization Badges */}
        <BadgeSection
          title="Specializations"
          categoryBadge={{
            text: "Focus",
            icon: <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>,
            bgColor: "bg-purple-500/10 text-purple-500"
          }}
          sectionIcon={<svg className="w-6 h-6 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>}
          decorativeColor="bg-purple-500"
          animationDelay="0.3s"
        >
          <BadgeItem
            icon={<svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>}
            title="Crypto Trader"
            description="Spezialisiert auf Kryptowährungen"
            badgeText="Crypto Trader"
            badgeColor="bg-orange-500 text-white"
            iconBgColor="bg-orange-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>}
            title="Stock Pro"
            description="Fokus auf Aktienmärkte"
            badgeText="Stock Pro"
            badgeColor="bg-green-500 text-white"
            iconBgColor="bg-green-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path></svg>}
            title="ETF Strategist"
            description="ETF-basierte Anlagestrategien"
            badgeText="ETF Strategist"
            badgeColor="bg-yellow-500 text-black"
            iconBgColor="bg-yellow-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"></path></svg>}
            title="Forex Trader"
            description="Devisenmarkt-Spezialist"
            badgeText="Forex Trader"
            badgeColor="bg-blue-500 text-white"
            iconBgColor="bg-blue-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>}
            title="Commodity Investor"
            description="Fokus auf Rohstoffmärkte"
            badgeText="Commodity Investor"
            badgeColor="bg-gray-600 text-white"
            iconBgColor="bg-gray-600/10"
          />
        </BadgeSection>

        {/* Status Badges */}
        <BadgeSection
          title="Account Status"
          categoryBadge={{
            text: "Membership",
            icon: <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>,
            bgColor: "bg-pink-500/10 text-pink-500"
          }}
          sectionIcon={<svg className="w-6 h-6 mr-2 text-pink-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>}
          decorativeColor="bg-pink-500"
          animationDelay="0.4s"
        >
          <BadgeItem
            icon={<svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>}
            title="Verified"
            description="Vollständig verifiziertes Konto"
            badgeText="Verified"
            badgeColor="bg-green-500 text-white"
            iconBgColor="bg-green-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7"></path></svg>}
            title="Premium"
            description="Premium-Mitglied"
            badgeText="Premium"
            badgeColor="bg-yellow-500 text-black"
            iconBgColor="bg-yellow-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"></path></svg>}
            title="VIP"
            description="VIP-Kontoinhaber"
            badgeText="VIP"
            badgeColor="bg-red-500 text-white"
            iconBgColor="bg-red-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-gray-800 dark:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z"></path></svg>}
            title="Founding Member"
            description="Von Anfang an bei BuyHigh.io"
            badgeText="Founding Member"
            badgeColor="bg-gray-800 text-white dark:bg-gray-200 dark:text-gray-800"
            iconBgColor="bg-gray-800/10 dark:bg-gray-200/10"
          />
        </BadgeSection>

        {/* Community Badges */}
        <BadgeSection
          title="Community Contributions"
          categoryBadge={{
            text: "Engagement",
            icon: <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>,
            bgColor: "bg-cyan-500/10 text-cyan-500"
          }}
          sectionIcon={<svg className="w-6 h-6 mr-2 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>}
          decorativeColor="bg-cyan-500"
          animationDelay="0.5s"
        >
          <BadgeItem
            icon={<svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path></svg>}
            title="Mentor"
            description="Hilft aktiv neuen Tradern"
            badgeText="Mentor"
            badgeColor="bg-blue-500 text-white"
            iconBgColor="bg-blue-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>}
            title="Strategy Author"
            description="Teilt wertvolle Trading-Strategien"
            badgeText="Strategy Author"
            badgeColor="bg-purple-500 text-white"
            iconBgColor="bg-purple-500/10"
          />
          <BadgeItem
            icon={<svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>}
            title="Analyst"
            description="Erstellt hochwertige Analysen"
            badgeText="Analyst"
            badgeColor="bg-green-500 text-white"
            iconBgColor="bg-green-500/10"
          />
        </BadgeSection>

        {/* Earn Badges CTA */}
        <div className="glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 text-center animate-float" style={{ animationDelay: '0.6s' }}>
          <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">Sammle deine eigenen Badges!</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-lg mx-auto">
            Beginne mit dem Trading, tritt der Community bei und verdiene Badges, die deinen Fortschritt und deine Expertise zeigen.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <button 
              onClick={() => window.location.href = '/trade'}
              className="neo-button px-5 py-2 bg-blue-500/10 text-blue-500 border border-blue-500/20 hover:bg-blue-500 hover:text-white rounded-lg text-sm font-medium transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              Zum Trading
            </button>
            <button 
              onClick={() => window.location.href = '/social'}
              className="neo-button px-5 py-2 bg-pink-500/10 text-pink-500 border border-pink-500/20 hover:bg-pink-500 hover:text-white rounded-lg text-sm font-medium transition-all flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              Community
            </button>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default TraderBadgesPage;
