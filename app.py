#!/usr/bin/env python3
"""
Flask front-end for the VideoWithVoiceover engine
=================================================
Mirrors the original five-tab desktop GUI and serves the media files
so the browser can preview them.
"""
# Standard library imports
import base64
import io
import json
import logging
import mimetypes
import os
import pickle
import re
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timezone, timezone
from pathlib import Path
from threading import Thread
from flask_limiter import Limiter
# Flask imports
from flask import (
    Flask, Request, Response, abort, flash, jsonify, redirect,
    render_template, request, send_file, send_from_directory,
    session, url_for
)
from flask.cli import with_appcontext
import click
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user
)

# Third-party imports
import stripe
from google_auth_oauthlib.flow import Flow
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Local/project imports
import engine
from forms import LoginForm
from models import FREE_TIER_LIMIT, Project, User, db
from payments import payments
from utils.alternative_services import AlternativeServices
from utils.monitoring import api_monitor
from utils.openai_wrapper import fallback_handler
# … your existing imports …
import threading
from typing import Optional, Tuple
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address




# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
ONE_TIME_PRICE_ID = os.getenv("STRIPE_ONE_TIME_PRICE_ID")
SUBSCRIPTION_PRICE_ID = os.getenv("STRIPE_SUBSCRIPTION_PRICE_ID")
FREE_TIER_LIMIT = 3
PREMIUM_TIER_LIMIT = 50  # or however many projects you want

CLIENT_SECRETS_FILE = Path("workspace/client_secrets.json")
YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def get_media_duration(file_path):
    """Get duration of media file using ffprobe with proper image handling"""

    # First check if it's an image file by extension
    ext = os.path.splitext(file_path)[1].lower()
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg']

    if ext in image_extensions:
        return 5.0  # Always return 5 seconds for images

    # Also check by mime type in case extension is missing or unusual
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image'):
        return 5.0  # Images always get 5 seconds

    # Try using ffprobe for video/audio files
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            # Ensure minimum duration of 1 second for video/audio
            return max(1.0, round(duration, 2))
    except Exception as e:
        pass

    # Additional fallback: check file content if extension/mimetype failed
    try:
        # Try to open as image using PIL if available
        from PIL import Image
        with Image.open(file_path) as img:
            # If we can open it as an image, return 5 seconds
            return 5.0
    except:
        pass

    # Fallback for video/audio based on mime type
    if mime_type:
        if mime_type.startswith('video'):
            # If ffprobe failed, estimate based on file size
            try:
                file_size = os.path.getsize(file_path)
                estimated_duration = max(5.0, min(60.0, file_size / (1024 * 1024) * 8))
                return round(estimated_duration, 1)
            except:
                return 30.0
        elif mime_type.startswith('audio'):
            # Estimate for audio files
            try:
                file_size = os.path.getsize(file_path)
                estimated_duration = max(10.0, min(300.0, file_size / (1024 * 1024) * 60))
                return round(estimated_duration, 1)
            except:
                return 30.0

    # Default fallback
    return 30.0


def format_time_duration(seconds):
    """Format time duration as MM:SS"""
    if not seconds and seconds != 0:
        return '--:--'
    total_seconds = int(round(seconds))
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def user_token_path(user_id):
    """Get the path for user's YouTube token file"""
    return f"workspace/youtube_token_{user_id}.pkl"


# Ensure you have a SECRET_KEY set for sessions & CSRF
# ─────────────────── Flask basic setup ──────────────────────────────────

app = Flask(__name__)

app.jinja_env.globals['now'] = lambda: datetime.now(timezone.utc)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev‐fallback‐only')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)

# Register blueprints AFTER app is created
try:
    from payments import payments as payments_bp
    app.register_blueprint(payments_bp, url_prefix='/payments')
except ImportError:
    print("Warning: payments module not found, skipping blueprint registration")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

# Register blueprints
# app.register_blueprint(payments)

alternative_services = AlternativeServices()
#----------------------------------------------

# Jinja helper used by clips.html
def format_time(value):
    try:
        if value is None or value == '':
            return '0:00'

        # Handle Jinja Undefined safely
        try:
            from jinja2.runtime import Undefined
            if isinstance(value, Undefined):
                return '0:00'
        except Exception:
            pass

        # Use the existing format_time_duration function
        return format_time_duration(float(value))

    except Exception as e:
        app.logger.debug(f"format_time error: {e} for value: {value}")
        return '0:00'

# Make available in templates (call style and filter style)
app.jinja_env.globals['format_time'] = format_time
app.jinja_env.filters['format_time'] = format_time



@app.route('/projects')
@login_required
def projects():
    """List all projects for the current user"""
    user_projects = Project.query.filter_by(
        user_id=current_user.id
    ).order_by(Project.created_at.desc()).all()

    return render_template('projects.html', projects=user_projects)

@app.before_request
def ensure_user_id():
    session.permanent = True
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())


app.config.update(
    UPLOAD_FOLDER=os.path.abspath('uploads'),
    ENABLE_OPENAI_FALLBACKS=True,
    MAX_OPENAI_RETRIES=3,
    FALLBACK_CACHE_DURATION=3600,
    FALLBACK_AUDIO_PATH='static/audio/fallbacks/',
    FALLBACK_IMAGE_PATH='static/images/fallbacks/'
)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['FALLBACK_AUDIO_PATH'], exist_ok=True)
os.makedirs(app.config['FALLBACK_IMAGE_PATH'], exist_ok=True)
app.config['PREFERRED_URL_SCHEME'] = 'https'

log = app.logger
log.setLevel(logging.INFO)


# Helper functions to get workspace paths
def get_workspace_dir(user_id, project_id):
    """Get the workspace directory for a specific user and project"""
    return Path(f"workspace_u{user_id}_p{project_id}")

def allowed_video_mime(file):
    """Validate video file by MIME type"""
    import magic
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset file pointer
    return mime.startswith('video/')

def get_workspace_paths(user_id, project_id):
    """Get all workspace paths for a specific user and project"""
    workspace_dir = get_workspace_dir(user_id, project_id)
    return {
        'workspace': workspace_dir,
        'final': workspace_dir / "final",
        'title': workspace_dir / "title.txt",
        'script': workspace_dir / "script.txt",
        'keywords': workspace_dir / "keywords.txt",
        'clips': workspace_dir / "clips.json",
        'status': workspace_dir / "status.txt",
        'media': workspace_dir / "media",
        'music': workspace_dir / "music",
        'manifest': workspace_dir / "manifest.json"
    }


# Create a function to ensure workspace exists
def ensure_workspace_exists(user_id, project_id):
    """Ensure all workspace directories exist for a user/project"""
    paths = get_workspace_paths(user_id, project_id)

    # Create main workspace directory
    paths['workspace'].mkdir(parents=True, exist_ok=True)

    # Create subdirectories - only create if they exist in paths
    directories_to_create = ['assets', 'media', 'output', 'final']

    for dir_name in directories_to_create:
        if dir_name in paths:
            dir_path = paths[dir_name]
            if isinstance(dir_path, Path) and not dir_path.suffix:  # It's a directory, not a file
                dir_path.mkdir(parents=True, exist_ok=True)

    # Handle 'music' directory if it's needed (add to get_workspace_paths if required)
    music_dir = paths['workspace'] / 'music'
    music_dir.mkdir(parents=True, exist_ok=True)

    return paths


def _load_manifest(user_id, project_id):
    """Load manifest for specific user and project"""
    if hasattr(engine, '_load_manifest'):
        return engine._load_manifest(user_id=user_id, project_id=project_id)

    paths = get_workspace_paths(user_id, project_id)
    manifest_file = paths['manifest']
    return json.loads(manifest_file.read_text()) if manifest_file.exists() else {}


@app.template_filter('strftime')
def _jinja2_filter_datetime(value, fmt='%Y-%m-%dT%H:%M'):
    return value.strftime(fmt) if isinstance(value, datetime.datetime) else value


@app.context_processor
def inject_now():
    return dict(now=lambda: datetime.now(timezone.utc))


def _flash(ok: bool, msg: str):
    flash(msg, 'success' if ok else 'danger')


@app.route('/uploads/<int:user_id>/<int:project_id>/<path:filename>')
@login_required
def uploaded_file(user_id, project_id, filename):
    """Serve uploaded files from user/project specific workspace"""
    # Security check - ensure user can only access their own files
    if user_id != current_user.id:
        abort(403)

    # Verify user owns the project
    project = Project.query.get(project_id)
    if not project or project.user_id != current_user.id:
        abort(404)

    # Construct the workspace path
    workspace_dir = f"workspace_u{user_id}_p{project_id}"

    # Determine which subdirectory based on filename
    if filename.startswith('media/'):
        file_path = Path(workspace_dir) / filename
    elif filename.startswith('music/'):
        file_path = Path(workspace_dir) / filename
    elif filename.startswith('final/'):
        file_path = Path(workspace_dir) / filename
    else:
        file_path = Path(workspace_dir) / filename

    if not file_path.is_file():
        abort(404)

    # Serve the file
    return send_from_directory(file_path.parent, file_path.name, as_attachment=False)


# Add a helper route for backward compatibility or simpler access
@app.route('/workspace/<path:filename>')
@login_required
def serve_workspace_file(filename):
    """Serve files from the workspace directory."""
    workspace_root = Path("/home/myapp/apps/VideoWithVoiceover/workspace")
    file_path = workspace_root / filename

    # Security check - ensure the path is within workspace
    try:
        file_path.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        abort(404)

    if not file_path.exists():
        print(f"[serve_workspace_file] File not found: {file_path}")
        abort(404)

    print(f"[serve_workspace_file] Serving: {file_path}")
    return send_file(str(file_path))


@app.route('/final_video')
@login_required
def final_video():
    """Final video page"""
    project_id = request.args.get('project_id')

    if project_id:
        # Specific project requested
        project = Project.query.get(project_id)
        if not project or project.user_id != current_user.id:
            flash('Project not found', 'error')
            return redirect(url_for('index'))
    else:
        # Get the most recent project
        project = Project.query.filter_by(
            user_id=current_user.id
        ).order_by(Project.created_at.desc()).first()

        if not project:
            flash('No projects found', 'warning')
            return redirect(url_for('index'))

        # Redirect to include project_id in URL
        return redirect(url_for('final_video', project_id=project.id))

    # Get workspace path using the helper function
    workspace_path = get_workspace_paths(current_user.id, project.id)

    # Check for existing final video (checking multiple formats)
    final_video_path = None
    video_url = None

    # First check in the root workspace directory (as per second function)
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        path = os.path.join(workspace_path, f"final_video{ext}")
        if os.path.exists(path):
            final_video_path = f"final_video{ext}"
            video_url = url_for('serve_final_video',
                                user_id=current_user.id,
                                project_id=project.id)
            break

    # If not found, check in final subdirectory (as per first function)
    if not final_video_path:
        final_dir = Path(workspace_path) / "final"
        if final_dir.exists():
            for video_file in final_dir.glob("*.mp4"):
                if video_file.stat().st_size > 1024:
                    final_video_path = f"final/{video_file.name}"
                    video_url = url_for('uploaded_file',
                                        user_id=current_user.id,
                                        project_id=project.id,
                                        filename=final_video_path)
                    break

    # Get available clips
    clips_dir = os.path.join(workspace_path, "clips")
    clips = []
    if os.path.exists(clips_dir):
        for filename in sorted(os.listdir(clips_dir)):
            if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                clips.append(filename)

    # Get script content if available
    script_content = None
    script_path = os.path.join(workspace_path, "script.txt")
    if os.path.exists(script_path):
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
        except Exception as e:
            print(f"Error reading script: {e}")

    return render_template('final_video.html',
                           project=project,
                           video_path=video_url,  # URL for serving the video
                           final_video=final_video_path,  # Filename for display
                           clips=clips,
                           script_content=script_content)


# ========================================================================
# AUTH: signup / login / logout
# ========================================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))
        user = User(email=email, password_hash=generate_password_hash(password), projects_limit=FREE_TIER_LIMIT)
        db.session.add(user);
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('signup.html')


from forms import LoginForm


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # instantiate the form
    # on POST, validate data + CSRF
    if form.validate_on_submit():
        # lookup user
        user = User.query.filter_by(email=form.email.data).first()
        # check password
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            # redirect to next or default page
            next_page = request.args.get('next') or url_for('script')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'error')
    # on GET or on failed validation, re‐render form (with errors + CSRF)
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ========================================================================
# 1) MAIN TAB  "/"
# ========================================================================
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=True)
        app.logger.info(f"Main tab form data: {form_data}")

        video_title = form_data.get('video_title', '').strip()
        if not video_title:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Please enter a video title'}), 400
            flash("Please enter a video title", "error")
            return redirect(url_for('index'))

        # ✅ Check if there’s already an active project in session
        project_id = session.get('project_id')
        if project_id:
            project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
            if project:
                app.logger.info(f"Reusing existing project {project.id}")
            else:
                session.pop('project_id', None)
                project = None
        else:
            project = None

        # ✅ Create new project only if none exists
        if not project:
            project = Project(user_id=current_user.id, title=video_title, status='draft')
            db.session.add(project)
            db.session.commit()
            session['project_id'] = project.id
            app.logger.info(f"Created new project {project.id}")

        # ✅ Update title if changed
        if project.title != video_title:
            project.title = video_title
            db.session.commit()

        # ✅ Generate keywords if none provided
        if not form_data.get('keywords', '').strip():
            try:
                keywords_list = engine.suggest_keywords(video_title)
                if keywords_list:
                    form_data['keywords'] = ', '.join(keywords_list[:5])
                else:
                    genre = form_data.get('genre', 'general')
                    form_data['keywords'] = f"{video_title}, {genre} video, tutorial, guide, tips"
            except Exception as e:
                app.logger.error(f"Error generating keywords: {e}")
                form_data['keywords'] = f"{video_title}, video, content"

        # ✅ Save main tab info
        ok, msg = engine.save_main_tab(form_data, user_id=current_user.id, project_id=project.id)

        if ok:
            # Load generated script if available
            paths = get_workspace_paths(current_user.id, project.id)
            if paths['script'].exists():
                try:
                    script_content = paths['script'].read_text().strip()
                    project.script = script_content
                    db.session.commit()
                    app.logger.info(f"Saved generated script for project {project.id}")
                except Exception as e:
                    app.logger.error(f"Error reading generated script: {e}")

            # Return JSON for AJAX or redirect to script
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'project_id': project.id})

            flash("Script generated successfully!", "success")
            return redirect(url_for('script', project_id=project.id))
        else:
            db.session.delete(project)
            db.session.commit()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': msg}), 400

            flash(msg, "error")
            return redirect(url_for('index'))

    # GET
    return render_template(
        'index.html',
        languages=engine.language_options,
        voices=engine.get_voice_list()
    )


# ---------- helper APIs --------------------------------------------------
@app.get('/api/voices')
def api_voices():
    return jsonify(engine.get_voice_list())


@app.post('/api/test_voice')
def api_test_voice():
    try:
        voice = request.json['voice']
        # Since the generate_voice_test function is missing, let's create a simple implementation
        # This is a temporary fix until the function is added to engine.py
        if hasattr(engine, 'generate_voice_test'):
            data = engine.generate_voice_test(voice)
        else:
            # Temporary implementation - empty MP3 file
            app.logger.warning("Using temporary voice test implementation")
            # Create an empty MP3 file - this is just a placeholder
            data = b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

        if not data:  # Check if we got empty data
            return jsonify({"error": "Failed to generate voice test"}), 500

        return send_file(io.BytesIO(data),
                         download_name='test.mp3',
                         mimetype='audio/mpeg')
    except Exception as e:
        app.logger.exception("Voice test generation failed")
        return jsonify({"error": str(e)}), 500


@app.post('/api/keywords')
def api_keywords():
    prompt = request.json.get('prompt', '')
    title = request.json.get('title', '')
    return jsonify(engine.suggest_keywords(title, prompt))  # list[str]


@app.route('/authorize_youtube')
def authorize_youtube():
    flow = Flow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=YOUTUBE_SCOPES,
        redirect_uri=os.getenv('YOUTUBE_REDIRECT_URI', 'https://ai-videocreator.com/oauth2callback')
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(auth_url)


@app.route('/oauth2callback')
def oauth2callback():
    user_id = session.get('user_id')
    print(f"OAUTH2CALLBACK: ENTERED. user_id={user_id}")
    try:
        print("OAUTH2CALLBACK: About to create Flow.")
        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE),
            scopes=YOUTUBE_SCOPES,
            state=session.get('state'),
            redirect_uri=os.getenv('YOUTUBE_REDIRECT_URI', 'https://ai-videocreator.com/oauth2callback')
        )
        print("OAUTH2CALLBACK: About to fetch token from request.url =", request.url)
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        print("OAUTH2CALLBACK: Creds obtained, about to save pickle.")
        with open(user_token_path(user_id), "wb") as tokenfile:
            pickle.dump(creds, tokenfile)
            print(f"OAUTH2CALLBACK: Token written to {user_token_path(user_id)}")
        flash("YouTube authentication successful!", "success")
        return redirect(url_for('final_video'))
    except Exception as e:
        print("OAUTH2CALLBACK: EXCEPTION:", e)
        import traceback;
        traceback.print_exc()
        return f"<pre>OAuth callback failed: {e}\n\n{traceback.format_exc()}</pre>", 400


# ========================================================================
# 2) SCRIPT TAB  "/script" - UPDATED WITH USER/PROJECT WORKSPACE
# ========================================================================

def clear_old_media(user_id=None, project_id=None):
    """Clear old media files to free up disk space"""
    try:
        import shutil
        import os
        import time

        current_time = time.time()

        # If specific user/project provided, clean only that workspace
        if user_id and project_id:
            workspace_dir = f"workspace_u{user_id}_p{project_id}"
            if os.path.exists(workspace_dir):
                for root, dirs, files in os.walk(workspace_dir):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        # Check if file is older than 1 hour
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > 3600:  # 1 hour
                            try:
                                os.remove(filepath)
                                app.logger.info(f"Removed old media file: {filepath}")
                            except:
                                pass
        else:
            # Clean all old workspace directories
            for dirname in os.listdir('.'):
                if dirname.startswith('workspace_u'):
                    dir_path = os.path.join('.', dirname)
                    if os.path.isdir(dir_path):
                        # Check directory age
                        dir_age = current_time - os.path.getmtime(dir_path)
                        if dir_age > 86400:  # 24 hours
                            try:
                                shutil.rmtree(dir_path)
                                app.logger.info(f"Removed old workspace: {dir_path}")
                            except:
                                pass

        app.logger.info("Old media cleanup completed")

    except Exception as e:
        app.logger.warning(f"Media cleanup failed: {str(e)}")


# ============================
# /script route (FIXED)
# ============================
@app.route('/script', methods=['GET', 'POST'])
@login_required
def script():
    project_id = request.args.get('project_id') or session.get('project_id')
    if not project_id:
        flash("No project selected", "error")
        return redirect(url_for('index'))

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        session.pop('project_id', None)
        flash("Project not found", "error")
        return redirect(url_for('index'))

    paths = get_workspace_paths(current_user.id, project.id)

    # --- Define async_generate_clips here so it's available ---
    def async_generate_clips(project_id, user_id):
        from engine import download_media_for_query, _search_jamendo_music, _save_manifest, _download_all
        import asyncio, shutil, re, os
        from pathlib import Path

        def safe_filename(source, prefix=""):
            if isinstance(source, Path):
                name = source.name
            else:
                name = os.path.basename(source.split("?")[0])
            base, ext = os.path.splitext(name)
            base = re.sub(r'[a-f0-9]{16,}', '', base, flags=re.IGNORECASE)
            base = re.sub(r'[-_][0-9]{8,}', '', base)
            base = re.sub(r'[^\w\s-]', '', base)
            base = base.strip().replace(' ', '_')
            base = re.sub(r'[_-]+', '_', base).strip('_')
            if prefix:
                base = f"{prefix}_{base}" if base else prefix
            if not base:
                base = "file"
            return f"{base}{ext}"

        with app.app_context():
            try:
                project = Project.query.filter_by(id=project_id, user_id=user_id).first()
                if not project:
                    app.logger.error(f"[async_generate_clips] Project {project_id} not found")
                    return

                paths = get_workspace_paths(user_id, project_id)
                media_folder = paths['clips'].parent / "media"
                music_folder = paths['clips'].parent / "music"
                media_folder.mkdir(parents=True, exist_ok=True)
                music_folder.mkdir(parents=True, exist_ok=True)

                query = project.title
                prefix = query.replace(" ", "_")

                # --- Download media ---
                media_files = download_media_for_query(query, media_folder)
                media_clips = []
                for file in media_files:
                    if isinstance(file, (str, Path)):
                        dest = media_folder / safe_filename(file, prefix=prefix)
                        original_file = Path(file) if isinstance(file, str) else file
                        if original_file.exists() and not dest.exists():
                            shutil.move(str(original_file), str(dest))
                        media_clips.append(dest)

                # --- Download music ---
                music_urls = _search_jamendo_music(query)
                music_clips = []
                if music_urls:
                    async def run_music():
                        downloaded_files = []
                        for music_url in music_urls:
                            temp_files = await _download_all([music_url], music_folder)
                            for temp_file in temp_files:
                                dest = music_folder / safe_filename(temp_file, prefix=prefix)
                                if temp_file.exists() and not dest.exists():
                                    shutil.move(str(temp_file), str(dest))
                                downloaded_files.append(dest)
                        return downloaded_files
                    music_clips = asyncio.run(run_music())

                # --- Save manifest ---
                _save_manifest({
                    "project_id": project.id,
                    "media_clips": list(dict.fromkeys([str(p) for p in media_clips])),
                    "music_clips": list(dict.fromkeys([str(p) for p in music_clips])),
                    "subtitles": []
                }, user_id, project_id)

                app.logger.info(f"[async_generate_clips] ✅ Downloads complete for project {project.id}")

            except Exception as e:
                app.logger.error(f"[ERROR] Failed to generate clips for project {project_id}: {e}", exc_info=True)

    # =====================
    # POST handling
    # =====================
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=True)
        script_text = form_data.get('script_text', '').strip()
        regenerate = 'regenerate' in request.form or 'save-regenerate' in request.form

        if script_text or regenerate:
            if regenerate:
                try:
                    new_script = engine.generate_script(project.title, form_data)
                    if new_script and new_script.strip():
                        project.script = new_script.strip()
                        db.session.commit()
                        with open(paths['script'], 'w', encoding='utf-8') as f:
                            f.write(new_script.strip())
                        script_text = new_script.strip()
                    else:
                        flash("Failed to regenerate script", "error")
                except Exception:
                    flash("Error regenerating script", "error")
            else:
                project.script = script_text
                db.session.commit()
                with open(paths['script'], 'w', encoding='utf-8') as f:
                    f.write(script_text)

            # Start async clip generation
            from threading import Thread
            Thread(target=async_generate_clips, args=(project.id, current_user.id), daemon=True).start()

            # Return JSON for AJAX or redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Script saved! Media download started.',
                    'project_id': project.id
                })

            return redirect(url_for('clips', project_id=project.id))

    # =====================
    # GET handling
    # =====================
    keywords_str = paths['keywords'].read_text().strip() if paths['keywords'].exists() else ""

    # Ensure clips_data always has correct structure
    clips_data = {"media_clips": [], "music_clips": [], "subtitles": []}
    if paths['clips'].exists():
        try:
            with open(paths['clips'], 'r') as f:
                clips_data = json.load(f)
            clips_data.setdefault("media_clips", [])
            clips_data.setdefault("music_clips", [])
            clips_data.setdefault("subtitles", [])
        except Exception as e:
            app.logger.error(f"[/script] Failed to read clips.json: {e}", exc_info=True)

    return render_template(
        'script.html',
        project=project,
        script=project.script or "",
        keywords=keywords_str,
        clips_data=clips_data
    )


# ============================
# /upload_clip route
# ============================
@app.route("/upload_clip", methods=["POST"])
@limiter.limit("10 per hour")
@login_required
def upload_clip():
    """Handle clip upload"""
    project_id = session.get('project_id')
    if not project_id:
        return jsonify({"error": "No project selected"}), 400

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 403

    if 'clip' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['clip']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_video_file(file.filename):
        paths = get_workspace_paths(current_user.id, project_id)
        clips_dir = paths['media']  # save uploaded clips to 'media'
        clips_dir.mkdir(parents=True, exist_ok=True)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"

        filepath = clips_dir / filename
        file.save(str(filepath))

        # Update or create clips.json after the actual file exists
        clips_json_path = paths['clips']
        if clips_json_path.exists():
            try:
                with open(clips_json_path, 'r') as f:
                    clips_data = json.load(f)
            except:
                clips_data = {'project_id': project_id, 'media_clips': [], 'music_clips': [], 'subtitles': []}
        else:
            clips_data = {'project_id': project_id, 'media_clips': [], 'music_clips': [], 'subtitles': []}

        if 'media_clips' not in clips_data:
            clips_data['media_clips'] = []

        if filename not in clips_data['media_clips']:
            clips_data['media_clips'].append(filename)

        with open(clips_json_path, 'w') as f:
            json.dump(clips_data, f, indent=2)

        app.logger.info(f"User {current_user.id} uploaded clip: {filename} to project {project_id}")

        return jsonify({
            "success": True,
            "filename": filename,
            "path": url_for('serve_clip', user_id=current_user.id, project_id=project_id, filename=filename)
        })

    return jsonify({"error": "Invalid file format"}), 400





import json
from pathlib import Path


def generate_clips_for_project(project, paths):
    """
    Generate media clips for the project.
    For now, simulate downloading 5 media files and 2 music files.
    Replace this with actual download logic from APIs (Pixabay, Pexels, etc.)
    """
    import time
    paths['clips'].parent.mkdir(parents=True, exist_ok=True)

    clips_data = {
        "project_id": project.id,
        "media_clips": [],
        "music_clips": [],
        "subtitles": []
    }

    # Simulate media download
    for i in range(1, 6):
        filename = f"media_clip_{i}.mp4"
        # simulate a small delay
        time.sleep(1)
        clips_data['media_clips'].append(filename)
        app.logger.info(f"[generate_clips] Project {project.id} media clip added: {filename}")

    # Simulate music download
    for i in range(1, 3):
        filename = f"music_clip_{i}.mp3"
        time.sleep(0.5)
        clips_data['music_clips'].append(filename)
        app.logger.info(f"[generate_clips] Project {project.id} music clip added: {filename}")

    # Save updated clips.json
    with open(paths['clips'], 'w', encoding='utf-8') as f:
        json.dump(clips_data, f, indent=2)
    app.logger.info(f"[generate_clips] Project {project.id} clips.json updated")



# ============================
# /api/clips/data route
# ============================
@app.route('/api/clips/data')
@login_required
def api_clips_data():
    project_id = request.args.get('project_id', type=int) or session.get('project_id')
    if not project_id:
        return jsonify({'status': 'error', 'message': 'No project selected', 'progress': 0})

    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        return jsonify({'status': 'error', 'message': 'Project not found', 'progress': 0})

    paths = get_workspace_paths(current_user.id, project_id)
    if not paths['clips'].exists():
        paths['clips'].parent.mkdir(parents=True, exist_ok=True)
        with open(paths['clips'], 'w', encoding='utf-8') as f:
            json.dump({'project_id': project_id, 'media_clips': [], 'music_clips': [], 'subtitles': []}, f, indent=2)

    try:
        with open(paths['clips'], 'r', encoding='utf-8') as f:
            clips_data = json.load(f)
        clips_data.setdefault('media_clips', [])
        clips_data.setdefault('music_clips', [])
        clips_data.setdefault('subtitles', [])
        clips_data.setdefault('project_id', project_id)

        return jsonify({
            'status': 'completed',
            'message': 'Clips data loaded',
            'progress': 100,
            'project_id': clips_data['project_id'],
            'media_clips': clips_data['media_clips'],
            'music_clips': clips_data['music_clips'],
            'subtitles': clips_data['subtitles']
        })
    except Exception as e:
        app.logger.error(f"[/api/clips/data] Error reading clips.json: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Failed to read clips.json',
            'progress': 0,
            'project_id': project_id,
            'media_clips': [],
            'music_clips': [],
            'subtitles': []
        })

# ========================================================================
# CLIPS PAGE - FIXED FOR MISSING OR INVALID clips.json
# ========================================================================
@app.route("/clips")
@login_required
def clips():
    user_id = current_user.id
    project_id = session.get('project_id')
    if not project_id:
        flash("No project selected", "error")
        return redirect(url_for("projects"))

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        flash("Project not found", "error")
        return redirect(url_for("projects"))

    paths = get_workspace_paths(user_id, project_id)

    # Ensure clips.json exists and has correct schema
    if not paths['clips'].exists():
        paths['clips'].parent.mkdir(parents=True, exist_ok=True)
        with open(paths['clips'], 'w', encoding='utf-8') as f:
            json.dump({
                'project_id': project_id,
                'media_clips': [],
                'music_clips': [],
                'subtitles': []
            }, f, indent=2)
        clips_data = {'project_id': project_id, 'media_clips': [], 'music_clips': [], 'subtitles': []}
    else:
        try:
            with open(paths['clips'], "r", encoding="utf-8") as f:
                clips_data = json.load(f)
            # enforce schema for template safety
            clips_data.setdefault('media_clips', [])
            clips_data.setdefault('music_clips', [])
            clips_data.setdefault('subtitles', [])
            clips_data.setdefault('project_id', project_id)
            app.logger.info(f"[/clips] Loaded clips.json for project {project_id}")
        except Exception as e:
            app.logger.error(f"[/clips] Error reading clips.json: {e}", exc_info=True)
            clips_data = {'project_id': project_id, 'media_clips': [], 'music_clips': [], 'subtitles': []}

    return render_template(
        "clips.html",
        project=project,
        clips_data=clips_data
    )





# Import get_remote_address at the top of app.py
from flask_limiter.util import get_remote_address

# Or define your own get_limiter_key function
def get_limiter_key():
    """Get the key for rate limiting based on remote address."""
    # If behind a proxy, use X-Forwarded-For
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    # Otherwise use remote_addr
    return request.remote_addr or '127.0.0.1'

# Configure rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Use the imported function
    default_limits=["100 per day", "10 per hour"],
    storage_uri="memory://"
)



@app.route("/delete_clip", methods=["POST"])
@login_required
def delete_clip():
    """Handle clip deletion"""
    project_id = session.get('project_id')

    if not project_id:
        return jsonify({"error": "No project selected"}), 400

    # Verify project belongs to current user
    project = Project.query.filter_by(
        id=project_id,
        user_id=current_user.id
    ).first()

    if not project:
        return jsonify({"error": "Project not found"}), 403

    data = request.get_json()
    filename = data.get('filename')

    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    # Sanitize filename
    filename = secure_filename(filename)

    paths = get_workspace_paths(current_user.id, project_id)
    filepath = paths['workspace'] / "clips" / filename

    if filepath.exists():
        try:
            filepath.unlink()  # Path object's delete method
            app.logger.info(f"User {current_user.id} deleted clip: {filename} from project {project_id}")

            # Also update clips.json if it exists
            clips_json_path = paths['clips']
            if clips_json_path.exists():
                try:
                    with open(clips_json_path, 'r') as f:
                        clips_data = json.load(f)

                    # Remove deleted clip from clips data
                    clips_data = [c for c in clips_data if os.path.basename(c.get('path', '')) != filename]

                    with open(clips_json_path, 'w') as f:
                        json.dump(clips_data, f, indent=2)
                except Exception as e:
                    app.logger.warning(f"Could not update clips.json: {e}")

            return jsonify({"success": True})
        except Exception as e:
            app.logger.error(f"Error deleting clip {filename}: {str(e)}")
            return jsonify({"error": "Failed to delete clip"}), 500

    return jsonify({"error": "Clip not found"}), 404


# Serve clip route remains the same
@app.route("/serve_clip/<int:user_id>/<int:project_id>/<filename>")
@login_required
def serve_clip(user_id, project_id, filename):
    """Serve video/audio/image clip file"""
    if current_user.id != user_id:
        abort(403)

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        abort(404)

    filename = secure_filename(filename)
    paths = get_workspace_paths(user_id, project_id)

    for folder in [paths['media'], paths.get('music', paths['workspace'] / 'music'), paths['workspace'] / "clips"]:
        filepath = folder / filename
        if filepath.exists():
            return send_file(filepath, mimetype=None, as_attachment=False, conditional=True)

    abort(404)



def get_media_info(filepath):
    """Get duration and type info for media files using ffprobe"""
    import subprocess, json

    if not filepath.exists():
        return {'duration': 5.0, 'type': 'unknown'}

    ext = filepath.suffix.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return {'duration': 5.0, 'type': 'image'}

    try:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(filepath)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            has_video = any(s.get('codec_type') == 'video' for s in data.get('streams', []))
            has_audio = any(s.get('codec_type') == 'audio' for s in data.get('streams', []))
            if has_video:
                return {'duration': duration, 'type': 'video'}
            if has_audio:
                return {'duration': duration, 'type': 'audio'}
    except Exception as e:
        app.logger.warning(f"Could not get media info for {filepath}: {e}")

    # Fallback
    if ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv']:
        return {'duration': 10.0, 'type': 'video'}
    if ext in ['.mp3', '.wav', '.ogg', '.m4a']:
        return {'duration': 30.0, 'type': 'audio'}

    return {'duration': 5.0, 'type': 'unknown'}

# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

def allowed_video_file(filename):
    """Check if the uploaded file has an allowed video extension"""
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    if not filename:
        return False

    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


def get_workspace_paths(user_id, project_id):
    """Get all relevant paths for a user's project workspace"""
    workspace_base = Path(app.config.get('WORKSPACE_DIR', 'workspace'))
    user_workspace = workspace_base / f"user_{user_id}" / f"project_{project_id}"

    # Ensure directories exist
    user_workspace.mkdir(parents=True, exist_ok=True)

    return {
        'workspace': user_workspace,
        'clips': user_workspace / 'clips.json',
        'status': user_workspace / 'status.txt',
        'assets': user_workspace / 'assets',
        'media': user_workspace / 'media',
        'output': user_workspace / 'output',
        'keywords': user_workspace / 'keywords.txt',
        'script': user_workspace / 'script.txt',
        'narration': user_workspace / 'narration.mp3',
        'final_video': user_workspace / 'final_video.mp4',
        'config': user_workspace / 'config.json',
        'final': user_workspace / 'final',
        'music': user_workspace / 'music'  # Add this if you need music directory
    }

def generate_clips_for_project(project, paths):
    """
    Generate a default clips.json for a project if it doesn't exist.
    For now, just creates an empty structure to prevent /clips errors.
    """
    clips_file = paths['clips']

    if not clips_file.exists():
        clips_data = {
            "project_id": project.id,
            "media_clips": [],
            "music_clips": [],
            "subtitles": []
        }

        # Ensure parent directory exists
        clips_file.parent.mkdir(parents=True, exist_ok=True)

        # Write empty clips.json
        with open(clips_file, 'w') as f:
            json.dump(clips_data, f, indent=2)

        app.logger.info(f"[/script] Created empty clips.json for project {project.id}")


@app.route("/generate_final_video", methods=["POST"])
def generate_final_video():
    user_id = session.get('user_id')
    project_id = session.get('project_id')

    if not user_id or not project_id:
        return jsonify({"error": "No project selected"}), 400

    data = request.get_json()
    clip_order = data.get('clip_order', [])

    if not clip_order:
        return jsonify({"error": "No clips selected"}), 400

    workspace_path = get_workspace_paths(user_id, project_id)
    clips_dir = os.path.join(workspace_path, "clips")

    # Verify all clips exist
    clip_paths = []
    for clip_name in clip_order:
        clip_path = os.path.join(clips_dir, secure_filename(clip_name))
        if not os.path.exists(clip_path):
            return jsonify({"error": f"Clip {clip_name} not found"}), 404
        clip_paths.append(clip_path)

    try:
        # Generate final video using moviepy or similar
        output_path = os.path.join(workspace_path, "final_video.mp4")

        # Here you would implement the actual video concatenation
        # This is a placeholder for the video generation logic
        concatenate_videos(clip_paths, output_path)

        app.logger.info(f"User {user_id} generated final video for project {project_id}")

        return jsonify({
            "success": True,
            "video_url": url_for('serve_final_video', user_id=user_id, project_id=project_id)
        })

    except Exception as e:
        app.logger.error(f"Error generating final video: {str(e)}")
        return jsonify({"error": "Failed to generate video"}), 500


@app.route("/serve_final_video/<int:user_id>/<int:project_id>")
def serve_final_video(user_id, project_id):
    # Verify user has access
    if session.get('user_id') != user_id:
        abort(403)

    workspace_path = get_workspace_paths(user_id, project_id)

    # Find the final video file
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        video_path = os.path.join(workspace_path, f"final_video{ext}")
        if os.path.exists(video_path):
            return send_file(video_path, mimetype=f'video/{ext[1:]}')

    abort(404)


@app.route("/download_final_video/<int:user_id>/<int:project_id>")
def download_final_video(user_id, project_id):
    # Verify user has access
    if session.get('user_id') != user_id:
        abort(403)

    workspace_path = get_workspace_paths(user_id, project_id)

    # Find the final video file
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        video_path = os.path.join(workspace_path, f"final_video{ext}")
        if os.path.exists(video_path):
            project = Project.query.get(project_id)
            if project:
                filename = f"{secure_filename(project.name)}_final{ext}"
            else:
                filename = f"final_video{ext}"

            return send_file(video_path,
                             mimetype=f'video/{ext[1:]}',
                             as_attachment=True,
                             download_name=filename)

    flash("No final video found", "error")
    return redirect(url_for("final_video"))


@app.route("/export_project/<int:user_id>/<int:project_id>")
def export_project(user_id, project_id):
    # Verify user has access
    if session.get('user_id') != user_id:
        abort(403)

    workspace_path = get_workspace_paths(user_id, project_id)

    if not os.path.exists(workspace_path):
        flash("Project workspace not found", "error")
        return redirect(url_for("projects"))

    try:
        # Create a temporary zip file
        project = Project.query.get(project_id)
        zip_filename = f"{secure_filename(project.name)}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, workspace_path)
                    zipf.write(file_path, arcname)

        app.logger.info(f"User {user_id} exported project {project_id}")

        # Send file and cleanup
        def remove_file(response):
            try:
                os.remove(zip_path)
                os.rmdir(temp_dir)
            except Exception as e:
                app.logger.error(f"Error removing temporary files: {e}")
            return response

        return send_file(zip_path,
                         mimetype='application/zip',
                         as_attachment=True,
                         download_name=zip_filename).call_on_close(remove_file)

    except Exception as e:
        app.logger.error(f"Error exporting project: {str(e)}")
        flash("Failed to export project", "error")
        return redirect(url_for("projects"))


@app.route("/cleanup_workspace", methods=["POST"])
def cleanup_workspace():
    user_id = session.get('user_id')
    project_id = session.get('project_id')

    if not user_id or not project_id:
        return jsonify({"error": "No project selected"}), 400

    workspace_path = get_workspace_paths(user_id, project_id)

    try:
        # Remove all files except script.txt
        for root, dirs, files in os.walk(workspace_path):
            for file in files:
                if file != 'script.txt':
                    file_path = os.path.join(root, file)
                    os.remove(file_path)

        # Remove empty directories
        for root, dirs, files in os.walk(workspace_path, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)

        app.logger.info(f"User {user_id} cleaned up workspace for project {project_id}")
        return jsonify({"success": True})

    except Exception as e:
        app.logger.error(f"Error cleaning up workspace: {str(e)}")
        return jsonify({"error": "Failed to cleanup workspace"}), 500


@app.route("/get_workspace_info")
def get_workspace_info():
    user_id = session.get('user_id')
    project_id = session.get('project_id')

    if not user_id or not project_id:
        return jsonify({"error": "No project selected"}), 400

    workspace_path = get_workspace_paths(user_id, project_id)

    if not os.path.exists(workspace_path):
        return jsonify({
            "exists": False,
            "size": 0,
            "file_count": 0
        })

    # Calculate workspace size and file count
    total_size = 0
    file_count = 0

    for root, dirs, files in os.walk(workspace_path):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
            file_count += 1

    # Get specific file types count
    clips_count = 0
    clips_dir = os.path.join(workspace_path, "clips")
    if os.path.exists(clips_dir):
        clips_count = len([f for f in os.listdir(clips_dir)
                           if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))])

    has_script = os.path.exists(os.path.join(workspace_path, "script.txt"))
    has_final_video = any(os.path.exists(os.path.join(workspace_path, f"final_video{ext}"))
                          for ext in ['.mp4', '.avi', '.mov', '.mkv'])

    return jsonify({
        "exists": True,
        "size": total_size,
        "size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": file_count,
        "clips_count": clips_count,
        "has_script": has_script,
        "has_final_video": has_final_video
    })


# Helper function for video concatenation
def concatenate_videos(clip_paths, output_path):
    """
    Concatenate video clips into a single video file.
    This is a placeholder - implement with moviepy or ffmpeg
    """
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips

        clips = []
        for path in clip_paths:
            clip = VideoFileClip(path)
            clips.append(clip)

        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

        # Clean up
        for clip in clips:
            clip.close()
        final_clip.close()

    except ImportError:
        # Fallback to ffmpeg command if moviepy not available
        import subprocess

        # Create a temporary file list for ffmpeg
        list_file = output_path + '.txt'
        with open(list_file, 'w') as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")

        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file,
            '-c', 'copy', output_path
        ]

        subprocess.run(cmd, check=True)
        os.remove(list_file)


# Helper function to check allowed video formats
def allowed_video_file(filename):
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    return '.' in filename and \
        os.path.splitext(filename)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


# API endpoints for AJAX operations
@app.route("/api/project/<int:project_id>/files")
def api_project_files(project_id):
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    # Verify user owns this project
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({"error": "Project not found or access denied"}), 404

    workspace_path = get_workspace_paths(user_id, project_id)

    files = {
        "script": None,
        "clips": [],
        "final_video": None
    }

    # Check for script
    script_path = os.path.join(workspace_path, "script.txt")
    if os.path.exists(script_path):
        files["script"] = {
            "filename": "script.txt",
            "size": os.path.getsize(script_path),
            "modified": os.path.getmtime(script_path)
        }

    # Check for clips
    clips_dir = os.path.join(workspace_path, "clips")
    if os.path.exists(clips_dir):
        for filename in os.listdir(clips_dir):
            if allowed_video_file(filename):
                filepath = os.path.join(clips_dir, filename)
                files["clips"].append({
                    "filename": filename,
                    "size": os.path.getsize(filepath),
                    "modified": os.path.getmtime(filepath),
                    "url": url_for('serve_clip', user_id=user_id, project_id=project_id, filename=filename)
                })

    # Check for final video
    for ext in ['.mp4', '.avi', '.mov', '.mkv']:
        video_path = os.path.join(workspace_path, f"final_video{ext}")
        if os.path.exists(video_path):
            files["final_video"] = {
                "filename": f"final_video{ext}",
                "size": os.path.getsize(video_path),
                "modified": os.path.getmtime(video_path),
                "url": url_for('serve_final_video', user_id=user_id, project_id=project_id),
                "download_url": url_for('download_final_video', user_id=user_id, project_id=project_id)
            }
            break

    return jsonify(files)


@app.route("/api/workspace/usage")
def api_workspace_usage():
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    # Calculate total disk usage for user
    total_size = 0
    project_sizes = {}

    user_projects = Project.query.filter_by(user_id=user_id).all()

    for project in user_projects:
        workspace_path = get_workspace_paths(user_id, project.id)
        project_size = 0

        if os.path.exists(workspace_path):
            for root, dirs, files in os.walk(workspace_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    project_size += file_size
                    total_size += file_size

        project_sizes[project.id] = {
            "name": project.name,
            "size": project_size,
            "size_mb": round(project_size / (1024 * 1024), 2)
        }

    # Check against user's quota (if implemented)
    quota_mb = 1024  # Example: 1GB quota per user
    used_mb = round(total_size / (1024 * 1024), 2)

    return jsonify({
        "total_size": total_size,
        "total_size_mb": used_mb,
        "quota_mb": quota_mb,
        "remaining_mb": round(quota_mb - used_mb, 2),
        "usage_percentage": round((used_mb / quota_mb) * 100, 2),
        "projects": project_sizes
    })


@app.route("/migrate_legacy_workspace", methods=["POST"])
def migrate_legacy_workspace():
    """
    Migrate files from old workspace structure to new user-specific structure
    """
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Old workspace path (if you had a different structure before)
        old_workspace = os.path.join(app.config['UPLOAD_FOLDER'], 'workspace')

        if not os.path.exists(old_workspace):
            return jsonify({"message": "No legacy workspace found"}), 200

        migrated_count = 0

        # Get user's projects
        user_projects = Project.query.filter_by(user_id=user_id).all()

        for project in user_projects:
            new_workspace = get_workspace_paths(user_id, project.id)

            # Look for files that might belong to this project
            # This is a simplified example - adjust based on your old structure
            old_project_path = os.path.join(old_workspace, str(project.id))

            if os.path.exists(old_project_path):
                # Create new workspace
                os.makedirs(new_workspace, exist_ok=True)

                # Copy files
                for item in os.listdir(old_project_path):
                    old_item_path = os.path.join(old_project_path, item)
                    new_item_path = os.path.join(new_workspace, item)

                    if os.path.isfile(old_item_path):
                        shutil.copy2(old_item_path, new_item_path)
                        migrated_count += 1
                    elif os.path.isdir(old_item_path):
                        shutil.copytree(old_item_path, new_item_path)
                        migrated_count += 1

        app.logger.info(f"User {user_id} migrated {migrated_count} items from legacy workspace")

        return jsonify({
            "success": True,
            "migrated_count": migrated_count
        })

    except Exception as e:
        app.logger.error(f"Error during workspace migration: {str(e)}")
        return jsonify({"error": "Migration failed"}), 500


# Background task to clean up old workspaces
@app.route("/admin/cleanup_old_workspaces", methods=["POST"])
def cleanup_old_workspaces():
    """
    Admin endpoint to clean up workspaces for deleted projects
    """
    # Add admin authentication check here
    if not session.get('is_admin'):
        abort(403)

    try:
        cleaned_count = 0
        workspace_base = app.config['UPLOAD_FOLDER']

        # Get all workspace directories
        for item in os.listdir(workspace_base):
            if item.startswith('workspace_u'):
                # Extract user_id and project_id from directory name
                match = re.match(r'workspace_u(\d+)_p(\d+)', item)
                if match:
                    user_id = int(match.group(1))
                    project_id = int(match.group(2))

                    # Check if project still exists
                    project = Project.query.get(project_id)
                    if not project:
                        # Remove orphaned workspace
                        workspace_path = os.path.join(workspace_base, item)
                        shutil.rmtree(workspace_path)
                        cleaned_count += 1
                        app.logger.info(f"Removed orphaned workspace: {item}")

        return jsonify({
            "success": True,
            "cleaned_count": cleaned_count
        })

    except Exception as e:
        app.logger.error(f"Error cleaning up workspaces: {str(e)}")
        return jsonify({"error": "Cleanup failed"}), 500


# Error handlers
@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Access forbidden"}), 403
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Resource not found"}), 404
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"Internal error: {str(error)}")
    if request.path.startswith('/api/'):
        return jsonify({"error": "Internal server error"}), 500
    return render_template('errors/500.html'), 500


# Context processor to make helper functions available in templates
@app.context_processor
def utility_processor():
    def format_file_size(size):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def time_ago(timestamp):
        """Convert timestamp to human readable time ago format"""
        if isinstance(timestamp, float):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = timestamp

        now = datetime.now()
        diff = now - dt

        if diff.seconds < 60:
            return "just now"
        elif oft.seconds < 3600:
            return f"{diff.seconds // 60} minutes ago"
        elif diff.days < 1:
            return f"{diff.seconds // 3600} hours ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            return f"{diff.days // 7} weeks ago"
        elif diff.days < 365:
            return f"{diff.days // 30} months ago"
        else:
            return f"{diff.days // 365} years ago"

    def get_file_icon(filename):
        """Get appropriate icon class for file type"""
        ext = os.path.splitext(filename)[1].lower()

        icon_map = {
            '.mp4': 'fa-file-video',
            '.avi': 'fa-file-video',
            '.mov': 'fa-file-video',
            '.mkv': 'fa-file-video',
            '.webm': 'fa-file-video',
            '.txt': 'fa-file-text',
            '.pdf': 'fa-file-pdf',
            '.doc': 'fa-file-word',
            '.docx': 'fa-file-word',
            '.jpg': 'fa-file-image',
            '.jpeg': 'fa-file-image',
            '.png': 'fa-file-image',
            '.gif': 'fa-file-image',
            '.zip': 'fa-file-archive',
            '.rar': 'fa-file-archive',
        }

        return icon_map.get(ext, 'fa-file')

    return dict(
        format_file_size=format_file_size,
        time_ago=time_ago,
        get_file_icon=get_file_icon
    )


# Scheduled tasks (if using Flask-APScheduler)
def cleanup_temp_files():
    """Clean up temporary files older than 24 hours"""
    temp_dir = tempfile.gettempdir()
    cutoff_time = datetime.now() - timedelta(hours=24)

    for filename in os.listdir(temp_dir):
        if filename.startswith('tmp_video_'):
            filepath = os.path.join(temp_dir, filename)
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                if file_time < cutoff_time:
                    os.remove(filepath)
                    app.logger.info(f"Removed old temp file: {filename}")
            except Exception as e:
                app.logger.error(f"Error removing temp file {filename}: {str(e)}")


def check_disk_usage():
    """Monitor disk usage and alert if necessary"""
    workspace_base = app.config['UPLOAD_FOLDER']

    # Get disk usage
    stat = shutil.disk_usage(workspace_base)
    used_percent = (stat.used / stat.total) * 100

    if used_percent > 90:
        app.logger.warning(f"Disk usage critical: {used_percent:.2f}%")
        # Send alert email or notification
    elif used_percent > 80:
        app.logger.warning(f"Disk usage high: {used_percent:.2f}%")


# CLI commands for maintenance
@app.cli.command()
@click.argument('user_id', type=int)
def reset_user_workspace(user_id):
    """Reset all workspaces for a specific user"""
    click.echo(f"Resetting workspaces for user {user_id}...")

    user = User.query.get(user_id)
    if not user:
        click.echo(f"User {user_id} not found!")
        return

    projects = Project.query.filter_by(user_id=user_id).all()

    for project in projects:
        workspace_path = get_workspace_paths(user_id, project.id)
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)
            click.echo(f"Removed workspace for project {project.id}")

    click.echo("Done!")


@app.cli.command()
def cleanup_orphaned_workspaces():
    """Remove workspaces for non-existent projects"""
    click.echo("Cleaning up orphaned workspaces...")

    workspace_base = app.config['UPLOAD_FOLDER']
    cleaned_count = 0

    for item in os.listdir(workspace_base):
        if item.startswith('workspace_u'):
            match = re.match(r'workspace_u(\d+)_p(\d+)', item)
            if match:
                user_id = int(match.group(1))
                project_id = int(match.group(2))

                project = Project.query.get(project_id)
                if not project or project.user_id != user_id:
                    workspace_path = os.path.join(workspace_base, item)
                    shutil.rmtree(workspace_path)
                    cleaned_count += 1
                    click.echo(f"Removed orphaned workspace: {item}")

    click.echo(f"Cleaned up {cleaned_count} orphaned workspaces")


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    click.echo("Database initialized!")


@app.cli.command()
def create_admin():
    """Create an admin user"""
    username = click.prompt("Admin username")
    email = click.prompt("Admin email")
    password = click.prompt("Admin password", hide_input=True)

    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    click.echo(f"Admin user '{username}' created successfully!")


# Security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Set appropriate cache headers for different content types
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    elif request.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    return response


# Request logging
@app.before_request
def log_request():
    """Log incoming requests"""
    if app.config.get('LOG_REQUESTS'):
        app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")


# Database session management
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Remove database session at the end of request"""
    db.session.remove()


# ========================================================================
# 5) SUPPORT TAB  "/support"
# ========================================================================
@app.route('/support', methods=['GET', 'POST'])
def support():
    sr_number = None
    ticket_types = ['Issue', 'Enhancement', 'Comment']  # Define ticket types

    if request.method == 'POST':
        form = request.form.to_dict(flat=True)

        # Add user information if logged in
        if current_user.is_authenticated:
            form['user_id'] = current_user.id
            # Pre-fill email if not provided
            if not form.get('customer_email'):
                form['customer_email'] = current_user.email
            if not form.get('customer_name'):
                form['customer_name'] = getattr(current_user, 'name', current_user.username)

        # Create support ticket
        ok, sr_number, msg = engine.create_support_ticket(form)

        if ok:
            # Add the SR number to the form data
            form['sr_number'] = sr_number

            # Send support email
            try:
                engine.send_support_email(form)
                flash(f'Support ticket created successfully. SR Number: {sr_number}', 'success')
            except Exception as e:
                app.logger.error(f"Failed to send support email: {e}")
                flash(f'Ticket created (SR: {sr_number}) but email notification failed.', 'warning')
        else:
            flash(msg, 'error')

        # Redirect to prevent form resubmission
        if ok:
            return redirect(url_for('support'))

    # Get current datetime for the template
    from datetime import datetime, timezone
    current_time = datetime.now()

    return render_template('support.html',
                           sr_number=sr_number,
                           ticket_types=ticket_types,
                           current_time=current_time)

# Main application entry point
if __name__ == "__main__":
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database
    with app.app_context():
        db.create_all()

    # Configure logging
    if not app.debug:
        file_handler = logging.FileHandler('app.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

# Configuration suggestions for production deployment
"""
Production deployment considerations:

1. Use a production WSGI server (Gunicorn, uWSGI)
   gunicorn -w 4 -b 0.0.0.0:5000 app:app

2. Set up nginx as reverse proxy

3. Use PostgreSQL or MySQL instead of SQLite

4. Set up proper logging with rotation:
   - Application logs
   - Access logs
   - Error logs

5. Implement rate limiting to prevent abuse

6. Set up monitoring and alerting

7. Configure backup strategy for user workspaces

8. Implement CDN for static files and videos

9. Use Redis for session storage and caching

10. Set up SSL/TLS certificates

11. Implement proper error tracking (Sentry)

12. Configure environment variables for sensitive data
"""