"""Settings Controller - handles application settings endpoints"""

import logging
from flask import Blueprint, request, current_app
from models import db, Settings
from utils import success_response, error_response, bad_request
from datetime import datetime, timezone
from config import Config

logger = logging.getLogger(__name__)

settings_bp = Blueprint(
    "settings", __name__, url_prefix="/api/settings"
)


# Prevent redirect issues when trailing slash is missing
@settings_bp.route("/", methods=["GET"], strict_slashes=False)
def get_settings():
    """
    GET /api/settings - Get application settings
    """
    try:
        settings = Settings.get_settings()
        return success_response(settings.to_dict())
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return error_response(
            "GET_SETTINGS_ERROR",
            f"Failed to get settings: {str(e)}",
            500,
        )


@settings_bp.route("/", methods=["PUT"], strict_slashes=False)
def update_settings():
    """
    PUT /api/settings - Update application settings

    Request Body:
        {
            "api_base_url": "https://api.example.com",
            "api_key": "your-api-key",
            "image_resolution": "2K",
            "image_aspect_ratio": "16:9"
        }
    """
    try:
        data = request.get_json()
        if not data:
            return bad_request("Request body is required")

        settings = Settings.get_settings()

        # Update AI provider format configuration
        if "ai_provider_format" in data:
            provider_format = data["ai_provider_format"]
            if provider_format not in ["openai", "gemini"]:
                return bad_request("AI provider format must be 'openai' or 'gemini'")
            settings.ai_provider_format = provider_format

        # Update API configuration
        if "api_base_url" in data:
            raw_base_url = data["api_base_url"]
            # Empty string from frontend means "clear override, fall back to env/default"
            if raw_base_url is None:
                settings.api_base_url = None
            else:
                value = str(raw_base_url).strip()
                settings.api_base_url = value if value != "" else None

        if "api_key" in data:
            settings.api_key = data["api_key"]

        # Update image generation configuration
        if "image_resolution" in data:
            resolution = data["image_resolution"]
            if resolution not in ["1K", "2K", "4K"]:
                return bad_request("Resolution must be 1K, 2K, or 4K")
            settings.image_resolution = resolution

        if "image_aspect_ratio" in data:
            aspect_ratio = data["image_aspect_ratio"]
            settings.image_aspect_ratio = aspect_ratio

        # Update worker configuration
        if "max_description_workers" in data:
            workers = int(data["max_description_workers"])
            if workers < 1 or workers > 20:
                return bad_request(
                    "Max description workers must be between 1 and 20"
                )
            settings.max_description_workers = workers

        if "max_image_workers" in data:
            workers = int(data["max_image_workers"])
            if workers < 1 or workers > 20:
                return bad_request(
                    "Max image workers must be between 1 and 20"
                )
            settings.max_image_workers = workers

        # Update model & MinerU configuration (optional, empty values fall back to Config)
        if "text_model" in data:
            settings.text_model = (data["text_model"] or "").strip() or None

        if "image_model" in data:
            settings.image_model = (data["image_model"] or "").strip() or None

        if "mineru_api_base" in data:
            settings.mineru_api_base = (data["mineru_api_base"] or "").strip() or None

        if "mineru_token" in data:
            settings.mineru_token = data["mineru_token"]

        if "image_caption_model" in data:
            settings.image_caption_model = (data["image_caption_model"] or "").strip() or None

        if "output_language" in data:
            language = data["output_language"]
            if language in ["zh", "en", "ja", "auto"]:
                settings.output_language = language
            else:
                return bad_request("Output language must be 'zh', 'en', 'ja', or 'auto'")

        settings.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Sync to app.config
        _sync_settings_to_config(settings)

        logger.info("Settings updated successfully")
        return success_response(
            settings.to_dict(), "Settings updated successfully"
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {str(e)}")
        return error_response(
            "UPDATE_SETTINGS_ERROR",
            f"Failed to update settings: {str(e)}",
            500,
        )


@settings_bp.route("/reset", methods=["POST"], strict_slashes=False)
def reset_settings():
    """
    POST /api/settings/reset - Reset settings to default values

    重置策略：将可配置项设为 None，使其回退到环境变量
    只保留 UI 必需的默认值（如分辨率、比例等）
    """
    try:
        settings = Settings.get_settings()

        # Reset to None to fall back to environment variables
        # 将可配置项重置为 None，使其回退到环境变量
        settings.ai_provider_format = None
        settings.api_base_url = None
        settings.api_key = None
        settings.text_model = None
        settings.image_model = None
        settings.mineru_api_base = None
        settings.mineru_token = None
        settings.image_caption_model = None

        # Keep UI-required defaults
        # 保留 UI 必需的默认值
        settings.output_language = 'zh'  # 重置为默认中文
        settings.image_resolution = Config.DEFAULT_RESOLUTION
        settings.image_aspect_ratio = Config.DEFAULT_ASPECT_RATIO
        settings.max_description_workers = Config.MAX_DESCRIPTION_WORKERS
        settings.max_image_workers = Config.MAX_IMAGE_WORKERS
        settings.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        # Sync to app.config (will use env vars for None values)
        _sync_settings_to_config(settings)

        logger.info("Settings reset to defaults (using environment variables)")
        return success_response(
            settings.to_dict(), "Settings reset to defaults"
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting settings: {str(e)}")
        return error_response(
            "RESET_SETTINGS_ERROR",
            f"Failed to reset settings: {str(e)}",
            500,
        )


def _sync_settings_to_config(settings: Settings):
    """
    Sync settings to Flask app config and clear AI service cache if needed

    优先级：数据库非 None/空值 > 环境变量（Config）> 代码默认值
    只有当数据库值不为 None 且不为空字符串时才覆盖 app.config
    """
    # Track if AI-related settings changed
    ai_config_changed = False

    # Sync AI provider format (只有数据库有值时才覆盖)
    if settings.ai_provider_format is not None and settings.ai_provider_format != '':
        old_format = current_app.config.get("AI_PROVIDER_FORMAT")
        if old_format != settings.ai_provider_format:
            ai_config_changed = True
            logger.info(f"AI provider format changed: {old_format} -> {settings.ai_provider_format}")
        current_app.config["AI_PROVIDER_FORMAT"] = settings.ai_provider_format
    else:
        # 数据库为 None/空，使用环境变量
        logger.info(f"AI_PROVIDER_FORMAT using env value: {current_app.config.get('AI_PROVIDER_FORMAT')}")

    # Sync API configuration (只有数据库有值时才覆盖)
    if settings.api_base_url is not None and settings.api_base_url != '':
        old_base = current_app.config.get("GOOGLE_API_BASE")
        if old_base != settings.api_base_url:
            ai_config_changed = True
            logger.info(f"API base URL changed: {old_base} -> {settings.api_base_url}")
        current_app.config["GOOGLE_API_BASE"] = settings.api_base_url
        current_app.config["OPENAI_API_BASE"] = settings.api_base_url
    else:
        # 数据库为 None/空，使用环境变量
        logger.info(f"API_BASE using env values: GOOGLE={current_app.config.get('GOOGLE_API_BASE')}, OPENAI={current_app.config.get('OPENAI_API_BASE')}")

    if settings.api_key is not None and settings.api_key != '':
        old_key = current_app.config.get("GOOGLE_API_KEY")
        # Only compare existence, not actual value for security
        if (old_key is None) != (settings.api_key is None):
            ai_config_changed = True
            logger.info("API key updated")
        current_app.config["GOOGLE_API_KEY"] = settings.api_key
        current_app.config["OPENAI_API_KEY"] = settings.api_key
    else:
        # 数据库为 None/空，使用环境变量
        has_google = bool(current_app.config.get("GOOGLE_API_KEY"))
        has_openai = bool(current_app.config.get("OPENAI_API_KEY"))
        logger.info(f"API keys using env values: GOOGLE={has_google}, OPENAI={has_openai}")

    # Check model changes (只有数据库有值时才覆盖)
    if settings.text_model is not None and settings.text_model != '':
        old_model = current_app.config.get("TEXT_MODEL")
        if old_model != settings.text_model:
            ai_config_changed = True
            logger.info(f"Text model changed: {old_model} -> {settings.text_model}")
        current_app.config["TEXT_MODEL"] = settings.text_model
    else:
        logger.info(f"TEXT_MODEL using env value: {current_app.config.get('TEXT_MODEL')}")

    if settings.image_model is not None and settings.image_model != '':
        old_model = current_app.config.get("IMAGE_MODEL")
        if old_model != settings.image_model:
            ai_config_changed = True
            logger.info(f"Image model changed: {old_model} -> {settings.image_model}")
        current_app.config["IMAGE_MODEL"] = settings.image_model
    else:
        logger.info(f"IMAGE_MODEL using env value: {current_app.config.get('IMAGE_MODEL')}")

    # Sync image generation settings (这些始终有默认值)
    current_app.config["DEFAULT_RESOLUTION"] = settings.image_resolution
    current_app.config["DEFAULT_ASPECT_RATIO"] = settings.image_aspect_ratio

    # Sync worker settings (这些始终有默认值)
    current_app.config["MAX_DESCRIPTION_WORKERS"] = settings.max_description_workers
    current_app.config["MAX_IMAGE_WORKERS"] = settings.max_image_workers
    logger.info(f"Updated worker settings: desc={settings.max_description_workers}, img={settings.max_image_workers}")

    # Sync MinerU settings (只有数据库有值时才覆盖)
    if settings.mineru_api_base is not None and settings.mineru_api_base != '':
        current_app.config["MINERU_API_BASE"] = settings.mineru_api_base
        logger.info(f"Updated MINERU_API_BASE to: {settings.mineru_api_base}")
    else:
        logger.info(f"MINERU_API_BASE using env value: {current_app.config.get('MINERU_API_BASE')}")

    if settings.mineru_token is not None and settings.mineru_token != '':
        current_app.config["MINERU_TOKEN"] = settings.mineru_token
        logger.info("Updated MINERU_TOKEN from settings")
    else:
        has_token = bool(current_app.config.get("MINERU_TOKEN"))
        logger.info(f"MINERU_TOKEN using env value: {has_token}")

    if settings.image_caption_model is not None and settings.image_caption_model != '':
        current_app.config["IMAGE_CAPTION_MODEL"] = settings.image_caption_model
        logger.info(f"Updated IMAGE_CAPTION_MODEL to: {settings.image_caption_model}")
    else:
        logger.info(f"IMAGE_CAPTION_MODEL using env value: {current_app.config.get('IMAGE_CAPTION_MODEL')}")

    if settings.output_language:  # 这个始终有默认值 'zh'
        current_app.config["OUTPUT_LANGUAGE"] = settings.output_language
        logger.info(f"Updated OUTPUT_LANGUAGE to: {settings.output_language}")

    # Clear AI service cache if AI-related configuration changed
    if ai_config_changed:
        try:
            from services.ai_service_manager import clear_ai_service_cache
            clear_ai_service_cache()
            logger.warning("AI configuration changed - AIService cache cleared. New providers will be created on next request.")
        except Exception as e:
            logger.error(f"Failed to clear AI service cache: {e}")
