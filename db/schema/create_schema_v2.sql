-- ==========================================================
--   MPD — PFT v2 : création du schéma (PostgreSQL 18)
--   À exécuter sur une base VIDE. Modèle : docs/merise/MCD.md
-- ==========================================================

BEGIN;

------------------------------------------------------------
-- 1. COMPTES D'ACCÈS À L'APP (indépendants du patrimoine)
------------------------------------------------------------
CREATE TABLE app_user (
    user_id        INTEGER GENERATED ALWAYS AS IDENTITY,
    email          VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           VARCHAR(10)  NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT pk_app_user PRIMARY KEY (user_id),
    CONSTRAINT uq_app_user_email UNIQUE (email),
    CONSTRAINT ck_app_user_role CHECK (role IN ('admin', 'viewer'))
);

------------------------------------------------------------
-- 2. PORTEFEUILLES (enveloppes : PEA, CTO, PEE, livrets)
------------------------------------------------------------
CREATE TABLE portfolio (
    portfolio_id      INTEGER GENERATED ALWAYS AS IDENTITY,
    portfolio_name    VARCHAR(50) NOT NULL,
    institution_name  VARCHAR(50) NOT NULL,
    wrapper_type      VARCHAR(10) NOT NULL,
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_portfolio PRIMARY KEY (portfolio_id),
    CONSTRAINT uq_portfolio_name UNIQUE (portfolio_name),
    CONSTRAINT ck_portfolio_wrapper_type CHECK (wrapper_type IN ('PEA', 'CTO', 'PEE', 'LIVRET'))
);

------------------------------------------------------------
-- 3. ACTIFS (une seule fois en base, quel que soit le portefeuille)
------------------------------------------------------------
CREATE TABLE asset (
    asset_id    INTEGER GENERATED ALWAYS AS IDENTITY,
    asset_name  VARCHAR(100) NOT NULL,
    ticker      VARCHAR(20),
    is_cash     BOOLEAN      NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_asset PRIMARY KEY (asset_id),
    CONSTRAINT uq_asset_name UNIQUE (asset_name),
    CONSTRAINT uq_asset_ticker UNIQUE (ticker)   -- plusieurs NULL autorisés
);

------------------------------------------------------------
-- 4. COTATIONS (historique des prix, rattaché à l'actif)
------------------------------------------------------------
CREATE TABLE quote (
    quote_id    INTEGER GENERATED ALWAYS AS IDENTITY,
    asset_id    INTEGER       NOT NULL,
    quote_date  DATE          NOT NULL,
    price       NUMERIC(12,6) NOT NULL,
    CONSTRAINT pk_quote PRIMARY KEY (quote_id),
    CONSTRAINT fk_quote_asset FOREIGN KEY (asset_id)
        REFERENCES asset (asset_id) ON DELETE RESTRICT,
    CONSTRAINT uq_quote_asset_date UNIQUE (asset_id, quote_date),
    CONSTRAINT ck_quote_price CHECK (price > 0)
);

------------------------------------------------------------
-- 5. LIGNES DE DÉTENTION (un actif dans un portefeuille)
------------------------------------------------------------
CREATE TABLE holding (
    holding_id    INTEGER GENERATED ALWAYS AS IDENTITY,
    portfolio_id  INTEGER NOT NULL,
    asset_id      INTEGER NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_holding PRIMARY KEY (holding_id),
    CONSTRAINT fk_holding_portfolio FOREIGN KEY (portfolio_id)
        REFERENCES portfolio (portfolio_id) ON DELETE RESTRICT,
    CONSTRAINT fk_holding_asset FOREIGN KEY (asset_id)
        REFERENCES asset (asset_id) ON DELETE RESTRICT,
    CONSTRAINT uq_holding_portfolio_asset UNIQUE (portfolio_id, asset_id)
);

------------------------------------------------------------
-- 6. MOUVEMENTS (flux : achats, apports, retraits miroir...)
------------------------------------------------------------
CREATE TABLE movement (
    movement_id    INTEGER GENERATED ALWAYS AS IDENTITY,
    holding_id     INTEGER       NOT NULL,
    movement_date  DATE          NOT NULL,
    movement_type  VARCHAR(20)   NOT NULL,
    quantity       NUMERIC(15,6) NOT NULL,
    unit_price     NUMERIC(12,6) NOT NULL,
    fees           NUMERIC(8,2)  NOT NULL DEFAULT 0,
    CONSTRAINT pk_movement PRIMARY KEY (movement_id),
    CONSTRAINT fk_movement_holding FOREIGN KEY (holding_id)
        REFERENCES holding (holding_id) ON DELETE RESTRICT,
    CONSTRAINT ck_movement_quantity CHECK (quantity <> 0),
    CONSTRAINT ck_movement_unit_price CHECK (unit_price >= 0),
    CONSTRAINT ck_movement_fees CHECK (fees >= 0),
    -- Doit rester synchronisé avec MovementType (core/constants.py), test #9
    CONSTRAINT ck_movement_type CHECK (movement_type IN (
        'ACHAT', 'VENTE', 'DIVIDENDE', 'APPORT', 'RETRAIT', 'ABONDEMENT',
        'INTERET', 'AJUSTEMENT', 'RETRAIT_MIROIR', 'TRANSFERT'
    ))
);

------------------------------------------------------------
-- 7. INDEX (en plus de ceux créés par les PK et les UNIQUE)
------------------------------------------------------------
-- quote : uq_quote_asset_date couvre déjà la FK et « dernière cotation par actif »
-- holding : uq_holding_portfolio_asset couvre déjà la FK portfolio_id
CREATE INDEX idx_holding_asset ON holding (asset_id);

-- Mouvements d'une ligne dans le temps (vues historiques, TRI)
CREATE INDEX idx_movement_holding_date ON movement (holding_id, movement_date);
-- Filtres par période tous portefeuilles confondus (apports mensuels)
CREATE INDEX idx_movement_date ON movement (movement_date);

------------------------------------------------------------
-- 8. DOCUMENTATION DANS LE CATALOGUE (visible dans DBeaver)
------------------------------------------------------------
COMMENT ON TABLE app_user  IS 'Comptes d''accès à l''app et aux API (rôles admin / viewer). Données perso : registre RGPD.';
COMMENT ON TABLE portfolio IS 'Enveloppes financières. Le taux d''imposition par wrapper_type est dans settings/config.yaml.';
COMMENT ON TABLE asset     IS 'Actifs (ETF, actions, fonds, cash, livrets), uniques quel que soit le portefeuille.';
COMMENT ON TABLE quote     IS 'Historique des prix par actif, une cotation par jour au plus.';
COMMENT ON TABLE holding   IS 'Ligne de détention : un actif dans un portefeuille. Remplace pdt_id dans les vues.';
COMMENT ON TABLE movement  IS 'Flux. Un achat ETF = ACHAT sur le titre + RETRAIT_MIROIR sur la ligne cash.';

COMMIT;