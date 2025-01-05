drop database if exists quotes;
create database if not exists quotes;

use quotes;




drop table if exists messages;
create table messages(
	quote_id mediumint PRIMARY KEY AUTO_INCREMENT,
    quote_ts datetime,
    discord_uid bigint,
    username varchar(32),
    content varchar(2000),
    discord_channel varchar(100),
    discord_server varchar(100),
    sender varchar(32),
    quote_order mediumint auto_increment
);


drop table if exists players;
create table players(
	main_id int primary key auto_increment,
    discord_uid bigint,
    username varchar(32),
    discord_server varchar(100)
);

drop table if exists leaderboard;
create table leaderboard(
	entry_id int primary key auto_increment,
    discord_uid bigint,
    wins int DEFAULT 0,
    correct int DEFAULT 0,
    uploaded int DEFAULT 0
);

drop table if exists nicknames;
create table nicknames(
	
)

DELIMITER //

create trigger init_lb
after insert on players
for each row
begin
	insert into leaderboard (discord_uid)
    values (new.discord_uid);
end;

