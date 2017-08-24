from api.SQLiteAPI import SQLiteAPI

class TestDataGenerator(object):

    def __init__(self):
        self.api = SQLiteAPI()

    def generateFromSeason(self, league, season):
        data = []
        for i in range(5, 33):
            game_day_data = self.genererateFromGameDay(league, season, i)
            data.extend(game_day_data)
        return data

    def genererateFromGameDay(self, league, season, day):
        game_day_data = []
        game_day = self.api.get_game_day(league, season, day)

        state = day - 1
        table = self.api.get_game_table(league, season, state)
        table_trend = self.api.get_game_table_trend(league, season, state)
        table_home = self.api.get_game_table_home(league, season, state)
        table_away = self.api.get_game_table_away(league, season, state)

        for game in game_day:
            ht = game.get_home_team()
            hp = game.get_home_points()
            (pos_home, pos_home_trend, x_pos_home, x_pos_home_trend, home_home, x_home_home) =\
                self.extractInput(table, table_trend, table_home, ht)

            at = game.get_away_team()
            ap = game.get_away_points()
            (pos_away, pos_away_trend, x_pos_away, x_pos_away_trend, home_away, x_home_away) =\
                self.extractInput(table, table_trend, table_away, at)

            y_points_home = self.get_output_for_points(hp, ap)
            y_points_away = self.get_output_for_points(ap, hp)

            result = self.calculate_result(hp, ap)
            input = [x_pos_home, x_pos_away, x_pos_home_trend, x_pos_away_trend, x_home_home, x_home_away]
            output = [y_points_home, y_points_away]
            game_day_data.append((input, output, [result]))
        return game_day_data

    def extractInput(self, table, table_trend, table_home, team):
        pos = table.get_position(team)
        x_pos = self.get_input_for_position(pos)

        trend = table_trend.get_position(team)
        x_trend = self.get_input_for_position(trend)

        home = table_home.get_position(team)
        x_home = self.get_input_for_position(home)

        return (pos, trend, x_pos, x_trend, home, x_home)

    def get_input_for_position(self, position):
        input = max(((18 - position) / 17.0), 0.01)
        return round(input, 2)

    def get_output_for_points(self, x, y):
        diff = x - y
        out = 0.5 + (0.15 * diff)
        out = max(min(out, 0.99), 0.01)
        return out

    def calculate_result(self, home, away):
        if home > away:
            return 1
        if away > home:
            return 2
        return 0