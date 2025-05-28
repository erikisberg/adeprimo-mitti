# Supabase Setup Instructions

This document provides instructions for setting up the Supabase database for the Mitti Scraper project.

## Database Setup

1. Go to your Supabase project at: [https://obciwphhkqjovcthrfij.supabase.co](https://obciwphhkqjovcthrfij.supabase.co)
2. Navigate to the SQL Editor in the left sidebar
3. Create a new query and copy-paste the following SQL:

```sql
-- Create analyses table
CREATE TABLE IF NOT EXISTS analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL,
    site_name TEXT NOT NULL,
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    analysis_text TEXT,
    changes_detected BOOLEAN DEFAULT false,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create news items table
CREATE TABLE IF NOT EXISTS news_items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    date TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create URL management table
CREATE TABLE IF NOT EXISTS monitored_urls (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_analyses_analyzed_at ON analyses(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_site_name ON analyses(site_name);
CREATE INDEX IF NOT EXISTS idx_analyses_overall_rating ON analyses(overall_rating);
CREATE INDEX IF NOT EXISTS idx_news_items_analysis_id ON news_items(analysis_id);
CREATE INDEX IF NOT EXISTS idx_news_items_rating ON news_items(rating);
CREATE INDEX IF NOT EXISTS idx_monitored_urls_active ON monitored_urls(active);

-- Enable Row Level Security
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitored_urls ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth needs)
-- For now, allow all operations (you can restrict later)
CREATE POLICY "Allow all operations on analyses" ON analyses
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on news_items" ON news_items
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on monitored_urls" ON monitored_urls
    FOR ALL USING (true);
```

4. Click "Run" to execute the SQL and create the tables

## Import Initial Data

After creating the tables, let's import the initial URLs from the `urls.json` file:

1. Create a new query in the SQL Editor
2. Copy-paste and run the following SQL to set up a function to import URLs:

```sql
-- Create a function to import URLs from the application
CREATE OR REPLACE FUNCTION import_urls_from_json(urls JSONB)
RETURNS VOID AS $$
DECLARE
    url_item JSONB;
BEGIN
    FOR url_item IN SELECT * FROM jsonb_array_elements(urls)
    LOOP
        INSERT INTO monitored_urls (url, name, category, active)
        VALUES (
            url_item->>'url',
            url_item->>'name',
            COALESCE(url_item->>'category', 'Övrigt'),
            true
        )
        ON CONFLICT (url) 
        DO UPDATE SET 
            name = EXCLUDED.name,
            category = EXCLUDED.category,
            updated_at = NOW();
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

## Verify Setup

To verify that your tables were created correctly:

1. Go to the "Table Editor" in the left sidebar
2. You should see the following tables:
   - `analyses`
   - `news_items`
   - `monitored_urls`

## Next Steps

Once you've set up the tables, you can:

1. Run the Streamlit app to start saving data to Supabase
2. Use the Supabase Table Editor to view and manage the data
3. Implement the URL management feature in the Streamlit app

## Additional Notes

- The database is set up with Row Level Security (RLS) but with open policies for now
- You may want to adjust the policies if you add authentication later
- The `monitored_urls` table includes a `category` field that can be used for filtering
- All tables include timestamps for auditing 