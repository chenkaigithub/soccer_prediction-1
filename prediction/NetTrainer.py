from data.TestDataGenerator import TestDataGenerator
from net.NeuralNetwork import NN2
from prediction.judger.DrawDiff import calculate_confidence, interprete

def create_net(alpha=0.1, input_layer=16, hidden_layer=14, output_layer=2):
    net = NN2(input_layer, hidden_layer, output_layer, alpha)
    return net

def train_and_check(net, train_set=None, check='2016', train_leagues=None,
                    max_iterations=2, league='bl1', min_delta=0.2):
    if train_set is None:
        train_set = ['2013', '2014', '2015']
    if not train_leagues:
        train_leagues = [league]
    trainer = NetTrainer(net)
    error = 99999
    for _ in range(0, max_iterations):
        for a_league in train_leagues:
            prev_error = error
            error = trainer.train_seasons(a_league, train_set)
            delta = prev_error - error
            if delta < min_delta:
                return trainer.check_season(league, check)

    return trainer.check_season(league, check)

class PickLeader(object):
    def query(self, input_list):
        home = input_list[0]
        away = input_list[len(input_list)/2]

        if home > away:
            return [0.99, 0.01]

        return [0.01, 0.99]

    def train(self, _input_list, _target_list):
        pass

class PickHome(object):
    def query(self, _input_list):
        return [0.99, 0.01]

    def train(self, _input_list, _target_list):
        pass

class PickAway(object):
    def query(self, _input_list):
        return [0.01, 0.99]

    def train(self, _input_list, _target_list):
        pass

class PickDraw(object):
    def query(self, _input_list):
        return [0.5, 0.5]

    def train(self, _input_list, _target_list):
        pass


class NetTrainer(object):

    def __init__(self, net):
        self.net = net
        self.generator = TestDataGenerator()
        self.count = 0
        self.hits = 0
        self.statistics = [0, 0, 0]

    def train_seasons(self, league, seasons):
        train_data = []
        for season in seasons:
            season_data = self.generator.generateFromSeason(league, season)
            train_data.extend(season_data)

        total_error = 0
        for data in train_data:
            (input_list, output_list, _, _) = data
            (_, errors) = self.net.train(input_list, output_list)
            single_error = abs(errors[0][0]) + abs(errors[1][0])
            total_error = total_error + single_error

        return total_error

    def check_game_day(self, league, season, game_day):
        game_day_data = self.generator.genererateFromGameDay(league, season, game_day)
        return_code = self._check_data(game_day_data)
        return return_code

    def check_season(self, league, season):
        season_data = self.generator.generateFromSeason(league, season)
        return_code = self._check_data(season_data)
        return return_code

    def _check_data(self, all_data):
        self._reset_statistics()
        for data in all_data:
            (input_list, _, result, _) = data
            result = result[0]
            query_output = self.net.query(input_list)
            query_result = interprete(query_output)
            self._update_statistics(result, query_result)
        return_code = self._get_result()
        return return_code

    def _reset_statistics(self):
        self.count = 0
        self.hits = 0
        self.statistics = [0, 0, 0]

    def _update_statistics(self, expected, actual):
        self.count = self.count + 1
        if expected == actual:
            self.hits = self.hits + 1
            self.statistics[actual] = self.statistics[actual] + 1

    def _get_result(self):
        percent = 100.0 * self.hits / self.count
        performance = int(percent)
        return (performance, self.hits, self.count, self.statistics)
