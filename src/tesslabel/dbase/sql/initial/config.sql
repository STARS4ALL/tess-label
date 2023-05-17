BEGIN TRANSACTION;
--------------------------------------------------------
-- Miscelaneous data to be inserted at database creation
--------------------------------------------------------

-----------------
-- Global section
-----------------

INSERT INTO config_t(section, property, value) 
VALUES ('database', 'version', '01');

-----------------------
-- Device communication
-----------------------

INSERT INTO config_t(section, property, value) 
VALUES ('device', 'model', 'TESS-W');
INSERT INTO config_t(section, property, value) 
VALUES ('device', 'endpoint', 'udp:192.168.4.1:2255');
INSERT INTO config_t(section, property, value) 
VALUES ('device', 'old_proto', '0');

---------------------------------------
-- TESS-W default configuration section
---------------------------------------

INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'prefix', 'stars');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'number', '1000');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'zero_point', '20.50');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'freq_offset', '1000');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'interval', '60');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'telnet_port', '23');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'SSID', 'MiFibra-09E0');
INSERT INTO config_t(section, property, value) 
VALUES ('TESS-W', 'sensor', 'TSL-237');

------------------------------------
-- TAS default configuration section
------------------------------------

INSERT INTO config_t(section, property, value) 
VALUES ('TAS', 'prefix', 'TAS');

---------------------------------------
-- TESS-P default configuration section
---------------------------------------

INSERT INTO config_t(section, property, value) 
VALUES ('TESS-P', 'prefix', 'TESS-P');

COMMIT;