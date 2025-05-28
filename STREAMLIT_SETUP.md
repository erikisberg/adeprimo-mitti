# Streamlit + Supabase Setup Guide

## 1. Set up Supabase (5 minutes)

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Create a new project (choose a region close to you)
3. Once created, go to Settings → API
4. Copy your:
   - Project URL (looks like `https://xxxxx.supabase.co`)
   - Anon/Public key (starts with `eyJ...`)

5. Go to SQL Editor and paste the contents of `supabase_schema.sql`
6. Click "Run" to create the tables

## 2. Test locally

```bash
# Install streamlit dependencies
pip install -r requirements_streamlit.txt

# Create secrets file
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit .streamlit/secrets.toml with your credentials
# Add your Supabase URL and key

# Run the app
streamlit run streamlit_app.py
```

## 3. Deploy to Streamlit Cloud (FREE)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your GitHub repo
5. Set `streamlit_app.py` as the main file
6. Click "Advanced settings"
7. Add your secrets (paste contents of your secrets.toml)
8. Deploy!

Your app will be available at:
`https://[your-username]-[repo-name]-[random].streamlit.app`

## 4. Daily Usage

1. Visit your Streamlit app URL
2. Click "🚀 Starta analys" 
3. Watch as sites are analyzed in real-time
4. View results with ratings
5. Check historical data in the "Historik" tab

## Features

- **Real-time analysis** - See results as they come in
- **Persistent storage** - All analyses saved to Supabase
- **Historical view** - Track trends over time
- **Filter by rating** - Focus on high-interest items
- **Mobile friendly** - Works on any device

## Tips

- Run analysis once per day (morning is best)
- Set minimum rating to 3 to see only important news
- Historical view shows patterns over time
- Export interesting finds for your articles

## Troubleshooting

- **"No module named 'backend'"** - Make sure backend folder is in same directory
- **Supabase connection error** - Check your URL and key in secrets
- **OpenAI errors** - Verify your API key is correct and has credits
- **Slow loading** - Analysis takes 3-5 minutes for all sites

## Cost

- **Streamlit Cloud**: FREE
- **Supabase**: FREE (up to 500MB database)
- **OpenAI**: ~$0.10-0.20 per analysis run
- **Firecrawl**: Check your plan limits