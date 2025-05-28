-- Supabase schema for Mitti AI

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
CREATE INDEX idx_analyses_analyzed_at ON analyses(analyzed_at DESC);
CREATE INDEX idx_analyses_site_name ON analyses(site_name);
CREATE INDEX idx_analyses_overall_rating ON analyses(overall_rating);
CREATE INDEX idx_news_items_analysis_id ON news_items(analysis_id);
CREATE INDEX idx_news_items_rating ON news_items(rating);
CREATE INDEX idx_monitored_urls_active ON monitored_urls(active);

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