"""Settings model"""
from datetime import datetime, timezone
from . import db


class Settings(db.Model):
    """
    Settings model - stores global application settings
    """
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True, default=1)
    ai_provider_format = db.Column(db.String(20), nullable=False, default='gemini')  # AI提供商格式: openai, gemini
    api_base_url = db.Column(db.String(500), nullable=True)  # API基础URL
    api_key = db.Column(db.String(500), nullable=True)  # API密钥
    image_resolution = db.Column(db.String(20), nullable=False, default='2K')  # 图像清晰度: 1K, 2K, 4K
    image_aspect_ratio = db.Column(db.String(10), nullable=False, default='16:9')  # 图像比例: 16:9, 4:3, 1:1
    max_description_workers = db.Column(db.Integer, nullable=False, default=5)  # 描述生成最大工作线程数
    max_image_workers = db.Column(db.Integer, nullable=False, default=8)  # 图像生成最大工作线程数

    # 新增：大模型与 MinerU 相关可视化配置（可在设置页中编辑）
    text_model = db.Column(db.String(100), nullable=True)  # 文本大模型名称（覆盖 Config.TEXT_MODEL）
    image_model = db.Column(db.String(100), nullable=True)  # 图片大模型名称（覆盖 Config.IMAGE_MODEL）
    mineru_api_base = db.Column(db.String(255), nullable=True)  # MinerU 服务地址（覆盖 Config.MINERU_API_BASE）
    mineru_token = db.Column(db.String(500), nullable=True)  # MinerU API Token（覆盖 Config.MINERU_TOKEN）
    image_caption_model = db.Column(db.String(100), nullable=True)  # 图片识别模型（覆盖 Config.IMAGE_CAPTION_MODEL）
    output_language = db.Column(db.String(10), nullable=False, default='zh')  # 输出语言偏好（zh, en, ja, auto）
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """
        Convert to dictionary with actual runtime values

        返回实际运行时使用的值（环境变量 > 数据库 > 默认值）
        直接从 app.config 读取，因为启动时已经按正确的优先级加载好了
        """
        # 尝试从 Flask app.config 读取实际运行时的值（已按环境变量 > 数据库优先级加载）
        try:
            from flask import current_app
            has_app_context = True
        except (ImportError, RuntimeError):
            has_app_context = False

        if has_app_context:
            # 从 app.config 读取实际运行时使用的值
            actual_provider_format = current_app.config.get('AI_PROVIDER_FORMAT', 'gemini')
            actual_text_model = current_app.config.get('TEXT_MODEL', 'gemini-3-flash-preview')
            actual_image_model = current_app.config.get('IMAGE_MODEL', 'gemini-3-pro-image-preview')
            actual_mineru_api_base = current_app.config.get('MINERU_API_BASE', 'https://mineru.net')
            actual_mineru_token = current_app.config.get('MINERU_TOKEN', '')
            actual_image_caption_model = current_app.config.get('IMAGE_CAPTION_MODEL', 'gemini-3-flash-preview')

            # API Base 和 Key 根据 provider format 选择
            if actual_provider_format == 'openai':
                actual_api_base = current_app.config.get('OPENAI_API_BASE', '')
                actual_api_key = current_app.config.get('OPENAI_API_KEY', '')
            else:
                actual_api_base = current_app.config.get('GOOGLE_API_BASE', '')
                actual_api_key = current_app.config.get('GOOGLE_API_KEY', '')
        else:
            # 没有 app context（比如在测试中），回退到 Config
            from config import Config
            actual_provider_format = Config.AI_PROVIDER_FORMAT if Config.AI_PROVIDER_FORMAT else self.ai_provider_format
            actual_text_model = Config.TEXT_MODEL if Config.TEXT_MODEL else self.text_model
            actual_image_model = Config.IMAGE_MODEL if Config.IMAGE_MODEL else self.image_model
            actual_mineru_api_base = Config.MINERU_API_BASE if Config.MINERU_API_BASE else self.mineru_api_base
            actual_mineru_token = Config.MINERU_TOKEN if Config.MINERU_TOKEN else self.mineru_token
            actual_image_caption_model = Config.IMAGE_CAPTION_MODEL if Config.IMAGE_CAPTION_MODEL else self.image_caption_model

            if actual_provider_format == 'openai':
                actual_api_base = Config.OPENAI_API_BASE if Config.OPENAI_API_BASE else self.api_base_url
                actual_api_key = Config.OPENAI_API_KEY if Config.OPENAI_API_KEY else self.api_key
            else:
                actual_api_base = Config.GOOGLE_API_BASE if Config.GOOGLE_API_BASE else self.api_base_url
                actual_api_key = Config.GOOGLE_API_KEY if Config.GOOGLE_API_KEY else self.api_key

        return {
            'id': self.id,
            'ai_provider_format': actual_provider_format,
            'api_base_url': actual_api_base,
            'api_key_length': len(actual_api_key) if actual_api_key else 0,
            'image_resolution': self.image_resolution,
            'image_aspect_ratio': self.image_aspect_ratio,
            'max_description_workers': self.max_description_workers,
            'max_image_workers': self.max_image_workers,
            'text_model': actual_text_model,
            'image_model': actual_image_model,
            'mineru_api_base': actual_mineru_api_base,
            'mineru_token_length': len(actual_mineru_token) if actual_mineru_token else 0,
            'image_caption_model': actual_image_caption_model,
            'output_language': self.output_language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_settings():
        """
        Get or create the single settings instance.

        - 首次创建时，将可配置项初始化为 None，使其回退到环境变量
        - 只有必须有默认值的字段（如 image_resolution）才设置默认值
        - 运行时优先级：数据库非 None 值 > 环境变量 > 代码默认值
        """
        settings = Settings.query.first()
        if not settings:
            # 延迟导入，避免循环依赖
            from config import Config

            # 创建初始设置，大部分字段为 None，使其回退到环境变量
            # 只有 UI 必需的字段（如分辨率、比例）设置默认值
            settings = Settings(
                ai_provider_format=None,  # None = 使用环境变量
                api_base_url=None,  # None = 使用环境变量
                api_key=None,  # None = 使用环境变量
                image_resolution=Config.DEFAULT_RESOLUTION,  # UI 必需默认值
                image_aspect_ratio=Config.DEFAULT_ASPECT_RATIO,  # UI 必需默认值
                max_description_workers=Config.MAX_DESCRIPTION_WORKERS,  # UI 必需默认值
                max_image_workers=Config.MAX_IMAGE_WORKERS,  # UI 必需默认值
                text_model=None,  # None = 使用环境变量
                image_model=None,  # None = 使用环境变量
                mineru_api_base=None,  # None = 使用环境变量
                mineru_token=None,  # None = 使用环境变量
                image_caption_model=None,  # None = 使用环境变量
                output_language='zh',  # 默认中文
            )
            settings.id = 1
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f'<Settings id={self.id}>'
