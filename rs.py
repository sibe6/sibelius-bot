import feedparser

happening_url = 'https://www.peto-media.fi/tiedotteet/rss.xml'
yle_major_headlines_url = 'https://feeds.yle.fi/uutiset/v1/majorHeadlines/YLE_UUTISET.rss'
yle_kainuu_headlines_url = 'https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET&concepts=18-141399'
yle_latest_news_url = 'https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET'

async def get_happening():
    feed = feedparser.parse(happening_url)

    trim_title = lambda title: title.split("/", 1)[0]
    trim_date = lambda summary: summary.split(" ", 2)[0]
    trim_time = lambda summary: summary.split(" ", 2)[1]
    trim_event = lambda summary: summary.split(" ", 3)[3]

    res = '```md\n'

    for entry in feed.entries:
        if(len(res) >= 1850):
            break

        res += (
            f'> {trim_title(entry.title)} '
            f'{trim_date(entry.summary)} '
            f'{trim_time(entry.summary)}\n'
            f'{trim_event(entry.summary)}\n\n'
        )

    res += '```'

    print("Lenght: ", len(res))

    return res

async def get_yle_news(which):
    if (which == 'major'):
        feed = feedparser.parse(yle_major_headlines_url)
    elif (which == 'kainuu'):
        feed = feedparser.parse(yle_kainuu_headlines_url)

    res = ''

    i = 1
    for entry in feed.entries:
        if (i >= 21) or (len(res) >= 1850):
            break
        res += f'- [{entry.title}]({entry.link})\n'
        i += 1

    res += ''
    return res

async def get_yle_latest_news():
    feed = feedparser.parse(yle_latest_news_url)

    try:
        with open('.latest_news.txt', 'r') as file:
            stored_news = file.readline().strip()
    except FileNotFoundError:
        stored_news = ""

    if feed.entries[0].title == stored_news:
        print(f"\t get_yle_latest_news(): feed.entries[0].title == stored_news ({stored_news})")
        return 0
    else:
        yle_latest_news = feed.entries[0].title
        with open('.latest_news.txt', 'w+') as file:
            file.write(yle_latest_news + '\n')
        return f'- [{feed.entries[0].title}]({feed.entries[0].link})'
