CREATE TABLE auth(name string primary key, auth int NOT NULL DEFAULT -5, timezone string NOT NULL DEFAULT "Europe/Amsterdam");
CREATE TABLE logout(channel string, nick string, tijd int, reason string, primary key (channel,nick));
CREATE TABLE netsplit(channel string,nick string, servers string, timeout int, PRIMARY KEY(channel,nick));
CREATE TABLE notes(nick string, msg string);
CREATE TABLE offline(channel string, nick string, tijd int);
CREATE TABLE paginas(tijd integer, nick text, paginas integer);
CREATE TABLE reminds (channel string, nick string, msg string, tijd int);
CREATE TABLE telefoonnrs (naam text,nummer text);
