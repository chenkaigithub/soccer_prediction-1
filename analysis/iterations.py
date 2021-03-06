from prediction.NetTrainer import create_net, train_and_check
from prediction.Benchmark import verify
from analysis.Util import show_plot

def main():
    x_axis = []
    y_axis = []
    seasons = ['2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015']

    n = 25
    step = 1
    net = create_net(alpha=0.1)
    for i in range(step, n + 1, step):
        x_axis.append(i)

        result = train_and_check(net, max_iterations=step, train_set=seasons)
        verified = verify(net, delta=1)

        print 'Executed with ', i, 'iterations:', result, 'verified:', verified
        y_axis.append(result.get_performance())

    show_plot(x_axis, y_axis, n)


if __name__ == "__main__":
    main()
