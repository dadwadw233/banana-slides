"""
Simplified Flask Application Entry Point
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate

# Load environment variables from project root .env file
_project_root = Path(__file__).parent.parent
_env_file = _project_root / '.env'
load_dotenv(dotenv_path=_env_file, override=True)

from flask import Flask
from flask_cors import CORS
from models import db
from config import Config
from controllers.material_controller import material_bp, material_global_bp
from controllers.reference_file_controller import reference_file_bp
from controllers.settings_controller import settings_bp
from controllers import project_bp, page_bp, template_bp, user_template_bp, export_bp, file_bp


# Enable SQLite WAL mode for all connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Enable WAL mode and related PRAGMAs for each SQLite connection.
    Registered once at import time to avoid duplicate handlers when
    create_app() is called multiple times.
    """
    # Only apply to SQLite connections
    if not isinstance(dbapi_conn, sqlite3.Connection):
        return

    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds timeout
    finally:
        cursor.close()


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration from Config class
    app.config.from_object(Config)
    
    # Override with environment-specific paths (use absolute path)
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(backend_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    db_path = os.path.join(instance_dir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Ensure upload folder exists
    project_root = os.path.dirname(backend_dir)
    upload_folder = os.path.join(project_root, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # CORS configuration (parse from environment)
    raw_cors = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
    if raw_cors.strip() == '*':
        cors_origins = '*'
    else:
        cors_origins = [o.strip() for o in raw_cors.split(',') if o.strip()]
    app.config['CORS_ORIGINS'] = cors_origins
    
    # Initialize logging (log to stdout so Docker can capture it)
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    
    # 设置第三方库的日志级别，避免过多的DEBUG日志
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.INFO)  # Flask开发服务器日志保持INFO

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=cors_origins)
    # Database migrations (Alembic via Flask-Migrate)
    Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(project_bp)
    app.register_blueprint(page_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(user_template_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(material_global_bp)
    app.register_blueprint(reference_file_bp, url_prefix='/api/reference-files')
    app.register_blueprint(settings_bp)

    with app.app_context():
        # Load settings from database and sync to app.config
        _load_settings_to_config(app)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Banana Slides API is running'}
    
    # Output language endpoint
    @app.route('/api/output-language', methods=['GET'])
    def get_output_language():
        """
        获取用户的输出语言偏好（从数据库 Settings 读取）
        返回: zh, ja, en, auto
        """
        from models import Settings
        try:
            settings = Settings.get_settings()
            return {'data': {'language': settings.output_language}}
        except SQLAlchemyError as db_error:
            logging.warning(f"Failed to load output language from settings: {db_error}")
            return {'data': {'language': Config.OUTPUT_LANGUAGE}}  # 默认中文

    # Root endpoint
    @app.route('/')
    def index():
        return {
            'name': 'Banana Slides API',
            'version': '1.0.0',
            'description': 'AI-powered PPT generation service',
            'endpoints': {
                'health': '/health',
                'api_docs': '/api',
                'projects': '/api/projects'
            }
        }
    
    return app


def _load_settings_to_config(app):
    """
    Load settings on startup with priority: Environment Variables > Database > Code Defaults

    启动时配置优先级：环境变量 > 数据库 > 代码默认值
    - 如果环境变量有值，使用环境变量并**同步更新数据库**
    - 如果环境变量无值，使用数据库中的值
    - 这样确保数据库始终存储实际运行时的值，前后端保持一致
    - 数据库的api_base_url/api_key存储当前provider的配置
    """
    from models import Settings, db
    from config import Config
    try:
        settings = Settings.get_settings()
        db_updated = False  # 跟踪是否需要更新数据库

        # Load AI provider format (环境变量优先并同步到数据库)
        if Config.AI_PROVIDER_FORMAT:
            if settings.ai_provider_format != Config.AI_PROVIDER_FORMAT:
                settings.ai_provider_format = Config.AI_PROVIDER_FORMAT
                db_updated = True
            app.config['AI_PROVIDER_FORMAT'] = Config.AI_PROVIDER_FORMAT
            current_provider = Config.AI_PROVIDER_FORMAT
            logging.info(f"Using AI_PROVIDER_FORMAT from env: {Config.AI_PROVIDER_FORMAT}")
        elif settings.ai_provider_format:
            app.config['AI_PROVIDER_FORMAT'] = settings.ai_provider_format
            current_provider = settings.ai_provider_format
            logging.info(f"Using AI_PROVIDER_FORMAT from database: {settings.ai_provider_format}")
        else:
            current_provider = 'gemini'  # 默认值
            app.config['AI_PROVIDER_FORMAT'] = current_provider

        # 加载所有provider的环境变量到app.config（供ai_providers使用）
        # Google/Gemini API configuration
        if Config.GOOGLE_API_BASE:
            app.config['GOOGLE_API_BASE'] = Config.GOOGLE_API_BASE
        if Config.GOOGLE_API_KEY:
            app.config['GOOGLE_API_KEY'] = Config.GOOGLE_API_KEY

        # OpenAI API configuration
        if Config.OPENAI_API_BASE:
            app.config['OPENAI_API_BASE'] = Config.OPENAI_API_BASE
        if Config.OPENAI_API_KEY:
            app.config['OPENAI_API_KEY'] = Config.OPENAI_API_KEY

        # 根据当前provider，同步对应的环境变量到数据库的api_base_url/api_key
        if current_provider == 'gemini':
            # Google/Gemini provider
            if Config.GOOGLE_API_BASE:
                if settings.api_base_url != Config.GOOGLE_API_BASE:
                    settings.api_base_url = Config.GOOGLE_API_BASE
                    db_updated = True
                logging.info(f"Using GOOGLE_API_BASE from env: {Config.GOOGLE_API_BASE}")
            elif settings.api_base_url:
                logging.info(f"Using API_BASE_URL from database: {settings.api_base_url}")

            if Config.GOOGLE_API_KEY:
                if settings.api_key != Config.GOOGLE_API_KEY:
                    settings.api_key = Config.GOOGLE_API_KEY
                    db_updated = True
                logging.info("Using GOOGLE_API_KEY from env (value hidden)")
            elif settings.api_key:
                logging.info("Using API_KEY from database (value hidden)")
        else:
            # OpenAI provider
            if Config.OPENAI_API_BASE:
                if settings.api_base_url != Config.OPENAI_API_BASE:
                    settings.api_base_url = Config.OPENAI_API_BASE
                    db_updated = True
                logging.info(f"Using OPENAI_API_BASE from env: {Config.OPENAI_API_BASE}")
            elif settings.api_base_url:
                logging.info(f"Using API_BASE_URL from database: {settings.api_base_url}")

            if Config.OPENAI_API_KEY:
                if settings.api_key != Config.OPENAI_API_KEY:
                    settings.api_key = Config.OPENAI_API_KEY
                    db_updated = True
                logging.info("Using OPENAI_API_KEY from env (value hidden)")
            elif settings.api_key:
                logging.info("Using API_KEY from database (value hidden)")

        # Load model configuration (环境变量优先并同步到数据库)
        if Config.TEXT_MODEL:
            if settings.text_model != Config.TEXT_MODEL:
                settings.text_model = Config.TEXT_MODEL
                db_updated = True
            logging.info(f"Using TEXT_MODEL from env: {Config.TEXT_MODEL}")
        elif settings.text_model:
            app.config['TEXT_MODEL'] = settings.text_model
            logging.info(f"Using TEXT_MODEL from database: {settings.text_model}")

        if Config.IMAGE_MODEL:
            if settings.image_model != Config.IMAGE_MODEL:
                settings.image_model = Config.IMAGE_MODEL
                db_updated = True
            logging.info(f"Using IMAGE_MODEL from env: {Config.IMAGE_MODEL}")
        elif settings.image_model:
            app.config['IMAGE_MODEL'] = settings.image_model
            logging.info(f"Using IMAGE_MODEL from database: {settings.image_model}")

        # Load MinerU configuration (环境变量优先并同步到数据库)
        if Config.MINERU_API_BASE:
            if settings.mineru_api_base != Config.MINERU_API_BASE:
                settings.mineru_api_base = Config.MINERU_API_BASE
                db_updated = True
            logging.info(f"Using MINERU_API_BASE from env: {Config.MINERU_API_BASE}")
        elif settings.mineru_api_base:
            app.config['MINERU_API_BASE'] = settings.mineru_api_base
            logging.info(f"Using MINERU_API_BASE from database: {settings.mineru_api_base}")

        if Config.MINERU_TOKEN:
            if settings.mineru_token != Config.MINERU_TOKEN:
                settings.mineru_token = Config.MINERU_TOKEN
                db_updated = True
            logging.info("Using MINERU_TOKEN from env (value hidden)")
        elif settings.mineru_token:
            app.config['MINERU_TOKEN'] = settings.mineru_token
            logging.info("Using MINERU_TOKEN from database (value hidden)")

        if Config.IMAGE_CAPTION_MODEL:
            if settings.image_caption_model != Config.IMAGE_CAPTION_MODEL:
                settings.image_caption_model = Config.IMAGE_CAPTION_MODEL
                db_updated = True
            logging.info(f"Using IMAGE_CAPTION_MODEL from env: {Config.IMAGE_CAPTION_MODEL}")
        elif settings.image_caption_model:
            app.config['IMAGE_CAPTION_MODEL'] = settings.image_caption_model
            logging.info(f"Using IMAGE_CAPTION_MODEL from database: {settings.image_caption_model}")

        # 如果环境变量更新了数据库，提交更改
        if db_updated:
            db.session.commit()
            logging.info("Database settings updated from environment variables")

        # Load image generation settings (数据库优先，因为这些是UI配置)
        app.config['DEFAULT_RESOLUTION'] = settings.image_resolution
        app.config['DEFAULT_ASPECT_RATIO'] = settings.image_aspect_ratio
        logging.info(f"Using image settings from database: {settings.image_resolution}, {settings.image_aspect_ratio}")

        # Load worker settings (数据库优先，因为这些是UI配置)
        app.config['MAX_DESCRIPTION_WORKERS'] = settings.max_description_workers
        app.config['MAX_IMAGE_WORKERS'] = settings.max_image_workers
        logging.info(f"Using worker settings from database: desc={settings.max_description_workers}, img={settings.max_image_workers}")

        # Load output language (数据库优先，因为这是UI配置)
        app.config['OUTPUT_LANGUAGE'] = settings.output_language
        logging.info(f"Using output language from database: {settings.output_language}")

    except Exception as e:
        logging.warning(f"Could not load settings from database: {e}")


# Create app instance
app = create_app()


if __name__ == '__main__':
    # Run development server
    if os.getenv("IN_DOCKER", "0") == "1":
        port = 5000 # 在 docker 内部部署时始终使用 5000 端口.
    else:
        port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logging.info(
        "\n"
        "╔══════════════════════════════════════╗\n"
        "║   🍌 Banana Slides API Server 🍌   ║\n"
        "╚══════════════════════════════════════╝\n"
        f"Server starting on: http://localhost:{port}\n"
        f"Output Language: {Config.OUTPUT_LANGUAGE}\n"
        f"Environment: {os.getenv('FLASK_ENV', 'development')}\n"
        f"Debug mode: {debug}\n"
        f"API Base URL: http://localhost:{port}/api\n"
        f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}\n"
        f"Uploads: {app.config['UPLOAD_FOLDER']}"
    )
    
    # Using absolute paths for database, so WSL path issues should not occur
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
