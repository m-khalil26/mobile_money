-- Création de la table pour stocker les informations wallet
CREATE TABLE wallet_info (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    wallet_address VARCHAR(200) NOT NULL, -- Format standard pour les adresses Ethereum
    private_key VARCHAR(200) NOT NULL,    -- Format standard pour les clés privées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances des recherches
CREATE INDEX idx_phone_number ON wallet_info(phone_number);
CREATE INDEX idx_wallet_address ON wallet_info(wallet_address);

-- Fonction pour mettre à jour le timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour mettre à jour automatiquement updated_at
CREATE TRIGGER update_wallet_info_updated_at
    BEFORE UPDATE ON wallet_info
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Ajout des contraintes de sécurité
ALTER TABLE wallet_info ADD CONSTRAINT unique_wallet_address UNIQUE (wallet_address);
ALTER TABLE wallet_info ADD CONSTRAINT unique_phone_number UNIQUE (phone_number);

-- Création d'un rôle avec des permissions limitées pour l'application
CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password_change_me';
GRANT SELECT, INSERT, UPDATE ON wallet_info TO app_user;
GRANT USAGE, SELECT ON SEQUENCE wallet_info_id_seq TO app_user;