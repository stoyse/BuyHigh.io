import React, { useState, useEffect, useMemo } from 'react';
import NewsCard, { NewsCardProps } from './NewsCard';
import { getNews } from '../../apiService';
import './News.css';
import BaseLayout from '../../components/Layout/BaseLayout';

// Dieses Interface spiegelt die Struktur wider, die von der /news/ API (via getNews) erwartet wird
interface ApiNewsAsset {
  id: number | string;
  symbol: string;      // Wird als Quelle verwendet
  name: string;        // Wird als Überschrift verwendet
  asset_type: string;  // Wird als Kategorie verwendet
  default_price?: number | null; // Dieses Feld kommt von der API, wird aber nicht direkt in NewsCard verwendet
  url?: string;        // URL des Artikels
}

// NewsItem erbt von NewsCardProps (definiert in NewsCard.tsx),
// die die für die NewsCard-Komponente benötigten Felder definieren.
// NewsCardProps ist in NewsCard.tsx definiert und wird hier implizit durch NewsItem genutzt.
interface NewsItem extends NewsCardProps {}

const NewsPage: React.FC = () => {
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [filteredNews, setFilteredNews] = useState<NewsItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [visibleCount, setVisibleCount] = useState<number>(10); // Anzahl initial sichtbarer Nachrichten
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNewsData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // getNews gibt jetzt direkt ApiNewsAsset[] oder [] zurück
        const assets: ApiNewsAsset[] = await getNews();

        if (Array.isArray(assets)) {
          const transformedNews: NewsItem[] = assets.map((asset: ApiNewsAsset, index: number) => ({
            id: asset.id,
            headline: asset.name,
            category: asset.asset_type.toLowerCase(),
            source: asset.symbol,
            animationDelay: `${index * 0.1}s`,
            articleUrl: asset.url, // articleUrl aus den API-Daten übernehmen
            // imageUrl, summary, dateTime sind optionale Props in NewsCardProps
            // und werden von dieser API nicht direkt geliefert. NewsCard.tsx behandelt das.
          }));
          setAllNews(transformedNews);
        } else {
          // Dieser Fall sollte gemäß der aktuellen Implementierung von getNews nicht eintreten.
          console.error('Unerwartetes Datenformat von getNews erhalten:', assets);
          throw new Error('News data is not in expected array format.');
        }
      } catch (err) {
        console.error("Error fetching news in NewsPage:", err);
        setError(err instanceof Error ? err.message : 'Failed to fetch news.');
        setAllNews([]); // Stelle sicher, dass allNews im Fehlerfall ein leeres Array ist
      } finally {
        setIsLoading(false);
      }
    };

    fetchNewsData();
  }, []);

  useEffect(() => {
    let newsToFilter = allNews;

    if (activeCategory !== 'all') {
      newsToFilter = newsToFilter.filter(item => item.category === activeCategory);
    }

    if (searchTerm) {
      newsToFilter = newsToFilter.filter(item =>
        item.headline.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.source && item.source.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    setFilteredNews(newsToFilter);
    setVisibleCount(10); 
  }, [allNews, activeCategory, searchTerm]);

  const handleCategoryFilter = (category: string) => {
    setActiveCategory(category);
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const loadMoreNews = () => {
    setVisibleCount(prevCount => prevCount + 10);
  };

  const categories = useMemo(() => {
    const uniqueCategories = new Set(allNews.map(item => item.category));
    return ['all', ...Array.from(uniqueCategories)];
  }, [allNews]);

  const newsToShow = filteredNews.slice(0, visibleCount);

  if (isLoading) {
    return (
      <BaseLayout title="Loading News - BuyHigh.io">
        <div className="container mx-auto flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-neo-amber border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading market news...</p>
          </div>
        </div>
      </BaseLayout>
    );
  }

  if (error) {
    return (
      <BaseLayout title="News Error - BuyHigh.io">
        <div className="container mx-auto flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-red-500">{error}</p>
            <button 
              className="mt-4 px-4 py-2 bg-neo-amber text-white rounded-lg hover:bg-neo-amber-dark transition-colors"
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </BaseLayout>
    );
  }

  return (
    <BaseLayout title="Market News - BuyHigh.io">
      <div className="container mx-auto">
        {/* News Header */}
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-pixel gradient-text mb-2">Market News</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm max-w-2xl mx-auto">
            Stay informed with the latest market updates, company announcements, and economic insights.
          </p>
        </header>

        {/* Filter Section */}
        <div className="mb-6 glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-5 relative overflow-hidden glow-effect">
          <div className="absolute -top-16 -right-16 w-32 h-32 bg-neo-amber rounded-full opacity-20 blur-3xl"></div>
          <div className="flex flex-col md:flex-row flex-wrap justify-between items-center relative z-10 gap-4">
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <button
                  key={category}
                  onClick={() => handleCategoryFilter(category)}
                  className={`category-filter text-sm px-3 py-1.5 rounded-lg border transition-colors duration-300
                    ${activeCategory === category
                      ? 'bg-neo-amber text-white border-neo-amber ring-2 ring-neo-amber ring-opacity-30'
                      : 'glass-card border-gray-300 dark:border-gray-600 hover:bg-neo-amber/80 hover:text-white hover:border-neo-amber'
                    }`}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </button>
              ))}
            </div>
            <div className="w-full md:w-auto">
              <input
                type="search"
                id="news-search"
                placeholder="Search news..."
                value={searchTerm}
                onChange={handleSearchChange}
                className="w-full md:w-64 px-4 py-2 rounded-lg bg-white/10 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-600 focus:ring-2 focus:ring-neo-amber focus:border-neo-amber outline-none placeholder-gray-500 dark:placeholder-gray-400 text-sm"
              />
            </div>
          </div>
        </div>

        {/* News Grid */}
        {!isLoading && !error && newsToShow.length === 0 && (
          <div className="glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-6 text-center">
            <div className="flex flex-col items-center justify-center py-8">
              <svg className="w-16 h-16 text-gray-400 dark:text-gray-500 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              <p className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">No News Found</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Try adjusting your filters or search term.</p>
            </div>
          </div>
        )}

        {!isLoading && !error && newsToShow.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {newsToShow.map(item => (
              <NewsCard key={item.id} {...item} />
            ))}
          </div>
        )}

        {/* Load More Button */}
        {!isLoading && filteredNews.length > visibleCount && (
          <div className="text-center mt-8">
            <button
              id="load-more"
              onClick={loadMoreNews}
              className="neo-button px-6 py-3 bg-neo-amber/10 text-neo-amber border border-neo-amber/20 hover:bg-neo-amber hover:text-white rounded-lg text-sm font-medium transition-all flex items-center mx-auto"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 13l-7 7-7-7m14-8l-7 7-7-7"></path>
              </svg>
              Load More News
            </button>
          </div>
        )}
      </div>
    </BaseLayout>
  );
};

export default NewsPage;
