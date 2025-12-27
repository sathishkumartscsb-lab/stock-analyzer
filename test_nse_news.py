from src.fetchers.news import NewsFetcher

nf = NewsFetcher()
news = nf.fetch_latest_news('RELIANCE')

print(f'Total news items: {len(news)}')
print('\nNews sources:')
for item in news[:5]:
    print(f'- {item["source"]}: {item["title"][:80]}')
