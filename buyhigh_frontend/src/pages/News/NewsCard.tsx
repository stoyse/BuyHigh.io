import React from 'react';

export interface NewsCardProps { // Exportiere das Interface
  id: number | string;
  headline: string;
  category: string;
  source?: string;
  imageUrl?: string; // Wird von der aktuellen API nicht bereitgestellt
  summary?: string; // Wird von der aktuellen API nicht bereitgestellt
  articleUrl?: string; // Wird von der aktuellen API nicht bereitgestellt
  dateTime?: string; // Wird von der aktuellen API nicht bereitgestellt
  animationDelay?: string;
}

const NewsCard: React.FC<NewsCardProps> = ({
  headline,
  category,
  source,
  imageUrl,
  summary,
  articleUrl,
  dateTime,
  animationDelay,
}) => {
  const placeholderImage = "/images/news_placeholder.png"; // Pfad zum Placeholder-Bild anpassen

  const content = (
    <>
      <div className="news-image-container rounded-t-2xl bg-gray-200 dark:bg-gray-700">
        <img
          src={imageUrl || placeholderImage}
          alt={headline}
          className="news-image w-full h-48 object-cover"
          onError={(e) => (e.currentTarget.src = placeholderImage)}
        />
      </div>
      <div className="p-5">
        <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white group-hover:text-neo-amber transition-colors">
          {headline}
        </h3>
        {summary && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 leading-relaxed">
            {summary.substring(0, 120)}{summary.length > 120 ? '...' : ''}
          </p>
        )}
        {!summary && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 italic">
            Zusammenfassung nicht verfügbar.
          </p>
        )}
        <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
          <span>{source || 'Unbekannte Quelle'}</span>
          <span>{dateTime || ''}</span>
        </div>
      </div>
    </>
  );

  return (
    <div
      className="news-item glass-card shadow-neo border border-gray-200/10 dark:border-gray-700/20 rounded-2xl overflow-hidden transition-all hover:shadow-neo-lg hover:scale-[1.01] animate-float group"
      data-category={category.toLowerCase()}
      style={{ animationDelay }}
    >
      {articleUrl ? (
        <a href={articleUrl} target="_blank" rel="noopener noreferrer" className="block">
          {content}
        </a>
      ) : (
        <div className="block cursor-default">{content}</div>
      )}
    </div>
  );
};

export default NewsCard;
