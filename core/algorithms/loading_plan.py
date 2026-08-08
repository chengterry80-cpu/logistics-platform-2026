"""
Skyline + Bottom-Left 二维装箱算法

用于生成运输车辆的装车方案，在二维平面上（底面）放置货物。
核心思路：维护一条 Skyline（天际线）表示已占用区域的右边界，
逐件货物按面积降序排列后，尝试在 Skyline 的最低点（最低 y 值）放置。

数据结构改进：Skyline 记录每个矩形的实际占用范围 (x, y, width, length)，
而非仅记录右边界，以确保不重叠约束严格满足。
"""

from typing import List, Dict, Tuple


def _rect_overlaps(x1, y1, w1, l1, x2, y2, w2, l2) -> bool:
    """两个矩形是否重叠（不包含相切）"""
    return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + l2 and y1 + l1 > y2


def find_best_position(placed_rects: List[Tuple], cargo_w: float, cargo_l: float,
                       vehicle_l: float, vehicle_w: float) -> Tuple[float, float]:
    """
    从已有矩形列表中找到最佳放置位置（Bottom-Left 策略）。

    候选点生成策略：
    - (0, 0) 始终为起点
    - 每个已有矩形的四个角点：(x, y), (x+w, y), (x, y+l), (x+w, y+l)
    - 所有候选点取交集保证不重叠

    Args:
        placed_rects: 已放置矩形列表 [(x, y, width, length), ...]
        cargo_w: 货物宽度（沿 x 轴）
        cargo_l: 货物长度（沿 y 轴）
        vehicle_l: 车辆长度（x 轴最大值）
        vehicle_w: 车辆宽度（y 轴最大值）

    Returns:
        (x, y) 最佳位置，找不到返回 (-1, -1)
    """
    # 收集候选点
    candidates = [(0, 0)]
    for (px, py, pw, pl) in placed_rects:
        candidates.append((px, py))
        candidates.append((px + pw, py))
        candidates.append((px, py + pl))
        candidates.append((px + pw, py + pl))

    # 去重
    candidates = list(set(candidates))

    best_x, best_y = -1, -1

    for cx, cy in candidates:
        # 边界检查
        if cx + cargo_w > vehicle_l or cy + cargo_l > vehicle_w:
            continue

        # 与所有已放置矩形检查重叠
        valid = True
        for (px, py, pw, pl) in placed_rects:
            if _rect_overlaps(cx, cy, cargo_w, cargo_l, px, py, pw, pl):
                valid = False
                break

        if not valid:
            continue

        # 选择最优：y 小优先（Bottom），x 小次之（Left）
        if best_y == -1 or cy < best_y or (cy == best_y and cx < best_x):
            best_x, best_y = cx, cy

    return (best_x, best_y)


def skyline_add_node(skyline: List[Tuple], x: float, y: float, width: float,
                     length: float) -> List[Tuple]:
    """
    向 Skyline 添加一个矩形节点。

    Skyline 节点格式: (x, y, width, length)
    表示一个实际占用的矩形区域。

    此函数为 append-only，合并逻辑在查找时处理。
    """
    skyline.append((x, y, width, length))
    return skyline


def can_place(cargo: Dict, vehicle: Dict, placed_rects: List[Tuple],
              x: float, y: float, rotated: bool = False) -> Tuple[bool, str]:
    """
    判断货物是否可以放入指定位置。

    Args:
        cargo: 货物 dict，包含 length, width, height, weight
        vehicle: 车辆 dict，包含 length, width, height, load_capacity
        placed_rects: 已放置矩形列表 [(x, y, width, length), ...]
        x, y: 放置起点
        rotated: 是否旋转 90°（length ↔ width）

    Returns:
        (can_place, reason)
    """
    cl = cargo['length']
    cw = cargo['width']
    ch = cargo.get('height', 0)

    if rotated:
        cl, cw = cw, cl

    vl = vehicle['length']
    vw = vehicle['width']
    vh = vehicle.get('height', 0)

    # 边界检查
    if x + cw > vl:
        return False, f'超出车辆长度边界: x+width={x + cw} > {vl}'
    if y + cl > vw:
        return False, f'超出车辆宽度边界: y+length={y + cl} > {vw}'

    # 高度检查
    if ch > vh:
        return False, f'货物高度{ch}mm > 车厢高度{vh}mm'

    # 重叠检查
    for (px, py, pw, pl) in placed_rects:
        if _rect_overlaps(x, y, cw, cl, px, py, pw, pl):
            return False, f'与已有货物重叠: ({x},{y},{cw},{cl}) vs ({px},{py},{pw},{pl})'

    return True, ''


def generate_loading_plan(cargo_list: List[Dict], vehicle: Dict) -> Dict:
    """
    生成二维装箱装车方案（Skyline + Bottom-Left 算法）。

    Args:
        cargo_list: 货物列表，每个 dict 包含:
            - cargo_id: 货物标识
            - length: 货物长度（mm）
            - width: 货物宽度（mm）
            - height: 货物高度（mm）
            - weight: 货物重量（kg）
        vehicle: 车辆 dict，包含:
            - length: 车厢长度（mm）
            - width: 车厢宽度（mm）
            - height: 车厢高度（mm）
            - load_capacity: 载重容量（kg）

    Returns:
        {
            'placed': [{'cargo_id', 'x', 'y', 'rotated', 'weight', 'length', 'width', 'height'}],
            'unplaced': [{'cargo_id', 'reason'}],
            'total_weight': float,
            'total_area': float,
            'vehicle_utilization': float,
            'vehicle_area': float,
            'used_area': float,
        }
    """
    if not cargo_list:
        return {
            'placed': [], 'unplaced': [], 'total_weight': 0, 'total_area': 0,
            'vehicle_utilization': 0, 'vehicle_area': 0, 'used_area': 0,
        }

    vl = vehicle['length']
    vw = vehicle['width']

    # 过滤无效货物 + 标记超尺寸货物
    valid_cargo = []
    oversized_cargo = []
    for c in cargo_list:
        cl = c.get('length', 0)
        cw = c.get('width', 0)
        if cl <= 0 or cw <= 0:
            continue
        if cl > vl and cw > vw:
            # 检查旋转是否可放
            if cw <= vl and cl <= vw:
                valid_cargo.append(c)
            else:
                oversized_cargo.append(c)
        else:
            valid_cargo.append(c)

    # 排序：底面面积降序（大件优先），面积相同按重量降序
    valid_cargo.sort(key=lambda c: (c['length'] * c['width'], c.get('weight', 0)), reverse=True)

    placed_rects: List[Tuple] = []  # (x, y, width, length)
    placed = []
    unplaced = []
    total_weight = 0
    total_area = 0

    # 将超尺寸货物加入 unplaced
    for c in oversized_cargo:
        cl = c['length']
        cw = c['width']
        unplaced.append({
            'cargo_id': c['cargo_id'],
            'reason': f'货物尺寸{cl}x{cw}mm 超出车辆 {vl}x{vw}mm（含旋转检查）',
        })

    for cargo in valid_cargo:
        cl = cargo['length']
        cw = cargo['width']
        ch = cargo.get('height', 0)
        cwt = cargo.get('weight', 0)

        # 重量检查
        capacity = vehicle.get('load_capacity', float('inf'))
        if total_weight + cwt > capacity:
            unplaced.append({
                'cargo_id': cargo['cargo_id'],
                'reason': f'超出载重限制: 当前{total_weight}kg + {cwt}kg > {capacity}kg',
            })
            continue

        # 高度检查
        if ch > vehicle.get('height', float('inf')):
            unplaced.append({
                'cargo_id': cargo['cargo_id'],
                'reason': f'货物高度{ch}mm > 车厢高度{vehicle.get("height", 0)}mm',
            })
            continue

        # 尝试正常放置
        x, y = find_best_position(placed_rects, cw, cl, vl, vw)
        if x >= 0 and y >= 0:
            placed_rects.append((x, y, cw, cl))
            placed.append({
                'cargo_id': cargo['cargo_id'],
                'x': x, 'y': y,
                'rotated': False,
                'weight': cwt,
                'length': cl, 'width': cw,
                'height': ch,
            })
            total_weight += cwt
            total_area += cl * cw
            continue

        # 尝试旋转 90°
        x, y = find_best_position(placed_rects, cl, cw, vl, vw)
        if x >= 0 and y >= 0:
            placed_rects.append((x, y, cl, cw))
            placed.append({
                'cargo_id': cargo['cargo_id'],
                'x': x, 'y': y,
                'rotated': True,
                'weight': cwt,
                'length': cw, 'width': cl,  # 旋转后实际占位
                'height': ch,
            })
            total_weight += cwt
            total_area += cl * cw
            continue

        # 无法放置
        unplaced.append({
            'cargo_id': cargo['cargo_id'],
            'reason': f'无可用位置: {cl}x{cw}mm 无法放入 {vl}x{vw}mm 车厢',
        })

    vehicle_area = vl * vw
    utilization = total_area / vehicle_area if vehicle_area > 0 else 0

    return {
        'placed': placed,
        'unplaced': unplaced,
        'total_weight': total_weight,
        'total_area': total_area,
        'vehicle_utilization': round(utilization, 4),
        'vehicle_area': vehicle_area,
        'used_area': total_area,
    }
