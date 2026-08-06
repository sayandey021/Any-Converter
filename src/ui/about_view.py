import flet as ft
import webbrowser
from src.ui.theme import AppTheme


class AboutView(ft.Container):
    def __init__(self, page: ft.Page, on_back=None):
        super().__init__()
        self.main_page = page
        self.on_back = on_back
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
        inputs_str = ", ".join([e.lstrip(".") for e in inputs])
        exports_str = ", ".join([e.lstrip(".") for e in exports])

        card_content = [
            ft.Row([
                ft.Icon(icon, color=AppTheme.PRIMARY, size=18),
                ft.Text(title, size=14, weight=ft.FontWeight.W_700, color=AppTheme.TEXT_PRIMARY),
            ], spacing=8),
            ft.Container(height=4),
            ft.Row([
                ft.Text("Inputs: ", size=12, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_MUTED),
                ft.Text(inputs_str, size=12, color=AppTheme.TEXT_SECONDARY, expand=True),
            ], spacing=4),
            ft.Row([
                ft.Text("Exports: ", size=12, weight=ft.FontWeight.W_600, color=AppTheme.PRIMARY_LIGHT),
                ft.Text(exports_str, size=12, color=AppTheme.TEXT_SECONDARY, expand=True),
            ], spacing=4),
        ]

        if note:
            card_content.extend([
                ft.Container(height=4),
                ft.Text(note, size=11, color=AppTheme.TEXT_MUTED, italic=True),
            ])

        return ft.Container(
            content=ft.Column(card_content, spacing=2),
            bgcolor=AppTheme.SURFACE_2,
            border_radius=10,
            padding=12,
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
        )

        # GitHub button
        github_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CODE_ROUNDED, color=AppTheme.TEXT_PRIMARY, size=16),
                ft.Text("GitHub", color=AppTheme.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_700),
            ], tight=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=AppTheme.SURFACE_3,
            border=ft.Border.all(1, AppTheme.BORDER),
            border_radius=20,
            padding=ft.Padding(left=18, right=18, top=10, bottom=10),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color="#25000000", offset=ft.Offset(0, 3)),
            ink=True,
            on_click=lambda e: self._open_url("https://github.com/sayandey021"),
        )

        # LinkedIn button
        linkedin_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PUBLIC_ROUNDED, color=AppTheme.PRIMARY, size=16),
                ft.Text("LinkedIn", color=AppTheme.TEXT_PRIMARY, size=13, weight=ft.FontWeight.W_700),
            ], tight=True, spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=AppTheme.SURFACE_3,
            border=ft.Border.all(1, AppTheme.BORDER),
            border_radius=20,
            padding=ft.Padding(left=18, right=18, top=10, bottom=10),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color="#25000000", offset=ft.Offset(0, 3)),
            ink=True,
            on_click=lambda e: self._open_url("https://www.linkedin.com/in/sayan-dey021/"),
        )

        return ft.Container(
            content=ft.Column([
                logo_icon,
                ft.Container(height=16),
                ft.Text("Any Converter", size=30, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY),
                ft.Container(height=2),
                ft.Text("Version 1.5.0", size=14, color=AppTheme.TEXT_MUTED, weight=ft.FontWeight.W_500),
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
            padding=ft.Padding(left=16, right=16, top=16, bottom=16),
            alignment=ft.Alignment(0, 0),
        )

    def _build_content(self):
        # Header
        title_text = ft.Text("About Any Converter", size=24, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY)
        if self.on_back:
            header_left = ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=AppTheme.TEXT_PRIMARY,
                    tooltip="Back to Convert",
                    on_click=lambda e: self.on_back()
                ),
                title_text
            ], spacing=10)
            
            header = ft.Row([
                header_left
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Categories list data
        categories = [
            {
                "title": "Images",
                "icon": ft.Icons.IMAGE_OUTLINED,
                "inputs": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".heic", ".heif", ".psd", ".ico", ".indd", ".idml", ".raw", ".cr2", ".nef", ".arw", ".dng", ".raf", ".pef", ".tga", ".pcx", ".pbm", ".pgm", ".ppm", ".exr", ".dpx"],
                "exports": [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".ico", ".tiff", ".tif", ".avif", ".jxl", ".heic", ".heif", ".tga", ".pcx", ".ppm", ".pgm", ".pbm", ".pnm", ".icns", ".sgi", ".dds", ".dib", ".xbm", ".xpm", ".cur"],
                "note": ".psd, .indd, .idml, .raw, .cr2, .nef, .arw, .dng are supported as inputs for conversion by extracting image data or embedded previews."
            },
            {
                "title": "Video",
                "icon": ft.Icons.VIDEO_LIBRARY_OUTLINED,
                "inputs": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".f4v", ".3gp", ".3g2", ".m4v", ".mxf", ".asf", ".mts", ".m2ts", ".ts", ".m2v", ".m1v", ".mpg", ".mpeg", ".vob", ".vro", ".wtv", ".dvr-ms", ".swf", ".m3u8", ".m3u", ".m4s", ".mpd", ".fmp4", ".cmfv", ".cmfa", ".f4f", ".ism", ".ismc", ".ismv", ".isma", ".sdp", ".yuv", ".divx", ".xvid", ".nut", ".mvi", ".roq", ".svi", ".ivf", ".h264", ".h265", ".hevc", ".amv", ".bik", ".bk2"],
                "exports": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv", ".f4v", ".mxf", ".asf", ".mts", ".m2ts", ".vob", ".ts", ".3gp", ".3g2", ".ogv", ".rm", ".rmvb", ".mpg", ".mpeg", ".m3u8", ".m3u", ".m4s", ".mpd", ".fmp4", ".cmfv", ".cmfa", ".f4f", ".ismv", ".isma", ".m4v", ".nut", ".m1v", ".m2v", ".h264", ".h265", ".hevc", ".yuv"],
                "extra_exports": {
                    "Audio Extraction": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".opus", ".mka", ".ogg"]
                },
                "note": "Supports video files, HLS playlists (.m3u8/.m3u), DASH (.mpd/.m4s), CMAF (.cmfv/.cmfa), Smooth Streaming (.ism/.ismv), SDP (.sdp), and AVCHD/Blu-ray streams (.m2ts/.mts)."
            },
            {
                "title": "Audio",
                "icon": ft.Icons.AUDIOTRACK_OUTLINED,
                "inputs": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".mka", ".aiff", ".alac", ".ape", ".wv", ".tta", ".tak", ".dsd", ".dff", ".dsf", ".mqa", ".wma", ".amr", ".awb", ".spx", ".gsm", ".qcp", ".voc", ".ac3", ".eac3", ".thd", ".dts", ".dtshd", ".mod", ".s3m", ".xm", ".it", ".ra", ".bwf", ".aob", ".oga", ".au", ".snd", ".mp2", ".mp1", ".caf", ".mpc", ".oma", ".omg", ".m4b", ".m4r"],
                "exports": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".aiff", ".alac", ".wma", ".amr", ".ac3", ".eac3", ".thd", ".dts", ".opus", ".oga", ".voc", ".au", ".snd", ".mp2", ".mp1", ".caf", ".spx", ".gsm", ".tta", ".ape", ".wv", ".mka"],
            },
            {
                "title": "3D & CAD Models",
                "icon": ft.Icons.VIEW_IN_AR_OUTLINED,
                "inputs": [
                    ".obj", ".stl", ".ply", ".glb", ".gltf", ".off", ".dae", ".fbx", 
                    ".step", ".stp", ".iges", ".igs", ".dxf", ".dwg", ".3mf", ".scad", ".dwf", ".3ds",
                    ".blend", ".x", ".lwo", ".lws", ".md5mesh", ".smd", ".vta", ".ogex", ".3d", ".b3d",
                    ".q3d", ".q3s", ".nff", ".ter", ".mdl", ".xml", ".ifc", ".x3d", ".x3db", ".csm",
                    ".bvh", ".ase", ".cob", ".scn", ".ac", ".ms3d", ".mqo", ".ndo", ".irr", ".irrmesh", ".pmx"
                ],
                "exports": [".obj", ".stl", ".ply", ".glb", ".gltf", ".off", ".dae", ".fbx", ".x", ".stp"],
            },
            {
                "title": "Documents",
                "icon": ft.Icons.DESCRIPTION_OUTLINED,
                "inputs": [".doc", ".docx", ".docm", ".dot", ".dotx", ".dotm", ".rtf", ".txt", ".log", ".odt", ".mht", ".html", ".htm", ".wpd", ".wps", ".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".sxc", ".ppt", ".pptx", ".pptm", ".pps", ".odp", ".key", ".pages", ".numbers", ".xps", ".oxps", ".vsd", ".vsdx", ".pub", ".mpp"],
                "exports": [".pdf"],
                "note": "Automatically cascades through Microsoft Office, LibreOffice, and WPS Office if any engine is missing or fails for legacy document formats."
            },
            {
                "title": "Data & Config",
                "icon": ft.Icons.DATA_OBJECT_OUTLINED,
                "inputs": [".json", ".yaml", ".yml", ".csv", ".xml", ".vcf", ".ics"],
                "exports": [".json", ".yaml", ".yml", ".csv", ".xml", ".pdf"],
            },
            {
                "title": "PDFs & E-Books",
                "icon": ft.Icons.MENU_BOOK_OUTLINED,
                "inputs": [".pdf", ".epub", ".mobi", ".azw3", ".azw", ".iba", ".djvu", ".djv", ".cbr", ".cbz", ".cb7", ".cbt", ".chm"],
                "exports": [".png", ".jpg", ".jpeg", ".webp", ".pdf"],
            },
            {
                "title": "Databases & SQL",
                "icon": ft.Icons.STORAGE_OUTLINED,
                "inputs": [".sql", ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb", ".json", ".yaml", ".yml", ".csv", ".xml", ".vcf", ".ics"],
                "exports": [".sql", ".sqlite", ".json", ".csv", ".xml", ".yaml", ".pdf"],
            },
            {
                "title": "GIS & Geospatial",
                "icon": ft.Icons.MAP_OUTLINED,
                "inputs": [".geojson", ".kml", ".kmz", ".gpx", ".shp"],
                "exports": [".geojson", ".kml", ".gpx", ".csv", ".json"],
            },
            {
                "title": "Archives & Disk Images",
                "icon": ft.Icons.FOLDER_ZIP_OUTLINED,
                "inputs": [".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".iso", ".img", ".mds", ".mdf", ".cab"],
                "exports": [".zip", ".7z", ".tar", ".tar.gz", ".tar.bz2", ".tar.xz", "folder"],
            },
            {
                "title": "Subtitles",
                "icon": ft.Icons.SUBTITLES_OUTLINED,
                "inputs": [".srt", ".vtt", ".ass", ".ssa", ".sub", ".scc"],
                "exports": [".srt", ".vtt", ".ass", ".sub", ".scc", ".txt"],
            },
            {
                "title": "Fonts",
                "icon": ft.Icons.FONT_DOWNLOAD_OUTLINED,
                "inputs": [".ttf", ".otf", ".woff", ".woff2", ".eot", ".dfont"],
                "exports": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
            },
            {
                "title": "Vector Graphics",
                "icon": ft.Icons.CATEGORY_OUTLINED,
                "inputs": [".svg", ".ai", ".eps", ".ps", ".cdr", ".xps", ".oxps"],
                "exports": [".png", ".jpg", ".jpeg", ".webp", ".pdf", ".svg"],
                "note": ".ai vector files are supported via PDF layers; .eps, .ps, and CorelDRAW (.cdr) files are rendered natively via CLI tools (LibreOffice/Inkscape) or embedded preview streams. .xps and .oxps documents are converted directly as vector page sheets."
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

        controls = []
        if self.on_back:
            controls.extend([header, ft.Container(height=16)])
        controls.append(ft.Container(content=scrollable_list, expand=True, padding=ft.Padding(left=0, top=0, right=0, bottom=0)))

        return ft.Column(controls, spacing=0, expand=True)
