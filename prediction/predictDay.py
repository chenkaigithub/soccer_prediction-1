from prediction.Oracle import Oracle
from prediction.NetTrainer import NetTrainer, create_net, train_and_check

LEAGUE = 'bl1'
GAME_DAY = 3

def create_a_net():
    net = create_net()
    (result, _, _, _) = train_and_check(net, ['2013','2014','2015','2016'], '2016', league=LEAGUE)
    print 'train:', result, '%'
    return net

net = create_a_net()
oracle = Oracle(net)

games = oracle.predict_game_day(LEAGUE, '2017', GAME_DAY)
for game in games:
    game.print_it()

