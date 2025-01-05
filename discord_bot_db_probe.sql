use quotes;

select *
from messages;


select *
from leaderboard;

select *
from players;

select username, wins, correct, uploaded, discord_server
from leaderboard l 
join players p on (p.discord_uid = l.discord_uid);

truncate table leaderboard;

alter table messages add column quote_order mediumint;

set @row_number = 0;
update messages
set quote_order = (@row_number := @row_number + 1)
order by quote_id;

select username, wins, correct
from leaderboard l join players p on (p.discord_uid = l.discord_uid);
