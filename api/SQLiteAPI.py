#encoding=utf8
import sqlite3

import api.OpenLigaDB as OpenLigaDB
from analysis.Util import normalize_team_name

def is_similar_teamname(team1, team2):
    for token in team1.split(" "):
        if len(token) < 4:
            continue
        if token in team2:
            return True
    return False

class Game(object):
    def __init__(self, data):
        self.data = data

    def print_data(self):
        for x in self.data:
            print(x)

    def get_home_team(self):
        return self.data[0].encode('utf-8')

    def get_home_points(self):
        return self.data[1]

    def get_away_team(self):
        return self.data[2].encode('utf-8')

    def get_away_points(self):
        return self.data[3]

    def print_it(self):
        print('%25s : %25s' % (self.get_home_team(), self.get_away_team()))

class Position(object):
    def __init__(self, data):
        (self.name, self.points, self.diff, self.offense, self.defense) = data

    def __getitem__(self, item):
        if item == 'defense':
            return self.defense
        elif item == 'offense':
            return self.offense
        return None

    def print_it(self):
        print(self.name, self.points, self.diff)

class GameTable(object):
    def __init__(self, data):
        self.positions = map(Position, data)
        if (len(self.positions) != 18) and (len(self.positions) != 9):
            raise BaseException("Unexpected table length: " + str(len(self.positions)))

    def get_name(self, position):
        name = self.positions[position-1].name.encode('utf-8')
        return name

    def get_points(self, position):
        points = self.positions[position-1].points
        return points

    def get_position(self, name):
        for i in range(1, len(self.positions)+1):
            n = self.get_name(i)
            if n == name:
                return i

        for i in range(1, len(self.positions)+1):
            n = self.get_name(i)
            if is_similar_teamname(n, name):
                return i

        if self.is_new_to_league(name):
            return 18

        #FIXME first game day(s)
        if len(self.positions) == 9:
            return 5
        raise BaseException("Team not found in GameTable: " + name)

    def is_new_to_league(self, name):
        #TODO Find better solution
        return name in ['Fortuna Düsseldorf', '1. FC Nürnberg']

    def get_goal_diff(self, position):
        diff = self.positions[position - 1].diff
        return diff

    def print_data(self):
        for pos in self.positions:
            pos.print_it()

    def _get_max_offense(self):
        return max(self._get_position_property('offense'))

    def _get_min_offense(self):
        return min(self._get_position_property('offense'))

    def get_property(self, name, prop):
        pos = self.get_position(name)
        value = self.positions[pos - 1][prop]
        return value

    def get_agg_property(self, agg, prop):
        return agg(self._get_position_property(prop))

    def _get_max_defense(self):
        return max(self._get_position_property('defense'))

    def _get_min_defense(self):
        return min(self._get_position_property('defense'))

    def _get_position_property(self, prop):
        return [p[prop] for p in self.positions]


class SQLiteAPI(object):
    def __init__(self):
        self.api = OpenLigaDB.OpenLigaDB()
        self.conn = None

    def _import_data(self, league, season, data, debug=False):
        for game in data:
            if debug:
                print(game)
            game_day = game['Group']['GroupOrderID']
            match = game['MatchID']

            team = self.get_name(game['Team1'])
            home = 1
            goals_own = self.get_result(game)['PointsTeam1']
            goals_opponent = self.get_result(game)['PointsTeam2']
            points = self.calculate_points(goals_own, goals_opponent)
            if not debug:
                self.insert_game(league, season, game_day, team,
                                 home, goals_own, goals_opponent, points, match)

            team = self.get_name(game['Team2'])
            home = 0
            goals_own = self.get_result(game)['PointsTeam2']
            goals_opponent = self.get_result(game)['PointsTeam1']
            points = self.calculate_points(goals_own, goals_opponent)
            if not debug:
                self.insert_game(league, season, game_day, team, home,
                                 goals_own, goals_opponent, points, match)

    def select_first_after_break(self, league, season):
        self.conn = sqlite3.connect('games.sqlite')
        cursor = self.conn.cursor()
        result = cursor.execute("SELECT game_day_after "
                                "FROM breaks "
                                "WHERE league = ? and season = ?", [league, season]).fetchall()
        self.conn.close()

        if not result:
            return -99

        (game_day,) = result[0]
        return game_day

    def import_game_day(self, league, season, game_day, debug=False):
        self.conn = sqlite3.connect('games.sqlite')
        self._delete_game_day(league, season, game_day)

        data = self.api.request_data_game_day(league, season, game_day)
        self._import_data(league, season, data, debug)

        self.conn.commit()
        self.conn.close()

    def _delete_game_day(self, league, season, game_day):
        self.conn.execute(u"DELETE FROM results WHERE league = '{0}' "
                          u"AND season = '{1}' AND game_day = '{2}'"
                          .format(league, season, game_day))

    def _delete_season(self, league, season):
        self.conn.execute(u"DELETE FROM results WHERE league = '{0}' "
                          u"AND season = '{1}'"
                          .format(league, season))

    def import_season(self, league, season, debug=False):
        self.conn = sqlite3.connect('games.sqlite')
        self._delete_season(league, season)

        data = self.api.request_data(league, season)
        self._import_data(league, season, data, debug)

        self.conn.commit()
        self.conn.close()

    def get_result(self, game):
        if not game:
            return None

        for result in game['MatchResults']:
            if result['ResultName'] == 'Endergebnis':
                return result
        return {"PointsTeam1": -1, "PointsTeam2": -1}

    def calculate_points(self, goals1, goals2):
        if goals1 > goals2:
            return 3
        if goals2 > goals1:
            return 0
        return 1

    def get_name(self, team):
        return team['TeamName']

    def insert_game(self, league, season, game_day, team, home, goals_own,
                    goals_opponent, points, match):
        team = normalize_team_name(team)
        cursor = self.conn.cursor()
        cursor.execute(u"INSERT INTO results VALUES"
                       u"('{0}', '{1}', {2}, '{3}', {4}, {5}, {6}, {7}, {8})"
                       .format(league, season, game_day, team, home, goals_own,
                               goals_opponent, points, match))

    def get_game_table(self, league, season, game_day):
        table = self.get_game_table_generic(league, season, game_day, "1 =", 1)
        return table

    def get_game_table_trend(self, league, season, game_day, trend=2):
        table = self.get_game_table_generic(league, season, game_day, "game_day >",
                                            (game_day - trend))
        return table

    def get_game_table_home(self, league, season, game_day):
        table = self.get_game_table_generic(league, season, game_day, "home =", 1)
        return table

    def get_game_table_away(self, league, season, game_day):
        table = self.get_game_table_generic(league, season, game_day, "home =", 0)
        return table

    def get_game_table_generic(self, league, season, game_day, additional_prop, binding):
        self.conn = sqlite3.connect('games.sqlite')
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT team, SUM(points), SUM(goals_own - goals_opponent), "
                              "SUM(goals_own), SUM(goals_opponent)"
                              "FROM results "
                              "WHERE league = ? and season = ? and game_day <= ? and {0} ? "
                              ""
                              "GROUP BY team "
                              "ORDER BY 2 DESC, 3 DESC, 4 DESC".format(additional_prop),
                              [league, season, game_day, binding]).fetchall()
        self.conn.close()

        try:
            table = GameTable(data)
        except:
            debug_info = "season: {}, game day: {}, property: {}".format(season, game_day, additional_prop)
            print(debug_info)
            raise
        return table

    def get_game_day(self, league, season, game_day):
        games = []
        self.conn = sqlite3.connect('games.sqlite')
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT home.team, home.goals_own, away.team, away.goals_own "
                              "FROM results home "
                              "INNER JOIN "
                              "results away "
                              "ON home.match = away.match "
                              "WHERE home.league = ? and home.season = ? and home.game_day = ? "
                              "AND away.league = ? and away.season = ? and away.game_day = ? "
                              "AND home.home = 1 "
                              "AND away.home = 0 ",
                              [league, season, game_day, league, season, game_day]).fetchall()

        for row in data:
            games.append(Game(row))

        self.conn.close()
        return games


    def print_data(self):
        self.conn = sqlite3.connect('games.sqlite')
        cursor = self.conn.cursor()
        data = cursor.execute("SELECT count(*), max(game_day), league, season "
                              "FROM results "
                              "GROUP BY league, season "
                              "ORDER BY league, season DESC").fetchall()

        for row in data:
            print(row)

        self.conn.close()
