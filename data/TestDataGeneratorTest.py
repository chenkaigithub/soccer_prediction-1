# pylint: disable=invalid-name
from __future__ import absolute_import

import unittest

from data.TestDataGenerator import TestDataGenerator
from prediction.Judger import calculate_output_for_points


class TableStub(object):
    def __init__(self):
        self.index = {'A': 0, 'B': 1, 'C': 2}
        self.values = {'x': [4, 8, 16], 'y':[0, 1, 3]}

    def get_agg_property(self, agg, prop):
        return agg(self.values[prop])

    def get_property(self, team, prop):
        return self.values[prop][self.index[team]]

class GenerateData(unittest.TestCase):

    def setUp(self):
        self.gen = TestDataGenerator()

    def test_first_day_of_season(self):
        data = self.gen.generate_from_game_gay('bl1', '2018', 1)
        self.assertEquals(len(data), 9)

    def test_season(self):
        data = self.gen.generate_from_season('bl1', '2014')

        self.assertTrue(len(data) > 100)
        self.assertTrue(len(data) < 1000)

        input_size = 16

        offenses = []
        defenses = []

        for d in data:
            (v_input, v_output, result, _) = d
            self.assertEqual(len(v_input), input_size)
            self.assertTrue(len(v_output) == 2)
            self.assertTrue(len(result) == 1)

            offenses.extend([v_input[6], v_input[(len(v_input) / 2) + 6]])
            defenses.extend([v_input[7], v_input[(len(v_input) / 2) + 7]])

            for i in range(0, input_size):
                self.assertTrue(v_input[i] > 0)
                self.assertTrue(v_input[i] <= 1)

            for i in range(0, 2):
                self.assertTrue(v_output[i] > 0)
                self.assertTrue(v_output[i] < 1)

            self.assertTrue(result[0] in [0, 1, 2])
        self.assertEqual(max(offenses), 1)
        self.assertLess(min(offenses), 0.1)

        self.assertEqual(max(defenses), 1)
        self.assertLess(min(defenses), 0.1)

    def test_season_data_count(self):
        data = self.gen.generate_from_season('bl1', '2016')
        expected = 9 * (34 - 4 - 4 -2)
        self.assertEquals(expected, len(data))

    def test_get_output_0_0(self):
        output = calculate_output_for_points(0, 0)
        self.assertEqual(0.5, output)

    def test_get_output_5_5(self):
        output = calculate_output_for_points(5, 5)
        self.assertEqual(0.5, output)

    def test_get_output_1_0(self):
        output = calculate_output_for_points(1, 0)
        self.assertEqual(0.75, output)

    def test_get_output_2_1(self):
        output = calculate_output_for_points(2, 1)
        self.assertEqual(0.75, output)

    def test_get_output_4_2(self):
        output = calculate_output_for_points(4, 2)
        self.assertEqual(0.99, output)

    def test_get_output_3_0(self):
        output = calculate_output_for_points(3, 0)
        self.assertEqual(0.99, output)

    def test_get_output_0_10(self):
        output = calculate_output_for_points(0, 10)
        self.assertEqual(0.01, output)

    def test_get_output_4_0(self):
        output = calculate_output_for_points(4, 0)
        self.assertEqual(0.99, output)

    def test_get_output_0_2(self):
        output = calculate_output_for_points(0, 2)
        self.assertEqual(0.01, output)

    def test_get_input_1(self):
        value = self.gen.get_input_for_position(1)
        self.assertEqual(1, value)

    def test_get_input_18(self):
        value = self.gen.get_input_for_position(18)
        self.assertEqual(0.01, value)

    def test_get_input_9(self):
        value = self.gen.get_input_for_position(9)
        self.assertEqual(0.53, value)

    def test_relative_table_property_low(self):
        table = TableStub()
        value = self.gen.get_relative_table_property('A', table, 'x')
        self.assertEqual(value, 0.01)

    def test_relative_table_property_middle(self):
        table = TableStub()
        value = self.gen.get_relative_table_property('B', table, 'x')
        self.assertEqual(value, 0.33)

    def test_relative_table_property_high(self):
        table = TableStub()
        value = self.gen.get_relative_table_property('C', table, 'x')
        self.assertEqual(value, 1)

    def test_relative_table_property_not_reversed(self):
        table = TableStub()
        value = self.gen.get_relative_table_property('B', table, 'y', reverse=False)
        self.assertEqual(value, 0.33)

    def test_relative_table_property_reversed(self):
        table = TableStub()
        value = self.gen.get_relative_table_property('B', table, 'y', reverse=True)
        self.assertEqual(value, 0.68)


if __name__ == '__main__':
    unittest.main()
