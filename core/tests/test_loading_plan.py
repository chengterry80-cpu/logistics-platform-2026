"""
二维装箱算法单元测试

测试 Skyline + Bottom-Left 算法的正确性，覆盖：
1. 单件货物放置
2. 多件货物排列
3. 旋转优化
4. 超重/超尺寸拒绝
5. 不重叠约束
6. 边界约束
"""

from django.test import TestCase

from core.algorithms.loading_plan import (
    generate_loading_plan,
    skyline_add_node,
    find_best_position,
    can_place,
    _rect_overlaps,
)


class SkylineMergeTest(TestCase):
    """测试 Skyline 节点添加"""

    def test_add_single_node(self):
        skyline = []
        result = skyline_add_node(skyline, 0, 0, 2000, 1500)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], (0, 0, 2000, 1500))

    def test_add_multiple_nodes(self):
        skyline = []
        skyline = skyline_add_node(skyline, 0, 0, 1000, 1000)
        skyline = skyline_add_node(skyline, 1000, 0, 1000, 1000)
        self.assertEqual(len(skyline), 2)


class BestPositionTest(TestCase):
    """测试最佳位置查找"""

    def test_empty_skyline(self):
        x, y = find_best_position([], 1000, 500, 6000, 2400)
        self.assertEqual((x, y), (0, 0))

    def test_find_position_next_to_existing(self):
        placed = [(0, 0, 2000, 1500)]
        x, y = find_best_position(placed, 1000, 500, 6000, 2400)
        self.assertEqual(x, 2000)
        self.assertEqual(y, 0)

    def test_find_position_second_row(self):
        """第一行满了，找第二行"""
        placed = [(0, 0, 5000, 2400)]
        x, y = find_best_position(placed, 2000, 500, 6000, 2400)
        self.assertEqual((x, y), (-1, -1))  # 第一行全满且没有第二行空间

    def test_finds_underneath(self):
        """在较小货物下方放置"""
        placed = [(0, 1000, 3000, 500)]
        x, y = find_best_position(placed, 2000, 500, 6000, 2400)
        self.assertEqual(x, 0)
        self.assertEqual(y, 0)

    def test_no_room_too_big(self):
        placed = [(0, 0, 5500, 2400)]
        x, y = find_best_position(placed, 2000, 3000, 6000, 2400)
        self.assertEqual((x, y), (-1, -1))


class OverlapTest(TestCase):
    """测试重叠检测"""

    def test_no_overlap_empty(self):
        self.assertFalse(_rect_overlaps(0, 0, 100, 100, 100, 100, 100, 100))

    def test_no_overlap_adjacent(self):
        self.assertFalse(_rect_overlaps(0, 0, 100, 100, 100, 0, 100, 100))

    def test_overlap_in_same_area(self):
        self.assertTrue(_rect_overlaps(50, 50, 100, 100, 0, 0, 200, 200))

    def test_partial_overlap(self):
        self.assertTrue(_rect_overlaps(0, 0, 100, 100, 50, 50, 100, 100))


class GenerateLoadingPlanTest(TestCase):
    """主算法测试"""

    def setUp(self):
        self.vehicle = {
            'length': 6000,      # 6m
            'width': 2400,       # 2.4m
            'height': 2500,      # 2.5m
            'load_capacity': 10000,  # 10吨
        }

    def test_single_cargo(self):
        """测试单件货物放置"""
        cargo = [{
            'cargo_id': 1,
            'length': 2000, 'width': 1500, 'height': 1200,
            'weight': 1000,
        }]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 1)
        self.assertEqual(result['placed'][0]['cargo_id'], 1)
        self.assertEqual(len(result['unplaced']), 0)
        self.assertEqual(result['total_weight'], 1000)

    def test_two_cargos_side_by_side(self):
        """测试两件货物并排排列"""
        cargo = [
            {'cargo_id': 1, 'length': 1500, 'width': 2000, 'height': 1000, 'weight': 500},
            {'cargo_id': 2, 'length': 1500, 'width': 2000, 'height': 1000, 'weight': 600},
        ]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 2)
        self.assertEqual(len(result['unplaced']), 0)

        # 验证两件货物不重叠
        placed = result['placed']
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                a, b = placed[i], placed[j]
                ax1, ay1 = a['x'], a['y']
                ax2, ay2 = a['x'] + a['width'], a['y'] + a['length']
                bx1, by1 = b['x'], b['y']
                bx2, by2 = b['x'] + b['width'], b['y'] + b['length']
                self.assertFalse(
                    ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1,
                    f"Cargo {a['cargo_id']} 和 Cargo {b['cargo_id']} 发生重叠"
                )

    def test_rotated_placement(self):
        """测试旋转优化"""
        cargo = [{
            'cargo_id': 1,
            'length': 3000, 'width': 1000, 'height': 800,
            'weight': 800,
        }]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 1)

    def test_overweight_rejected(self):
        """测试超重拒绝"""
        self.vehicle['load_capacity'] = 500
        cargo = [
            {'cargo_id': 1, 'length': 1000, 'width': 1000, 'height': 500, 'weight': 300},
            {'cargo_id': 2, 'length': 1000, 'width': 1000, 'height': 500, 'weight': 300},
        ]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 1)
        self.assertEqual(len(result['unplaced']), 1)
        self.assertIn('载重', result['unplaced'][0]['reason'])

    def test_oversized_rejected(self):
        """测试超尺寸拒绝"""
        self.vehicle['length'] = 2000
        self.vehicle['width'] = 2000
        cargo = [{
            'cargo_id': 1,
            'length': 3000, 'width': 3000, 'height': 1000,
            'weight': 500,
        }]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 0)
        self.assertEqual(len(result['unplaced']), 1)

    def test_height_exceeded(self):
        """测试高度超限拒绝"""
        self.vehicle['height'] = 500
        cargo = [{
            'cargo_id': 1,
            'length': 1000, 'width': 1000, 'height': 800,
            'weight': 200,
        }]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertEqual(len(result['placed']), 0)
        self.assertEqual(len(result['unplaced']), 1)
        self.assertIn('高度', result['unplaced'][0]['reason'])

    def test_no_overlap_constraint(self):
        """测试多件货物不重叠约束（10件）"""
        cargo = [
            {'cargo_id': i, 'length': 1000, 'width': 800, 'height': 500,
             'weight': 200}
            for i in range(10)
        ]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertGreaterEqual(len(result['placed']), 5)

        # 验证所有已放置货物不重叠
        placed = result['placed']
        for i in range(len(placed)):
            for j in range(i + 1, len(placed)):
                a, b = placed[i], placed[j]
                ax1, ay1 = a['x'], a['y']
                ax2, ay2 = a['x'] + a['width'], a['y'] + a['length']
                bx1, by1 = b['x'], b['y']
                bx2, by2 = b['x'] + b['width'], b['y'] + b['length']
                self.assertFalse(
                    ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1,
                    f"货物 {a['cargo_id']} 和 {b['cargo_id']} 重叠: "
                    f"{ax1},{ay1},{ax2},{ay2} vs {bx1},{by1},{bx2},{by2}"
                )

    def test_empty_list(self):
        """测试空列表"""
        result = generate_loading_plan([], self.vehicle)
        self.assertEqual(result['placed'], [])
        self.assertEqual(result['unplaced'], [])
        self.assertEqual(result['total_weight'], 0)

    def test_utilization(self):
        """测试利用率计算"""
        cargo = [{
            'cargo_id': 1,
            'length': 3000, 'width': 2000, 'height': 1000,
            'weight': 2000,
        }]
        result = generate_loading_plan(cargo, self.vehicle)
        self.assertGreater(result['vehicle_utilization'], 0)
        self.assertLessEqual(result['vehicle_utilization'], 1)


class CanPlaceTest(TestCase):
    """测试 can_place 函数"""

    def setUp(self):
        self.vehicle = {
            'length': 6000, 'width': 2400, 'height': 2500, 'load_capacity': 10000,
        }

    def test_can_place_valid(self):
        cargo = {'length': 2000, 'width': 1500, 'height': 1200, 'weight': 500}
        ok, reason = can_place(cargo, self.vehicle, [], 0, 0)
        self.assertTrue(ok)
        self.assertEqual(reason, '')

    def test_exceeds_length(self):
        """x+width 超出车辆长度边界"""
        cargo = {'length': 3000, 'width': 5000, 'height': 1000, 'weight': 500}
        ok, reason = can_place(cargo, self.vehicle, [], 2000, 0)
        self.assertFalse(ok)
        self.assertIn('长度边界', reason)

    def test_exceeds_width(self):
        """y+length 超出车辆宽度边界"""
        cargo = {'length': 5000, 'width': 3000, 'height': 1000, 'weight': 500}
        ok, reason = can_place(cargo, self.vehicle, [], 0, 0)
        self.assertFalse(ok)
        self.assertIn('宽度边界', reason)

    def test_exceeds_height(self):
        cargo = {'length': 1000, 'width': 1000, 'height': 3000, 'weight': 500}
        ok, reason = can_place(cargo, self.vehicle, [], 0, 0)
        self.assertFalse(ok)
        self.assertIn('高度', reason)

    def test_overlap_with_existing(self):
        cargo = {'length': 1000, 'width': 1000, 'height': 500, 'weight': 200}
        placed = [(0, 0, 2000, 1500)]
        ok, reason = can_place(cargo, self.vehicle, placed, 500, 500)
        self.assertFalse(ok)
        self.assertIn('重叠', reason)

    def test_no_overlap(self):
        cargo = {'length': 1000, 'width': 1000, 'height': 500, 'weight': 200}
        placed = [(0, 0, 2000, 1500)]
        ok, reason = can_place(cargo, self.vehicle, placed, 2500, 0)
        self.assertTrue(ok)

    def test_rotated_placement(self):
        cargo = {'length': 3000, 'width': 1000, 'height': 800, 'weight': 300}
        ok, reason = can_place(cargo, self.vehicle, [], 0, 0, rotated=True)
        self.assertTrue(ok)
