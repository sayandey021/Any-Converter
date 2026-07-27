import flet as ft
import webbrowser
from src.ui.theme import AppTheme


class AboutView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        self.padding = 0

        # Build UI content
        self.content = self._build_content()

    def _open_url(self, url: str):
        try:
            if self.main_page:
                self.main_page.launch_url(url)
            else:
                webbrowser.open(url)
        except Exception:
            webbrowser.open(url)

    def _create_badge(self, text: str, bg_color=None, text_color=None):
        bg = bg_color or AppTheme.SURFACE_VARIANT
        tc = text_color or AppTheme.TEXT_PRIMARY
        return ft.Container(
            content=ft.Text(text, size=11, weight=ft.FontWeight.W_600, color=tc),
            bgcolor=bg,
            border_radius=6,
            padding=ft.Padding(left=8, right=8, top=4, bottom=4),
            border=ft.Border.all(1, AppTheme.BORDER),
        )

    def _build_category_card(self, title: str, icon: str, inputs: list, exports: list, note: str = None, extra_exports: dict = None):
        input_badges = [self._create_badge(ext, AppTheme.SURFACE_3, AppTheme.TEXT_SECONDARY) for ext in inputs]
        export_badges = [self._create_badge(ext, AppTheme.SURFACE_VARIANT, AppTheme.PRIMARY_LIGHT) for ext in exports]

        card_content = [
            ft.Row([
                ft.Icon(icon, color=AppTheme.PRIMARY, size=20),
                ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=AppTheme.TEXT_PRIMARY),
            ], spacing=10),
            ft.Container(height=12),
            
            # Inputs section
            ft.Text("Supported Inputs", size=12, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_MUTED),
            ft.Container(height=6),
            ft.Row(input_badges, wrap=True, spacing=6, run_spacing=6),
            ft.Container(height=14),

            # Exports section
            ft.Text("Can Be Converted To", size=12, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_MUTED),
            ft.Container(height=6),
            ft.Row(export_badges, wrap=True, spacing=6, run_spacing=6),
        ]

        if extra_exports:
            for label, items in extra_exports.items():
                extra_badges = [self._create_badge(ext, AppTheme.SURFACE_VARIANT, AppTheme.ACCENT) for ext in items]
                card_content.extend([
                    ft.Container(height=8),
                    ft.Text(f"Can Be Converted To ({label})", size=12, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_MUTED),
                    ft.Container(height=6),
                    ft.Row(extra_badges, wrap=True, spacing=6, run_spacing=6),
                ])

        if note:
            card_content.extend([
                ft.Container(height=10),
                ft.Text(f"Note: {note}", size=11, color=AppTheme.TEXT_MUTED, italic=True),
            ])

        return ft.Container(
            content=ft.Column(card_content, spacing=0),
            bgcolor=AppTheme.SURFACE_2,
            border_radius=14,
            padding=18,
            margin=ft.Margin(left=0, top=0, right=16, bottom=0),
            border=ft.Border.all(1, AppTheme.BORDER),
        )

    def _build_hero_section(self):
        # App logo icon
        logo_icon = ft.Container(
            content=ft.Image(
                src="icon.png",
                width=72,
                height=72,
                fit=ft.BoxFit.CONTAIN,
                border_radius=18,
            ),
            width=72,
            height=72,
            border_radius=18,
            alignment=ft.Alignment(0, 0),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=AppTheme.PRIMARY + "66",
                offset=ft.Offset(0, 4)
            ),
        )

        # GitHub button
        github_btn = ft.Container(
            content=ft.Row([
                ft.Text("<>", color=AppTheme.TEXT_PRIMARY, size=14, weight=ft.FontWeight.W_800),
                ft.Text("GitHub", color=AppTheme.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_600),
            ], tight=True, spacing=8),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=20,
            padding=ft.Padding(left=18, right=18, top=10, bottom=10),
            on_click=lambda e: self._open_url("https://github.com/sayandey021"),
            ink=True,
            border=ft.Border.all(1, AppTheme.BORDER),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )

        # LinkedIn button
        linkedin_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LINK, color=AppTheme.PRIMARY_LIGHT, size=16),
                ft.Text("LinkedIn", color=AppTheme.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_600),
            ], tight=True, spacing=8),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=20,
            padding=ft.Padding(left=18, right=18, top=10, bottom=10),
            on_click=lambda e: self._open_url("https://www.linkedin.com/in/sayan-dey021/"),
            ink=True,
            border=ft.Border.all(1, AppTheme.BORDER),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )

        return ft.Container(
            content=ft.Column([
                logo_icon,
                ft.Container(height=16),
                ft.Text("Any Converter", size=30, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY),
                ft.Container(height=2),
                ft.Text("Version 1.0.0", size=14, color=AppTheme.TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Container(height=12),
                ft.Text("Developed by Sayan Dey", size=15, color=AppTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                ft.Container(height=10),
                ft.Text(
                    "A fast and offline file conversion tool for media, documents, archives, data, GIS & 3D models.",
                    size=13, color=AppTheme.TEXT_MUTED, text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Built with Python, Flet, and FFmpeg.",
                    size=12, color=AppTheme.TEXT_MUTED, text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.Row([github_btn, linkedin_btn], alignment=ft.MainAxisAlignment.CENTER, spacing=14),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            bgcolor=AppTheme.SURFACE,
            border_radius=18,
            padding=ft.Padding(left=24, right=24, top=32, bottom=32),
            margin=ft.Margin(left=0, top=0, right=16, bottom=0),
            border=ft.Border.all(1, AppTheme.BORDER),
            alignment=ft.Alignment(0, 0),
        )

    def _build_content(self):
        # Header
        header = ft.Row([
            ft.Text("About Any Converter", size=24, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Categories list data
        categories = [
            {
                "title": "Images",
                "icon": ft.Icons.IMAGE_OUTLINED,
                "inputs": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".heic", ".heif", ".psd", ".ico", ".tiff", ".tif", ".raw", ".cr2", ".nef", ".arw", ".dng", ".avif", ".jxl"],
                "exports": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ico", ".tiff", ".tif", ".avif", ".jxl"],
                "note": ".heic, .heif, .psd, .raw, .cr2, .nef, .arw, .dng are supported as inputs for conversion, but cannot be exported to directly."
            },
            {
                "title": "Video",
                "icon": ft.Icons.VIDEO_LIBRARY_OUTLINED,
                "inputs": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".f4v", ".mxf", ".asf", ".mts", ".m2ts", ".vob", ".ts", ".3gp", ".3g2", ".ogv", ".rm", ".rmvb", ".vro", ".dat", ".mpg", ".mpeg"],
                "exports": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".f4v", ".mxf", ".asf", ".mts", ".m2ts", ".vob", ".ts", ".3gp", ".3g2", ".ogv", ".rm", ".rmvb", ".mpg", ".mpeg"],
                "extra_exports": {
                    "Audio Extraction": [".mp3", ".wav", ".flac", ".m4a", ".aac"]
                }
            },
            {
                "title": "Audio",
                "icon": ft.Icons.AUDIOTRACK_OUTLINED,
                "inputs": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".aiff", ".alac", ".dff", ".dsf", ".mqa", ".mod", ".s3m", ".xm", ".it", ".wma", ".ra", ".bwf", ".amr", ".ac3", ".eac3", ".thd", ".dts", ".dtshd", ".aob"],
                "exports": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".aiff", ".alac", ".wma", ".amr", ".ac3", ".eac3", ".thd", ".dts"],
                "note": ".dff, .dsf, .mqa, .mod, .s3m, .xm, .it, .ra, .bwf, .dtshd are supported as inputs for conversion, but cannot be exported to directly due to encoder limitations."
            },
            {
                "title": "Documents",
                "icon": ft.Icons.DESCRIPTION_OUTLINED,
                "inputs": [".doc", ".docx", ".docm", ".dot", ".dotx", ".dotm", ".rtf", ".txt", ".log", ".odt", ".mht", ".html", ".htm", ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".ppt", ".pptx", ".pptm", ".pps", ".odp"],
                "exports": [".pdf"],
                "note": "Requires Microsoft Office to be installed for legacy formats. Falls back to internal open-source converters for modern formats."
            },
            {
                "title": "Data & Config",
                "icon": ft.Icons.DATA_OBJECT_OUTLINED,
                "inputs": [".json", ".yaml", ".yml", ".csv", ".xml"],
                "exports": [".json", ".yaml", ".yml", ".csv", ".xml", ".pdf"],
                "note": "Converts structured data bidirectionally between JSON, YAML, CSV, and XML formats, or exports to PDF."
            },
            {
                "title": "PDFs & E-Books",
                "icon": ft.Icons.MENU_BOOK_OUTLINED,
                "inputs": [".pdf", ".epub", ".mobi", ".azw3", ".azw", ".iba", ".djvu", ".djv"],
                "exports": [".png", ".jpg", ".jpeg", ".webp", ".pdf"],
                "note": "Converts e-books directly to PDF or extracts each page as a high-resolution image."
            },
            {
                "title": "3D & CAD Models",
                "icon": ft.Icons.VIEW_IN_AR_OUTLINED,
                "inputs": [".obj", ".stl", ".ply", ".glb", ".gltf", ".off", ".dae", ".fbx", ".step", ".stp", ".iges", ".igs", ".dxf", ".dwg", ".3mf"],
                "exports": [".obj", ".stl", ".ply", ".glb", ".gltf", ".off", ".dae"],
                "note": "Supports 3D meshes and CAD formats (STEP, IGES, DXF, DWG, 3MF). .fbx is supported as an input format."
            },
            {
                "title": "Databases & SQL",
                "icon": ft.Icons.STORAGE_OUTLINED,
                "inputs": [".sql", ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"],
                "exports": [".sql", ".sqlite", ".json", ".csv", ".xml", ".yaml"],
                "note": "Converts SQLite, SQL dumps, and MS Access databases into structured schemas or data files."
            },
            {
                "title": "GIS & Geospatial",
                "icon": ft.Icons.MAP_OUTLINED,
                "inputs": [".geojson", ".kml", ".kmz", ".gpx", ".shp"],
                "exports": [".geojson", ".kml", ".gpx", ".csv", ".json"],
                "note": "Converts spatial feature collections, GPS tracks, Google Earth KML/KMZ, and Shapefiles."
            },
            {
                "title": "Archives & Disk Images",
                "icon": ft.Icons.FOLDER_ZIP_OUTLINED,
                "inputs": [".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".iso", ".img", ".mds", ".mdf"],
                "exports": [".zip", ".7z", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz", "folder"],
                "note": "Extracts and converts compressed archives, ISO optical images, and MDF disk images directly to a folder or archive format."
            },
            {
                "title": "Subtitles",
                "icon": ft.Icons.SUBTITLES_OUTLINED,
                "inputs": [".srt", ".vtt", ".ass", ".ssa", ".sub", ".scc"],
                "exports": [".srt", ".vtt", ".ass", ".sub", ".scc", ".txt"],
                "note": "Converts subtitle files bidirectionally with timestamp alignment."
            },
            {
                "title": "Fonts",
                "icon": ft.Icons.FONT_DOWNLOAD_OUTLINED,
                "inputs": [".ttf", ".otf", ".woff", ".woff2"],
                "exports": [".ttf", ".otf", ".woff", ".woff2"],
                "note": "Converts desktop and web font formats natively."
            },
            {
                "title": "Vector Graphics",
                "icon": ft.Icons.CATEGORY_OUTLINED,
                "inputs": [".svg"],
                "exports": [".png", ".jpg", ".jpeg", ".pdf", ".svg"]
            },
        ]

        category_cards = [
            self._build_category_card(
                c["title"], c["icon"], c["inputs"], c["exports"], c.get("note"), c.get("extra_exports")
            )
            for c in categories
        ]

        # Section divider / title for categories
        formats_title = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.GRID_VIEW_ROUNDED, color=AppTheme.PRIMARY, size=20),
                ft.Text("Supported Formats & Categories", size=18, weight=ft.FontWeight.W_700, color=AppTheme.TEXT_PRIMARY),
            ], spacing=10),
            padding=ft.Padding(left=0, right=0, top=10, bottom=4),
            margin=ft.Margin(left=0, top=0, right=16, bottom=0),
        )

        scrollable_list = ft.Column(
            controls=[
                self._build_hero_section(),
                ft.Container(height=24),
                formats_title,
                ft.Container(height=8),
                *category_cards,
            ],
            spacing=12,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Column([
            header,
            ft.Container(height=16),
            ft.Container(content=scrollable_list, expand=True, padding=ft.Padding(left=0, top=0, right=0, bottom=24)),
        ], spacing=0, expand=True)
