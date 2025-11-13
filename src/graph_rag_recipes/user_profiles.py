"""内置用户画像样本，支撑 Project 4 的用户节点示例。"""

from __future__ import annotations

from typing import Iterable, Sequence

from .data_models import UserProfile


class UserProfileRepository:
    """提供用户节点及历史菜谱的读写接口。"""

    def __init__(self, profiles: Iterable[UserProfile] | None = None) -> None:
        sample_profiles = (
            list(profiles) if profiles is not None else self._default_profiles()
        )
        self._profiles = {profile.user_id: profile for profile in sample_profiles}

    def get(self, user_id: str) -> UserProfile | None:
        return self._profiles.get(user_id)

    def all(self) -> Sequence[UserProfile]:
        return tuple(self._profiles.values())

    @staticmethod
    def _default_profiles() -> list[UserProfile]:
        """使用示例菜谱 ID 构造几个典型用户。"""

        return [
            UserProfile(
                user_id="U123",
                liked_recipe_ids=(
                    "sample|home_style|tomato_scrambled_eggs",
                    "sample|sichuan|yuxiang_shredded_pork",
                ),
                preferred_tags=("酸甜", "家常热菜"),
            ),
            UserProfile(
                user_id="U207",
                liked_recipe_ids=("sample|cold|smashed_cucumber",),
                preferred_tags=("凉菜", "开胃"),
            ),
            UserProfile(
                user_id="U305",
                liked_recipe_ids=("sample|staple|mushroom_chicken_rice",),
                preferred_tags=("主食", "家常热菜"),
            ),
        ]


__all__ = ["UserProfileRepository"]
