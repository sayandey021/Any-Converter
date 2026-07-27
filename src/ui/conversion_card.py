import flet as ft
from src.ui.theme import AppTheme
import os

# File type → icon + color mapping
FILE_TYPE_MAP = {
    # Video
    'mp4':  (ft.Icons.MOVIE,          "#a78bfa"),
    'mkv':  (ft.Icons.MOVIE_FILTER,   "#818cf8"),
    'avi':  (ft.Icons.VIDEO_FILE,     "#c084fc"),
    'mov':  (ft.Icons.SLIDESHOW,      "#e879f9"),
    'webm': (ft.Icons.VIDEO_LIBRARY,  "#a78bfa"),
    'rm':   (ft.Icons.VIDEO_FILE, "#f43f5e"),
    'rmvb': (ft.Icons.VIDEO_FILE, "#f43f5e"),
    'vro':  (ft.Icons.VIDEO_FILE, "#f43f5e"),
    'dat':  (ft.Icons.VIDEO_FILE, "#f43f5e"),
    'mpg':  (ft.Icons.VIDEO_FILE, "#f43f5e"),
    'mpeg': (ft.Icons.VIDEO_FILE, "#f43f5e"),

    # Audio
    'aob':  (ft.Icons.AUDIO_FILE, "#3b82f6"),
    'mp3':  (ft.Icons.AUDIO_FILE,     "#34d399"),
    'wav':  (ft.Icons.WAVES,          "#6ee7b7"),
    'flac': (ft.Icons.MUSIC_NOTE,     "#10b981"),
    'm4a':  (ft.Icons.HEADPHONES,     "#34d399"),
    'aac':  (ft.Icons.AUDIO_FILE,     "#eab308"),
    'ogg':  (ft.Icons.AUDIO_FILE,     "#eab308"),
    # Image
    'png':  (ft.Icons.IMAGE,          "#38bdf8"),
    'jpg':  (ft.Icons.PHOTO,          "#0ea5e9"),
    'jpeg': (ft.Icons.PHOTO,          "#0ea5e9"),
    'webp': (ft.Icons.IMAGE_SEARCH,   "#06b6d4"),
    'gif':  (ft.Icons.GIF,            "#22d3ee"),
    'ico':  (ft.Icons.GRID_VIEW,      "#64748b"),
    # Markup
    'md':   (ft.Icons.TEXT_SNIPPET,   "#64748b"),
    # Data
    'json': (ft.Icons.DATA_OBJECT,    "#f59e0b"),
    'yaml': (ft.Icons.SETTINGS,       "#8b5cf6"),
    'yml':  (ft.Icons.SETTINGS,       "#8b5cf6"),
    
    # Document
    # Document
    'pdf':  (ft.Icons.PICTURE_AS_PDF, "#dc2626"),
    'epub': (ft.Icons.BOOK,           "#6366f1"),
    'mobi': (ft.Icons.BOOKMARKS,      "#6366f1"),
    'azw3': (ft.Icons.AUTO_STORIES,   "#6366f1"),
    'azw':  (ft.Icons.AUTO_STORIES,   "#6366f1"),
    'iba':  (ft.Icons.MENU_BOOK,      "#6366f1"),
    'djvu': (ft.Icons.PICTURE_IN_PICTURE, "#dc2626"),
    'djv':  (ft.Icons.PICTURE_IN_PICTURE, "#dc2626"),
    'doc':  (ft.Icons.DESCRIPTION,    "#2563eb"),
    'docx': (ft.Icons.DESCRIPTION,    "#2563eb"),
    'docm': (ft.Icons.DESCRIPTION,    "#2563eb"),
    'dot':  (ft.Icons.DESCRIPTION,    "#2563eb"),
    'dotx': (ft.Icons.DESCRIPTION,    "#2563eb"),
    'dotm': (ft.Icons.DESCRIPTION,    "#2563eb"),
    'rtf':  (ft.Icons.DESCRIPTION,    "#2563eb"),
    'txt':  (ft.Icons.SUBJECT,        "#94a3b8"),
    'log':  (ft.Icons.SUBJECT,        "#94a3b8"),
    'odt':  (ft.Icons.DESCRIPTION,    "#2563eb"),
    'mht':  (ft.Icons.WEB,            "#2563eb"),
    'html': (ft.Icons.WEB,            "#2563eb"),
    'htm':  (ft.Icons.WEB,            "#2563eb"),
    'xml':  (ft.Icons.CODE,           "#2563eb"),
    'xls':  (ft.Icons.TABLE_CHART,    "#16a34a"),
    'xlsx': (ft.Icons.TABLE_CHART,    "#16a34a"),
    'xlsm': (ft.Icons.TABLE_CHART,    "#16a34a"),
    'xlsb': (ft.Icons.TABLE_CHART,    "#16a34a"),
    'csv':  (ft.Icons.TABLE_CHART,    "#16a34a"),
    'ods':  (ft.Icons.TABLE_CHART,    "#16a34a"),
    'ppt':  (ft.Icons.PRESENT_TO_ALL, "#ea580c"),
    'pptx': (ft.Icons.PRESENT_TO_ALL, "#ea580c"),
    'pptm': (ft.Icons.PRESENT_TO_ALL, "#ea580c"),
    'pps':  (ft.Icons.PRESENT_TO_ALL, "#ea580c"),
    'odp':  (ft.Icons.PRESENT_TO_ALL, "#ea580c"),
    
    # 3D Models & CAD
    'obj':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'stl':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'ply':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'glb':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'gltf': (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'fbx':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'off':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'dae':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    '3mf':  (ft.Icons.VIEW_IN_AR,       "#ec4899"),
    'step': (ft.Icons.THREED_ROTATION, "#ec4899"),
    'stp':  (ft.Icons.THREED_ROTATION, "#ec4899"),
    'iges': (ft.Icons.THREED_ROTATION, "#ec4899"),
    'igs':  (ft.Icons.THREED_ROTATION, "#ec4899"),
    'dxf':  (ft.Icons.ARCHITECTURE,     "#ec4899"),
    'dwg':  (ft.Icons.ARCHITECTURE,     "#ec4899"),

    # Subtitles
    'srt': (ft.Icons.SUBTITLES,       "#a855f7"),
    'vtt': (ft.Icons.SUBTITLES,       "#a855f7"),
    'ass': (ft.Icons.SUBTITLES,       "#a855f7"),
    'ssa': (ft.Icons.SUBTITLES,       "#a855f7"),
    'sub': (ft.Icons.SUBTITLES,       "#a855f7"),
    'scc': (ft.Icons.CLOSED_CAPTION,  "#a855f7"),

    # Fonts
    'ttf':   (ft.Icons.FONT_DOWNLOAD, "#14b8a6"),
    'otf':   (ft.Icons.FONT_DOWNLOAD, "#14b8a6"),
    'woff':  (ft.Icons.FONT_DOWNLOAD, "#14b8a6"),
    'woff2': (ft.Icons.FONT_DOWNLOAD, "#14b8a6"),

    # Databases
    'sql':     (ft.Icons.STORAGE, "#6366f1"),
    'db':      (ft.Icons.STORAGE, "#6366f1"),
    'sqlite':  (ft.Icons.STORAGE, "#6366f1"),
    'sqlite3': (ft.Icons.STORAGE, "#6366f1"),
    'mdb':     (ft.Icons.STORAGE, "#6366f1"),
    'accdb':   (ft.Icons.STORAGE, "#6366f1"),

    # GIS & Geospatial
    'geojson': (ft.Icons.MAP,         "#10b981"),
    'kml':     (ft.Icons.EXPLORE,     "#10b981"),
    'kmz':     (ft.Icons.EXPLORE,     "#10b981"),
    'gpx':     (ft.Icons.LOCATION_ON, "#10b981"),
    'shp':     (ft.Icons.MAP,         "#10b981"),

    # Archives & Disk Images
    'zip':   (ft.Icons.FOLDER_ZIP, "#eab308"),
    'rar':   (ft.Icons.FOLDER_ZIP, "#eab308"),
    '7z':    (ft.Icons.FOLDER_ZIP, "#eab308"),
    'tar':   (ft.Icons.FOLDER_ZIP, "#eab308"),
    'gz':    (ft.Icons.FOLDER_ZIP, "#eab308"),
    'tgz':   (ft.Icons.FOLDER_ZIP, "#eab308"),
    'bz2':   (ft.Icons.FOLDER_ZIP, "#eab308"),
    'xz':    (ft.Icons.FOLDER_ZIP, "#eab308"),
    'iso':   (ft.Icons.DISC_FULL,  "#eab308"),
    'img':   (ft.Icons.DISC_FULL,  "#eab308"),
    'mds':   (ft.Icons.DISC_FULL,  "#eab308"),
    'mdf':   (ft.Icons.DISC_FULL,  "#eab308"),
    'folder':  (ft.Icons.FOLDER_OPEN, "#3b82f6"),
    'extract': (ft.Icons.FOLDER_OPEN, "#3b82f6"),

    # Vector Graphics
    'svg':  (ft.Icons.BRUSH,          "#06b6d4"),
    'eps':  (ft.Icons.COLOR_LENS,     "#8b5cf6"),
    'ai':   (ft.Icons.PALETTE,        "#f97316"),
}

FORMAT_GROUPS = {
    'video': ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'vro', 'dat', 'mpg', 'mpeg'],
    'audio': ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'aiff', 'alac', 'dff', 'dsf', 'mqa', 'mod', 's3m', 'xm', 'it', 'wma', 'ra', 'bwf', 'amr', 'ac3', 'eac3', 'thd', 'dts', 'dtshd', 'aob'],
    'image': ['png', 'jpg', 'webp', 'gif', 'bmp', 'heic', 'heif', 'ico', 'tiff', 'tif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'avif', 'jxl'],
    'markup': ['md'],
    'data': ['json', 'yaml', 'yml', 'csv', 'xml'],
    'database': ['sql', 'db', 'sqlite', 'sqlite3', 'mdb', 'accdb'],
    'gis': ['geojson', 'kml', 'kmz', 'gpx', 'shp'],
    'archive': ['zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'tbz2', 'xz', 'txz', 'iso', 'img', 'mds', 'mdf'],
    'subtitle': ['srt', 'vtt', 'ass', 'ssa', 'sub', 'scc'],
    'font': ['ttf', 'otf', 'woff', 'woff2'],
    'document': [
        'pdf', 'epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv', 'doc', 'docx', 'docm', 'dot', 'dotx', 'dotm', 'rtf', 'txt', 'log', 'odt', 'mht', 'html', 'htm',
        'xls', 'xlsx', 'xlsm', 'xlsb', 'ods',
        'ppt', 'pptx', 'pptm', 'pps', 'odp'
    ],
    'model3d': ['obj', 'stl', 'ply', 'glb', 'gltf', 'off', 'dae', 'fbx', 'step', 'stp', 'iges', 'igs', 'dxf', 'dwg', '3mf'],
    'vector': ['svg'],
}

def _get_format_group(ext: str) -> str:
    ext = ext.lstrip('.')
    for group, fmts in FORMAT_GROUPS.items():
        if ext in fmts:
            return group
    return 'other'

def _format_size(size_bytes: int) -> str:
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    size_float = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_float < 1024.0:
            if unit == 'B':
                return f"{int(size_float)} B"
            return f"{size_float:.1f} {unit}".replace('.0 ', ' ')
        size_float /= 1024.0
    return f"{size_float:.1f} PB"


class ConversionCard(ft.Container):
    def __init__(self, job, on_remove, on_status_change=None):
        super().__init__()
        self.job = job
        self.on_remove = on_remove
        self.on_status_change = on_status_change

        self.filename = os.path.basename(job.input_path)
        self.ext = os.path.splitext(self.filename)[1].lower().lstrip('.')
        self.src_group = _get_format_group(self.ext)

        # Decide available target formats based on source type
        if self.src_group == 'video':
            target_opts = ['mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'mp3', 'wav']
            default = 'mp4'
        elif self.src_group == 'audio':
            target_opts = ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'aiff', 'alac', 'wma', 'amr', 'ac3', 'eac3', 'thd', 'dts']
            default = 'mp3'
        elif self.src_group == 'markup':
            target_opts = ['md', 'html', 'rtf', 'txt']
            default = 'html'
        elif self.src_group == 'data':
            target_opts = ['json', 'yaml', 'csv', 'xml', 'pdf']
            default = 'yaml' if self.ext == 'json' else 'json'
        elif self.src_group == 'database':
            target_opts = ['sql', 'sqlite', 'json', 'csv', 'xml', 'yaml']
            default = 'sqlite' if self.ext == 'sql' else 'sql'
        elif self.src_group == 'gis':
            target_opts = ['geojson', 'kml', 'gpx', 'csv', 'json']
            default = 'geojson' if self.ext in ['kml', 'kmz', 'gpx', 'shp'] else 'kml'
        elif self.src_group == 'archive':
            target_opts = ['zip', '7z', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz', 'folder']
            default = '7z' if self.ext == 'zip' else 'zip'
        elif self.src_group == 'subtitle':
            target_opts = ['srt', 'vtt', 'ass', 'sub', 'scc', 'txt']
            default = 'vtt' if self.ext == 'srt' else 'srt'
        elif self.src_group == 'font':
            target_opts = ['ttf', 'otf', 'woff', 'woff2']
            default = 'woff2' if self.ext in ['ttf', 'otf', 'woff'] else 'ttf'
        elif self.src_group == 'document':
            if self.ext in ['txt', 'log']:
                target_opts = ['pdf', 'md', 'html', 'rtf', 'json', 'csv', 'xml']
                default = 'pdf'
            elif self.ext in ['rtf', 'html', 'htm']:
                target_opts = ['pdf', 'md', 'txt', 'html', 'rtf']
                default = 'pdf'
            elif self.ext in ['pdf', 'epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv']:
                if self.ext in ['epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv']:
                    target_opts = ['pdf', 'png', 'jpg', 'webp']
                    default = 'pdf'
                else:
                    # PDF can only convert to images right now
                    target_opts = ['png', 'jpg', 'webp']
                    default = 'png'
            else:
                target_opts = ['pdf']
                default = 'pdf'
        elif self.src_group == 'model3d':
            target_opts = ['obj', 'stl', 'ply', 'glb', 'gltf', 'off', 'dae']
            default = 'glb' if self.ext in ['obj', 'stl', 'ply', 'off', 'dae', 'fbx', 'step', 'stp', 'iges', 'igs', 'dxf', 'dwg', '3mf'] else 'obj'
        elif self.src_group == 'vector':
            if self.ext == 'svg':
                target_opts = ['png', 'jpg', 'webp', 'pdf', 'eps', 'ico']
                default = 'png'
            else:  # eps, ai
                target_opts = ['pdf', 'png', 'jpg', 'webp', 'svg', 'ico']
                default = 'pdf'
        else:  # image / other
            if self.ext == 'gif':
                target_opts = ['mp4', 'webm', 'png', 'jpg', 'webp', 'ico']
                default = 'mp4'
            else:
                target_opts = ['png', 'jpg', 'webp', 'gif', 'bmp', 'ico', 'svg', 'heic', 'heif']
                default = 'jpg' if self.ext == 'png' else 'png'

        self.job.target_format = self.job.target_format or default

        icon_name, icon_color = FILE_TYPE_MAP.get(self.ext, (ft.Icons.INSERT_DRIVE_FILE, AppTheme.TEXT_SECONDARY))

        # ── Format dropdown ──────────────────────────────────────
        self.target_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(f) for f in target_opts],
            value=self.job.target_format,
            width=110,
            border_color=AppTheme.BORDER,
            bgcolor=AppTheme.SURFACE_3,
            color=AppTheme.TEXT_PRIMARY,
            text_size=13,
            content_padding=ft.Padding(left=10, right=4, top=6, bottom=6),
            dense=True,
            border_radius=8,
            focused_border_color=AppTheme.PRIMARY,
        )
        # Set both on_change and on_select for compatibility across Flet versions
        self.target_dropdown.on_change = self.on_format_change
        if hasattr(self.target_dropdown, 'on_select'):
            self.target_dropdown.on_select = self.on_format_change

        # ── Status / progress ─────────────────────────────────────
        self.status_badge = ft.Container(
            content=ft.Text("Pending", size=11, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_MUTED),
            bgcolor=AppTheme.SURFACE_3,
            border_radius=20,
            padding=ft.Padding(left=10, right=10, top=4, bottom=4),
        )
        self.progress_bar = ft.ProgressBar(
            value=0,
            visible=False,
            color=AppTheme.PRIMARY,
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=4,
            height=3,
        )

        # ── Action buttons ────────────────────────────────────────
        self.delete_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=AppTheme.TEXT_MUTED,
            icon_size=16,
            on_click=lambda _: self.on_remove(self),
            tooltip="Remove",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding(left=6, right=6, top=6, bottom=6),
            )
        )

        from src.backend.thumbnail_manager import get_thumbnail, get_thumbnail_async

        # ── File icon block ───────────────────────────────────────
        self.file_icon_block = ft.Container(
            content=ft.Icon(icon_name, color=icon_color, size=28),
            bgcolor=f"22{icon_color.lstrip('#')}",
            border_radius=12,
            padding=ft.Padding(left=12, right=12, top=12, bottom=12),
            width=54, height=54,
        )

        if self.ext in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'ico']:
            self._apply_thumbnail(job.input_path)
        elif self.ext in ['pdf', 'epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv', 'mp4', 'mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'aiff', 'alac', 'dff', 'dsf', 'mqa', 'mod', 's3m', 'xm', 'it', 'wma', 'ra', 'bwf', 'amr', 'ac3', 'eac3', 'thd', 'dts', 'dtshd', 'obj', 'stl', 'ply', 'off', 'dae', 'glb', 'gltf', 'svg', 'tiff', 'tif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'avif', 'jxl', 'heic', 'heif', 'psd']:
            thumb_path = get_thumbnail(job.input_path)
            if thumb_path:
                self._apply_thumbnail(thumb_path)
            else:
                get_thumbnail_async(job.input_path, self._apply_thumbnail_async)

        # ── File size & estimate ─────────────────────────────────
        self.input_bytes = 0
        try:
            if os.path.exists(job.input_path):
                self.input_bytes = os.path.getsize(job.input_path)
        except Exception:
            pass
        self.input_size_str = _format_size(self.input_bytes)
        self.size_info_row = ft.Row(spacing=5)
        self._update_size_info()

        # ── File info ─────────────────────────────────────────────
        name_no_ext = os.path.splitext(self.filename)[0]
        ext_badge = ft.Container(
            content=ft.Text(
                f".{self.ext}".upper(),
                size=10,
                weight=ft.FontWeight.W_700,
                color=icon_color,
            ),
            bgcolor=f"33{icon_color.lstrip('#')}",
            border_radius=20,
            padding=ft.Padding(left=8, right=8, top=3, bottom=3),
        )

        self.file_name_text = ft.Text(
            name_no_ext,
            color=AppTheme.TEXT_PRIMARY,
            size=14,
            weight=ft.FontWeight.W_600,
            no_wrap=True,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.file_path_text = ft.Text(
            self._short_path(job.input_path),
            color=AppTheme.TEXT_MUTED,
            size=11,
            no_wrap=True,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        file_info = ft.Column([
            self.file_name_text,
            self.file_path_text,
            self.size_info_row,
        ], spacing=2, expand=True)

        # ── Format flow (extension badge → arrow → format selector) ──
        self.arrow_icon = ft.Icon(ft.Icons.ARROW_FORWARD, color=AppTheme.TEXT_MUTED, size=14)
        convert_section = ft.Row([
            ext_badge,
            self.arrow_icon,
            self.target_dropdown,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # ── Progress row ─────────────────────────────────────────
        self.progress_row = ft.Container(
            content=self.progress_bar,
            visible=False,
            padding=ft.Padding(left=0, right=0, top=6, bottom=0),
        )

        self._accent_strip = ft.Container(
            width=4,
            bgcolor=f"#40{AppTheme.PRIMARY[1:]}",
        )

        self._card_body = ft.Container(
            padding=ft.Padding(left=14, right=16, top=14, bottom=14),
            bgcolor=AppTheme.SURFACE_2,
            expand=True,
            content=ft.Column([
                ft.Row([
                    self.file_icon_block,
                    file_info,
                    convert_section,
                    self.status_badge,
                    self.delete_btn,
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=14),
                self.progress_row,
            ], spacing=0),
        )

        self.content = ft.Row([
            self._accent_strip,
            self._card_body,
        ], spacing=0)
        self.bgcolor = AppTheme.SURFACE_2
        self.border_radius = 12
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.animate_opacity = ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        self.opacity = 1

    def _apply_thumbnail(self, thumb_path: str):
        self.file_icon_block.content = ft.Image(
            src=thumb_path,
            width=48,
            height=48,
            fit="cover",
            border_radius=10
        )
        self.file_icon_block.bgcolor = None
        self.file_icon_block.padding = None

    def _apply_thumbnail_async(self, thumb_path: str):
        self._apply_thumbnail(thumb_path)
        try:
            self.update()
        except Exception:
            pass

    def _short_path(self, path: str) -> str:
        """Shorten a path to show only last 2 dirs."""
        parts = path.replace('\\', '/').split('/')
        if len(parts) > 3:
            return '…/' + '/'.join(parts[-3:-1]) + '/'
        return '/'.join(parts[:-1]) + '/'

    def _get_output_size_info(self):
        if self.job.status == "Completed" and hasattr(self.job, 'output_path') and os.path.exists(self.job.output_path):
            try:
                out_b = os.path.getsize(self.job.output_path)
                return _format_size(out_b), False
            except Exception:
                pass

        if not self.input_bytes:
            return "—", True

        src_ext = self.ext
        target_ext = (self.job.target_format or "").lower().strip()
        ratio = 1.0

        if self.src_group == 'video':
            if target_ext in ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg']:
                ratio = 0.1
            elif target_ext in ['webm', 'mp4']:
                ratio = 0.85
            elif target_ext in ['gif']:
                ratio = 1.8
        elif self.src_group == 'audio':
            if target_ext in ['mp3', 'm4a', 'aac', 'ogg']:
                ratio = 0.4 if src_ext == 'wav' else 0.9
            elif target_ext in ['wav', 'flac']:
                ratio = 2.5 if src_ext in ['mp3', 'm4a'] else 1.0
        elif self.src_group == 'image':
            if target_ext in ['jpg', 'jpeg', 'webp']:
                ratio = 0.5 if src_ext == 'png' else 0.8
            elif target_ext in ['png', 'bmp', 'tiff']:
                ratio = 1.5 if src_ext in ['jpg', 'jpeg', 'webp'] else 1.0
            elif target_ext == 'ico':
                ratio = 0.2
        elif self.src_group == 'document':
            if target_ext == 'pdf':
                ratio = 1.3
            elif target_ext in ['txt', 'md']:
                ratio = 0.3
        elif self.src_group == 'model3d':
            if target_ext in ['glb', 'gltf']:
                ratio = 0.7
            elif target_ext in ['obj', 'stl', 'ply']:
                ratio = 1.1

        est_bytes = int(self.input_bytes * ratio)
        return f"~{_format_size(est_bytes)}", True

    def _update_size_info(self):
        out_str, is_est = self._get_output_size_info()
        if is_est:
            self.size_info_row.controls = [
                ft.Text(f"Size: {self.input_size_str}", color=AppTheme.TEXT_MUTED, size=11, weight=ft.FontWeight.W_500),
                ft.Text("•", color=AppTheme.TEXT_MUTED, size=10),
                ft.Text(f"Est. {out_str}", color=AppTheme.PRIMARY, size=11, weight=ft.FontWeight.W_600),
            ]
        else:
            self.size_info_row.controls = [
                ft.Text(f"Size: {self.input_size_str}", color=AppTheme.TEXT_MUTED, size=11, weight=ft.FontWeight.W_500),
                ft.Text("→", color=AppTheme.SUCCESS, size=11),
                ft.Text(f"Out: {out_str}", color=AppTheme.SUCCESS, size=11, weight=ft.FontWeight.W_700),
            ]

    def on_format_change(self, e):
        # Use e.control.value — works in both on_change and on_select handlers
        new_fmt = (e.control.value or "").strip().lower()
        print(f"[FORMAT_CHANGE] {self.filename}: {self.job.target_format} -> {new_fmt!r}")
        if not new_fmt:
            return
        self.job.target_format = new_fmt
        name_no_ext = os.path.splitext(self.filename)[0]
        self.job.output_path = os.path.join(
            self.job.output_dir,
            f"{name_no_ext}.{self.job.target_format}"
        )
        print(f"[FORMAT_CHANGE] new output_path: {self.job.output_path}")
        self._update_size_info()
        self.update()

    def update_status(self):
        status = self.job.status
        self._update_size_info()
        if status == "Pending":
            self.progress_row.visible = False
            self._set_badge("Pending", AppTheme.TEXT_MUTED, AppTheme.SURFACE_3)
            self._accent_strip.bgcolor = f"#40{AppTheme.PRIMARY[1:]}"
            self.delete_btn.icon = ft.Icons.CLOSE
            self.delete_btn.icon_color = AppTheme.TEXT_MUTED
            self.delete_btn.tooltip = "Remove"
            self.delete_btn.on_click = lambda _: self.on_remove(self)
        elif status == "Converting":
            self.progress_bar.visible = True
            if hasattr(self.job, 'progress') and self.job.progress > 0 and self.job.progress < 100:
                self.progress_bar.value = self.job.progress / 100.0
                self._set_badge(f"Converting {self.job.progress}%", AppTheme.PRIMARY, AppTheme.SURFACE_VARIANT)
            else:
                self.progress_bar.value = None  # indeterminate
                self._set_badge("Converting…", AppTheme.PRIMARY, AppTheme.SURFACE_VARIANT)
            self.progress_bar.color = AppTheme.PRIMARY
            self.progress_row.visible = True
            self._accent_strip.bgcolor = AppTheme.PRIMARY
        elif status == "Completed":
            self.progress_bar.visible = True
            self.progress_bar.value = 1
            self.progress_bar.color = AppTheme.SUCCESS
            self.progress_row.visible = True
            self._set_badge("Done ✓", AppTheme.SUCCESS, AppTheme.SUCCESS_BG)
            self._accent_strip.bgcolor = AppTheme.SUCCESS
            self.delete_btn.icon = ft.Icons.FOLDER_OPEN
            self.delete_btn.icon_color = AppTheme.PRIMARY
            self.delete_btn.on_click = lambda _: os.startfile(self.job.output_dir)
            self.delete_btn.tooltip = "Open folder"
        elif status == "Failed":
            self.progress_row.visible = False
            self._set_badge("✗ Failed", AppTheme.ERROR, AppTheme.ERROR_BG)
            self._accent_strip.bgcolor = AppTheme.ERROR
        self.update()
        if self.on_status_change:
            self.on_status_change()

    def refresh_colors(self):
        self.target_dropdown.border_color = AppTheme.BORDER
        self.target_dropdown.bgcolor = AppTheme.SURFACE_3
        self.target_dropdown.color = AppTheme.TEXT_PRIMARY
        self.target_dropdown.focused_border_color = AppTheme.PRIMARY
        
        self.file_name_text.color = AppTheme.TEXT_PRIMARY
        self.file_path_text.color = AppTheme.TEXT_MUTED
        self.arrow_icon.color = AppTheme.TEXT_MUTED
        
        self._card_body.bgcolor = AppTheme.SURFACE_2
        
        self.update_status()

    def _set_badge(self, text: str, color: str, bg: str):
        self.status_badge.content = ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=color)
        self.status_badge.bgcolor = bg
        self.status_badge.border_radius = 20
