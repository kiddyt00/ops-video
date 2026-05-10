"""AI Model CRUD operations"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.ai_model import AIModel
from ..schemas.ai_model import AIModelCreate, AIModelUpdate


class AIModelCRUD:
    def get(self, db: Session, model_id: UUID) -> Optional[AIModel]:
        return db.query(AIModel).filter(AIModel.id == model_id).first()

    def get_all(self, db: Session, category: Optional[str] = None) -> List[AIModel]:
        q = db.query(AIModel)
        if category:
            q = q.filter(AIModel.category == category)
        return q.order_by(AIModel.category, AIModel.created_at).all()

    def create(self, db: Session, obj_in: AIModelCreate) -> AIModel:
        model = AIModel(**obj_in.model_dump())
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def update(self, db: Session, model_id: UUID, obj_in: AIModelUpdate) -> Optional[AIModel]:
        model = self.get(db, model_id)
        if not model:
            return None
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        db.commit()
        db.refresh(model)
        return model

    def delete(self, db: Session, model_id: UUID) -> bool:
        model = self.get(db, model_id)
        if not model or model.is_builtin:
            return False
        db.delete(model)
        db.commit()
        return True

    def toggle(self, db: Session, model_id: UUID) -> Optional[AIModel]:
        model = self.get(db, model_id)
        if not model:
            return None
        model.is_enabled = not model.is_enabled
        db.commit()
        db.refresh(model)
        return model

    def seed_builtins(self, db: Session) -> int:
        """Seed built-in models if they don't exist. Returns count of seeded models."""
        existing = {m.name for m in self.get_all(db)}
        builtins = [
            AIModelCreate(name="通义千问 (Qwen-Plus)", category="llm", provider="dashscope",
                         model_name="qwen-plus", api_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                         is_builtin=True, is_enabled=False),
            AIModelCreate(name="通义万相 (Wan2.6)", category="text2img", provider="dashscope",
                         model_name="wan2.6-t2i", api_base_url="https://dashscope.aliyuncs.com/api/v1",
                         is_builtin=True, is_enabled=False),
            AIModelCreate(name="Edge TTS (Xiaoxiao)", category="tts", provider="edge_tts",
                         model_name="zh-CN-XiaoxiaoNeural", is_builtin=True, is_enabled=True),
            AIModelCreate(name="BGM 合成引擎", category="bgm", provider="scipy",
                         model_name="scipy-synth", is_builtin=True, is_enabled=True),
            AIModelCreate(name="FFmpeg 视频合成", category="video", provider="ffmpeg",
                         model_name="H.264/AAC", is_builtin=True, is_enabled=True),
        ]
        count = 0
        for b in builtins:
            if b.name not in existing:
                self.create(db, b)
                count += 1
        return count


ai_model_crud = AIModelCRUD()
