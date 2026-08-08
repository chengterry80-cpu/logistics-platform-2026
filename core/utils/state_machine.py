from django.db import models


class Transition:
    """
    通用状态机工具类。
    支持状态转换合法性检查、before/after 钩子调用、自动保存。
    """

    def __init__(self, transitions_dict):
        """
        Args:
            transitions_dict: dict, {源状态: [目标状态1, 目标状态2, ...]}
        """
        self.transitions = transitions_dict

    def can_transition(self, from_state, to_state):
        """
        判断是否可从 from_state 转换到 to_state。

        Args:
            from_state: 当前状态
            to_state: 目标状态

        Returns:
            bool: 是否允许转换
        """
        allowed = self.transitions.get(from_state, [])
        return to_state in allowed

    def transition(self, instance, to_state, user=None):
        """
        执行状态转换：
        1. 检查合法性
        2. 调用 before_<to_state> 钩子
        3. 更新状态字段
        4. 调用 after_<to_state> 钩子
        5. 保存实例

        Args:
            instance: Django Model 实例
            to_state: 目标状态值
            user: 操作人（可选，传递给钩子）

        Raises:
            ValueError: 非法转换时抛出
        """
        state_field = instance.get_state_field()
        from_state = getattr(instance, state_field)

        if not self.can_transition(from_state, to_state):
            raise ValueError(
                f"非法状态转换: [{from_state}] -> [{to_state}]"
                f"（允许的目标状态: {self.transitions.get(from_state, [])}）"
            )

        before_hook = getattr(instance, f'before_{to_state}', None)
        if callable(before_hook):
            before_hook(user=user)

        setattr(instance, state_field, to_state)

        after_hook = getattr(instance, f'after_{to_state}', None)
        if callable(after_hook):
            after_hook(user=user)

        instance.save()
