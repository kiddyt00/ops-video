"""
Parameter preset CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.parameter_preset import ParameterPreset
from ..schemas.parameter_preset import PresetCreate, PresetUpdate


class PresetCRUD:
    """Parameter preset CRUD operations"""

    def create(self, db: Session, *, obj_in: PresetCreate, user_id: Optional[UUID] = None) -> ParameterPreset:
        """Create a new preset"""
        preset = ParameterPreset(
            name=obj_in.name,
            generator_type=obj_in.generator_type,
            description=obj_in.description,
            parameters=obj_in.parameters or {},
            user_id=user_id,
        )
        db.add(preset)
        db.commit()
        db.refresh(preset)
        return preset

    def get(self, db: Session, preset_id: UUID) -> Optional[ParameterPreset]:
        """Get preset by ID"""
        return db.query(ParameterPreset).filter(ParameterPreset.id == preset_id).first()

    def get_all(
        self, db: Session, *, user_id: Optional[UUID] = None,
        generator_type: Optional[str] = None
    ) -> List[ParameterPreset]:
        """Get all presets, optionally filtered by user and generator type"""
        query = db.query(ParameterPreset)
        if user_id is not None:
            query = query.filter(ParameterPreset.user_id == user_id)
        if generator_type is not None:
            query = query.filter(ParameterPreset.generator_type == generator_type)
        return query.all()

    def update(self, db: Session, *, preset_id: UUID, obj_in: PresetUpdate) -> Optional[ParameterPreset]:
        """Update preset"""
        preset = self.get(db, preset_id=preset_id)
        if not preset:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preset, field, value)

        db.add(preset)
        db.commit()
        db.refresh(preset)
        return preset

    def delete(self, db: Session, preset_id: UUID) -> bool:
        """Delete preset"""
        preset = self.get(db, preset_id=preset_id)
        if not preset:
            return False

        db.delete(preset)
        db.commit()
        return True


preset_crud = PresetCRUD()


# ─── System preset definitions ────────────────────────────────────────

SYSTEM_PRESETS = [
    {
        "name": "日系漫画标准",
        "generator_type": "script",
        "description": "日系漫画风格剧本模板",
        "parameters": {"style": "manga", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "日系漫画-图片",
        "generator_type": "image",
        "description": "日系赛璐璐画风",
        "parameters": {"style": "日系赛璐璐", "resolution": "512x768"},
        "is_system": True,
    },
    {
        "name": "日系漫画-音频",
        "generator_type": "tts",
        "description": "日系漫画配音模板",
        "parameters": {"voice": "zh-CN-XiaoxiaoNeural", "speed": "1.0", "bgm_style": "cheerful"},
        "is_system": True,
    },
    {
        "name": "日系漫画-视频",
        "generator_type": "video_composer",
        "description": "日系漫画视频合成模板",
        "parameters": {"fps": 24, "resolution": "720p", "transition": "fade"},
        "is_system": True,
    },
    {
        "name": "吉卜力风格-剧本",
        "generator_type": "script",
        "description": "吉卜力宫崎骏风格剧本",
        "parameters": {"style": "manga", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "吉卜力风格-图片",
        "generator_type": "image",
        "description": "吉卜力画风",
        "parameters": {"style": "吉卜力", "resolution": "1024x1024"},
        "is_system": True,
    },
    {
        "name": "吉卜力风格-音频",
        "generator_type": "tts",
        "description": "吉卜力风格温柔配音",
        "parameters": {"voice": "zh-CN-XiaoyiNeural", "speed": "0.9", "bgm_style": "ambient"},
        "is_system": True,
    },
    {
        "name": "赛博朋克-剧本",
        "generator_type": "script",
        "description": "赛博朋克现实风格剧本",
        "parameters": {"style": "realistic", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "赛博朋克-图片",
        "generator_type": "image",
        "description": "赛博朋克画风",
        "parameters": {"style": "赛博朋克", "resolution": "768x512"},
        "is_system": True,
    },
    {
        "name": "赛博朋克-音频",
        "generator_type": "tts",
        "description": "赛博朋克风格配音",
        "parameters": {"voice": "zh-CN-YunxiNeural", "speed": "1.1", "bgm_style": "dramatic"},
        "is_system": True,
    },
    {
        "name": "赛博朋克-视频",
        "generator_type": "video_composer",
        "description": "赛博朋克视频合成模板",
        "parameters": {"fps": 30, "resolution": "1080p", "transition": "slide"},
        "is_system": True,
    },
    {
        "name": "短视频快节奏-剧本",
        "generator_type": "script",
        "description": "快节奏短视频剧本",
        "parameters": {"style": "manga", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "短视频快节奏-图片",
        "generator_type": "image",
        "description": "Q版萌系画风",
        "parameters": {"style": "Q版萌系", "resolution": "512x768"},
        "is_system": True,
    },
    {
        "name": "短视频快节奏-音频",
        "generator_type": "tts",
        "description": "快节奏活泼配音",
        "parameters": {"voice": "zh-CN-YunxiNeural", "speed": "1.3", "bgm_style": "cheerful"},
        "is_system": True,
    },
    {
        "name": "短视频快节奏-视频",
        "generator_type": "video_composer",
        "description": "快节奏视频合成模板",
        "parameters": {"fps": 30, "resolution": "720p", "transition": "zoom"},
        "is_system": True,
    },
    {
        "name": "电影质感-剧本",
        "generator_type": "script",
        "description": "电影质感现实风格剧本",
        "parameters": {"style": "realistic", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "电影质感-图片",
        "generator_type": "image",
        "description": "厚涂电影风画风",
        "parameters": {"style": "厚涂电影风", "resolution": "1024x1024"},
        "is_system": True,
    },
    {
        "name": "电影质感-音频",
        "generator_type": "tts",
        "description": "电影质感沉稳配音",
        "parameters": {"voice": "zh-CN-YunjianNeural", "speed": "0.9", "bgm_style": "dramatic"},
        "is_system": True,
    },
    {
        "name": "电影质感-视频",
        "generator_type": "video_composer",
        "description": "电影质感视频合成模板",
        "parameters": {"fps": 24, "resolution": "1080p", "transition": "fade"},
        "is_system": True,
    },
    {
        "name": "国风水墨-剧本",
        "generator_type": "script",
        "description": "国风剧本模板",
        "parameters": {"style": "manga", "language": "zh"},
        "is_system": True,
    },
    {
        "name": "国风水墨-图片",
        "generator_type": "image",
        "description": "国风水墨画风",
        "parameters": {"style": "国风水墨", "resolution": "768x512"},
        "is_system": True,
    },
    {
        "name": "国风水墨-音频",
        "generator_type": "tts",
        "description": "国风古韵配音",
        "parameters": {"voice": "zh-CN-XiaoxiaoNeural", "speed": "1.0", "bgm_style": "ambient"},
        "is_system": True,
    },
    {
        "name": "国风水墨-视频",
        "generator_type": "video_composer",
        "description": "国风视频合成模板",
        "parameters": {"fps": 24, "resolution": "720p", "transition": "fade"},
        "is_system": True,
    },
]


def seed_system_presets(db: Session) -> int:
    """Seed built-in system presets. Returns count of newly seeded presets."""
    from ..models.parameter_preset import ParameterPreset

    existing = db.query(ParameterPreset).filter(
        ParameterPreset.is_system == True
    ).count()

    if existing > 0:
        return 0  # Already seeded

    count = 0
    for preset_data in SYSTEM_PRESETS:
        preset = ParameterPreset(
            name=preset_data["name"],
            generator_type=preset_data["generator_type"],
            description=preset_data["description"],
            parameters=preset_data["parameters"],
            is_system=preset_data["is_system"],
            user_id=None,
        )
        db.add(preset)
        count += 1

    db.commit()
    return count
