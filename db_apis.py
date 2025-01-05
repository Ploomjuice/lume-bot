"""
Managing the Quotes Game stuff

To do later:
Normalize Tables to 3rd
Implement updating


"""
from datetime import datetime
from dbutils import DBUtils


class Quote_API:
    def __init__(self):
        self.dbu = DBUtils()

    async def connect_to_db(self, username, password, database, host='localhost'):
        await self.dbu.connect(username, password, database, host)

    async def load_db(self, server):
        query = f"""
                SELECT discord_uid, username, content
                FROM messages
                WHERE discord_server = '{str(server)}'
                """
        df = await self.dbu.getdf(query)
        return df

    async def add_quote(self, discord_uid, username, content, channel, server, author):
        current_time = datetime.now()
        query = ("INSERT INTO messages "
                 "(quote_ts, discord_uid, username, content, discord_channel, discord_server, sender)"
                 "VALUES (%s, %s, %s, %s, %s, %s, %s)")

        vals = (current_time, discord_uid, username, content, channel, f"{server}", author)
        await self.dbu.insert_one(query, vals)

    async def delete_quote(self, quote_pos, server):
        query = f"DELETE FROM messages WHERE quote_order = {quote_pos} AND discord_server = '{server}'"
        # Execute

        await self.dbu.execute_query(query)

    async def retrieve_quote(self, server, quote_id):
        query = (f"SELECT username, content FROM messages WHERE (quote_order = {quote_id}) "
                 f"AND discord_server = '{server}'")

        df = await self.dbu.getdf(query)

        return tuple(df.iloc[0])

    async def load_players(self, server):
        query = f"""
                SELECT username  
                FROM players
                WHERE discord_server = '{server}'
                """
        df = await self.dbu.getdf(query)
        return list(df['username'])

    async def add_player(self, player_uid, player, server):
        query = ("INSERT INTO players (discord_uid, username, discord_server)"
                 " VALUES (%s, %s, %s)")
        vals = (player_uid, player, server)
        await self.dbu.insert_one(query, vals)

    async def add_player_lb(self, player_uid):
        query = """INSERT INTO leaderboard (discord_uid) VALUES (%s)"""

        # Execute
        await self.dbu.execute_query(query, (player_uid,))

    async def load_lb(self, server):
        query = f"""
                    select username, wins, correct, uploaded, discord_server
                    from leaderboard l 
                    join players p on (p.discord_uid = l.discord_uid)
                    WHERE discord_server = {server}
                """
        df = await self.dbu.getdf(query)
        return df

    async def load_profile(self, player, server):
        query = f"""
                    select discord_uid, wins, correct, uploaded, discord_server
                    from leaderboard l 
                    join players p on (p.discord_uid = l.discord_uid)
                    WHERE discord_server = {server} AND discord_uid = {player}
                """
        df = await self.dbu.getdf(query)
        return df

    async def update_leaderboard(self, player, correct=0, win=0):
        query = """UPDATE leaderboard
                 SET wins = wins + %s, correct = correct + %s
                 WHERE discord_uid = %s"""

        # Execute
        await self.dbu.execute_query(query, (win, correct, player))

    async def update_uploads(self, uid):
        query = """
                UPDATE leaderboard
                SET uploaded = uploaded + 1
                WHERE discord_uid = %s"""

        await self.dbu.execute_query(query, (uid,))

    async def refresh_ids(self, server):
        query1 = "set @row_number = 0"
        query2 = """update messages
                    set quote_order = (@row_number := @row_number + 1)
                    where discord_server = %s
                    order by quote_id"""

        # Execute
        await self.dbu.execute_query(query1)
        await self.dbu.execute_query(query2, (server,))
