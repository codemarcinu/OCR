-- Tabela z podstawowymi informacjami o paragonach
CREATE TABLE IF NOT EXISTS receipts (
    receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name VARCHAR(100) NOT NULL,
    store_address TEXT,
    store_nip VARCHAR(20),
    purchase_date DATE NOT NULL,
    purchase_time TIME NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50),
    receipt_number VARCHAR(50),
    register_number VARCHAR(20),
    loyalty_card_used BOOLEAN DEFAULT FALSE,
    loyalty_card_savings DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela z pozycjami paragonu
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,                    -- Oryginalna nazwa z paragonu
    item_name_standardized TEXT,                -- Nazwa ujednolicona przez AI
    quantity DECIMAL(10,3) NOT NULL,
    unit VARCHAR(20),                           -- szt, kg, l, opak
    unit_price_original DECIMAL(10,2),          -- Cena jednostkowa przed rabatem
    unit_price_after_discount DECIMAL(10,2),    -- Cena jednostkowa po rabacie
    item_discount_amount DECIMAL(10,2),         -- Kwota rabatu na pozycję
    item_total_price DECIMAL(10,2) NOT NULL,    -- Końcowa cena za pozycję
    vat_rate VARCHAR(1),                        -- A, B, C, D
    ai_category VARCHAR(100),                   -- Kategoria nadana przez AI
    is_frozen BOOLEAN DEFAULT FALSE,            -- Czy produkt jest mrożony
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

-- Tabela z rabatami ogólnymi
CREATE TABLE IF NOT EXISTS discounts (
    discount_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    discount_name TEXT NOT NULL,
    discount_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

-- Tabela z informacjami o VAT
CREATE TABLE IF NOT EXISTS vat_summary (
    vat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    vat_rate VARCHAR(1) NOT NULL,           -- A, B, C, D
    base_amount DECIMAL(10,2) NOT NULL,     -- Podstawa opodatkowania
    vat_amount DECIMAL(10,2) NOT NULL,      -- Kwota VAT
    vat_percent INTEGER NOT NULL,           -- Wartość procentowa (23, 8, 5, 0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

-- Tabela z wykorzystanymi kuponami
CREATE TABLE IF NOT EXISTS used_coupons (
    coupon_id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id INTEGER NOT NULL,
    coupon_name TEXT NOT NULL,
    coupon_value DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

-- Indeksy dla poprawy wydajności
CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(purchase_date);
CREATE INDEX IF NOT EXISTS idx_receipts_store ON receipts(store_name);
CREATE INDEX IF NOT EXISTS idx_items_receipt ON items(receipt_id);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(ai_category);
CREATE INDEX IF NOT EXISTS idx_discounts_receipt ON discounts(receipt_id);
CREATE INDEX IF NOT EXISTS idx_vat_receipt ON vat_summary(receipt_id);
CREATE INDEX IF NOT EXISTS idx_coupons_receipt ON used_coupons(receipt_id); 