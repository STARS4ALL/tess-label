-------------------------------
-- TESS LABEL database Data Model
-------------------------------

-- This is the database counterpart of a configuration file
-- All configurations are stored here
CREATE TABLE IF NOT EXISTS config_t
(
    section        TEXT,  -- Configuration section
    property       TEXT,  -- Property name
    value          TEXT,  -- Property value

    PRIMARY KEY(section, property)
);

-- TESS-W table
CREATE TABLE IF NOT EXISTS tess_t
(
    prefix          TEXT,    -- name prefix (i.e. stars or TAS)
    suffix          INTEGER, -- Sequential number after name prefix (ie. 0, 1, 2, etc)
    mac             TEXT,    -- Device MAC in XX:YY:ZZ:TT:UU:VV format
    sensor          TEXT,    -- Device sensor (i.e. TSL-237, Hamamantsu)
    zero_point      REAL,    -- Initial, uncalibrated Zero Point
    freq_offset,    REAL,    -- Frequency offset (dark frequency) in Hz
    interval,       INTEGER, -- Interval between measurmenets in seconds
    telnet_port     INTEGER, -- Telnet port
    broker          TEXT,    -- MQTT Broker host name
    password_hash   TEXT,    -- Password hash
    ssid            TEXT,    -- Initial SSID
    creation_date   TIMESTAMP,  -- record creation timestamp

    UNIQUE(prefix,suffix),

    PRIMARY KEY(mac)
);

