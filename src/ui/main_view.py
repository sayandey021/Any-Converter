import flet as ft
import os
from src.ui.theme import AppTheme
from src.ui.conversion_card import ConversionCard
from src.ui.settings_view import SettingsView
from src.ui.about_view import AboutView
from src.backend.converter import ConverterManager


class MainView(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        self.padding = 0
        self.converter_manager = ConverterManager()
        self.cards = []
        self._dropzone_hover = False
        self.active_tab = "Convert"
        self.total_converted = 0

        # ── File Picker (Removed due to custom flet_view client missing support) ──

        # ── Empty state (shown when no files) ────────────────────
        self._empty_state = self._build_empty_state()

        # ── File queue list ──────────────────────────────────────
        self.list_view = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding(left=0, right=0, top=4, bottom=16),
        )

        # ── Convert All button ────────────────────────────────────
        self.convert_all_btn = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT, color=ft.Colors.WHITE, size=18),
                ft.Text("Convert All", color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_700, size=14),
            ], tight=True, spacing=6),
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: AppTheme.PRIMARY,
                    ft.ControlState.HOVERED: AppTheme.PRIMARY_HOVER,
                    ft.ControlState.DISABLED: AppTheme.SURFACE_VARIANT,
                },
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=20, right=20, top=12, bottom=12),
                elevation=0,
            ),
            on_click=self.convert_all,
            disabled=True,
        )

        # ── Clear All button ─────────────────────────────────────
        self.clear_btn = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE_SWEEP_OUTLINED, color=AppTheme.ERROR, size=16),
                ft.Text("Clear All", color=AppTheme.ERROR, size=14),
            ], tight=True, spacing=6),
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, AppTheme.ERROR),
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=16, right=16, top=12, bottom=12),
            ),
            on_click=self.clear_all,
            visible=False,
        )

        # ── File count badge ──────────────────────────────────────
        self.file_count_text = ft.Text(
            "0 files queued",
            size=13,
            color=AppTheme.TEXT_MUTED,
            weight=ft.FontWeight.W_500,
        )

        # ── Drop Zone ─────────────────────────────────────────────
        self.dropzone = self._build_dropzone()

        # ── Queue header ─────────────────────────────────────────
        self.queue_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.QUEUE, color=AppTheme.PRIMARY, size=18),
                        ft.Text("Conversion Queue", size=16, weight=ft.FontWeight.W_700,
                                color=AppTheme.TEXT_PRIMARY),
                        self.file_count_text,
                    ], spacing=10),
                    ft.Row([
                        self.clear_btn,
                        ft.Container(width=8),
                        self.convert_all_btn,
                    ], spacing=0),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=ft.Padding(left=0, right=0, top=0, bottom=12),
            visible=False,
        )

        # ── Queue container (list + empty state) ─────────────────
        self.queue_body = ft.Container(
            content=self._empty_state,
            expand=True,
        )

        # ── Views ─────────────────────────────────────────────────
        self.convert_view = ft.Column([
            # Top bar
            self._build_topbar(),
            ft.Container(height=20),
            # Drop zone
            self.dropzone,
            ft.Container(height=20),
            # Queue header
            self.queue_section,
            # Queue body (expands)
            ft.Container(
                content=self.list_view,
                expand=True,
            ),
        ], spacing=0, expand=True)

        self._history_view = None
        self._settings_view = None
        self._about_view = None

        self.main_content_container = ft.Container(
            content=self.convert_view,
            expand=True,
            padding=ft.Padding(left=28, right=28, top=24, bottom=24),
        )

        # ── Sidebar (left) ─────────────────────────────────────────
        self.sidebar_container = self._build_sidebar()
        self.root_divider = ft.VerticalDivider(width=1, color=AppTheme.BORDER)

        # ── Root layout ───────────────────────────────────────────
        self.content = ft.Row([
            self.sidebar_container,
            self.root_divider,
            self.main_content_container,
        ], spacing=0, expand=True)

    # ─────────────────────────────────────────────────────────────
    # Builder helpers
    # ─────────────────────────────────────────────────────────────

    def _build_topbar(self) -> ft.Control:
        supported_text = ft.Text(
            "Fast, offline file converter for media, documents, 3D models & more",
            size=12, color=AppTheme.TEXT_MUTED,
        )
        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Any Converter", size=26, weight=ft.FontWeight.W_800,
                            color=AppTheme.TEXT_PRIMARY),
                    supported_text,
                ], spacing=3),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=0)

    def _create_nav_item(self, icon, label, active=False):
        color = AppTheme.PRIMARY if active else AppTheme.TEXT_SECONDARY
        bg = AppTheme.SURFACE_VARIANT if active else ft.Colors.TRANSPARENT
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=18),
                ft.Text(label, color=color, size=13, weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL),
            ], spacing=10),
            bgcolor=bg,
            border_radius=10,
            padding=ft.Padding(left=14, right=14, top=10, bottom=10),
            ink=True,
            on_click=lambda e, l=label: self._switch_tab(l)
        )

    def _build_sidebar(self) -> ft.Control:
        logo_section = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Image(
                        src="icon.png",
                        width=36,
                        height=36,
                        fit=ft.BoxFit.CONTAIN,
                        border_radius=10,
                    ),
                    width=36, height=36,
                    border_radius=10,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text("AnyConv", size=16, weight=ft.FontWeight.W_800,
                        color=AppTheme.TEXT_PRIMARY),
            ], spacing=10),
            padding=ft.Padding(left=16, right=16, top=20, bottom=16),
        )

        self.nav_convert = self._create_nav_item(ft.Icons.SWAP_HORIZ_ROUNDED, "Convert", True)
        self.nav_history = self._create_nav_item(ft.Icons.HISTORY, "History", False)
        self.nav_settings = self._create_nav_item(ft.Icons.SETTINGS_OUTLINED, "Settings", False)
        self.nav_about = self._create_nav_item(ft.Icons.INFO_OUTLINED, "About", False)

        nav_items = ft.Column([
            self.nav_convert,
            self.nav_history,
            self.nav_settings,
            self.nav_about,
        ], spacing=4)

        self.stat_converted_text = ft.Text("0 files", color=AppTheme.TEXT_SECONDARY, size=12, weight=ft.FontWeight.W_600)
        self.stat_queue_text = ft.Text("0 files", color=AppTheme.TEXT_SECONDARY, size=12, weight=ft.FontWeight.W_600)

        # Stats section
        stats = ft.Container(
            content=ft.Column([
                ft.Divider(color=AppTheme.BORDER, height=1),
                ft.Container(height=12),
                ft.Text("Session Stats", size=11, color=AppTheme.TEXT_MUTED,
                         weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                self._stat_row(ft.Icons.CHECK_CIRCLE_OUTLINE, "Converted", self.stat_converted_text),
                ft.Container(height=6),
                self._stat_row(ft.Icons.BOLT, "In Queue", self.stat_queue_text),
            ], spacing=0),
            padding=ft.Padding(left=16, right=16, top=0, bottom=16),
        )

        return ft.Container(
            content=ft.Column([
                logo_section,
                ft.Container(
                    content=nav_items,
                    padding=ft.Padding(left=8, right=8, top=0, bottom=0),
                ),
                ft.Container(expand=True),
                stats,
            ], spacing=0, expand=True),
            width=200,
            bgcolor=AppTheme.SURFACE,
        )

    def _stat_row(self, icon, label, value_control):
        return ft.Row([
            ft.Icon(icon, color=AppTheme.TEXT_MUTED, size=14),
            ft.Text(label, color=AppTheme.TEXT_MUTED, size=12),
            ft.Container(expand=True),
            value_control,
        ], spacing=6)

    def _build_dropzone(self) -> ft.Container:
        self._dz_icon = ft.Icon(ft.Icons.CLOUD_UPLOAD_OUTLINED, size=52, color=AppTheme.PRIMARY)
        self._dz_title = ft.Text(
            "Drop files here to convert",
            size=18, weight=ft.FontWeight.W_700,
            color=AppTheme.TEXT_PRIMARY,
        )
        self._dz_sub = ft.Text(
            "or click to browse — supports video, audio & image formats",
            size=12, color=AppTheme.TEXT_SECONDARY,
        )
        self._dz_badge = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=AppTheme.PRIMARY, size=14),
                ft.Text("Browse Files", color=AppTheme.PRIMARY, size=13,
                         weight=ft.FontWeight.W_600),
            ], spacing=6, tight=True),
            bgcolor=AppTheme.SURFACE_VARIANT,
            border_radius=20,
            padding=ft.Padding(left=16, right=16, top=8, bottom=8),
            on_click=self._open_picker,
        )

        inner = ft.Column([
            self._dz_icon,
            self._dz_title,
            self._dz_sub,
            ft.Container(height=4),
            self._dz_badge,
        ], alignment=ft.MainAxisAlignment.CENTER,
           horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)

        dz = ft.Container(
            content=inner,
            height=200,
            border_radius=16,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=[AppTheme.SURFACE_2, AppTheme.SURFACE_3],
            ),
            border=None,
            on_click=self._open_picker,
            ink=True,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
        )
        self._dz_container = dz
        
        # Native Flet client does not support flet_dropzone (requires custom compiled Flutter client)
        return dz

    def _on_dropzone_entered(self, e):
        self._dz_container.border = ft.Border.all(2, AppTheme.PRIMARY)
        self._dz_container.update()

    def _on_dropzone_exited(self, e):
        self._dz_container.border = None
        self._dz_container.update()

    def _on_dropzone_dropped(self, e):
        self._dz_container.border = None
        self._dz_container.update()
        if hasattr(e, 'files') and e.files:
            print(f"[DEBUG] Dropzone dropped files: {e.files}")
            class DroppedFile:
                def __init__(self, path):
                    self.path = path
                    self.name = os.path.basename(path)
            files = [DroppedFile(p) for p in e.files]
            self._process_files(files)

    def _build_empty_state(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=AppTheme.TEXT_MUTED),
                ft.Text("No files queued yet", size=15, color=AppTheme.TEXT_MUTED,
                        weight=ft.FontWeight.W_500),
                ft.Text("Add files using the drop zone above", size=12,
                        color=AppTheme.TEXT_MUTED),
            ], alignment=ft.MainAxisAlignment.CENTER,
               horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            alignment=ft.Alignment(0, 0),
            expand=True,
            padding=ft.Padding(left=0, right=0, top=40, bottom=40),
        )
    def _build_history_view(self) -> ft.Control:
        from src.backend.history_manager import HistoryManager
        records = HistoryManager().get_history()
        
        if not records:
            content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.HISTORY, size=48, color=AppTheme.TEXT_MUTED),
                    ft.Text("No history yet", size=15, color=AppTheme.TEXT_MUTED, weight=ft.FontWeight.W_500),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                expand=True, alignment=ft.Alignment(0, 0),
            )
        else:
            list_controls = [self._build_history_card(r) for r in records]
            content = ft.ListView(
                controls=list_controls,
                expand=True,
                spacing=8,
                padding=ft.Padding(left=0, right=16, top=10, bottom=16),
            )
            
        header = ft.Row([
            ft.Text("History", size=26, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY),
            ft.TextButton(
                "Clear History",
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=AppTheme.ERROR,
                on_click=self._clear_history,
                visible=len(records) > 0,
                style=ft.ButtonStyle(color=AppTheme.ERROR)
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
        return ft.Column([
            header,
            ft.Container(height=10),
            ft.Container(content, expand=True)
        ], spacing=0, expand=True)

    def _build_history_card(self, record) -> ft.Control:
        filename = record.get("filename", "Unknown")
        target_fmt = record.get("target_format", "").upper()
        status = record.get("status", "Unknown")
        time_str = record.get("timestamp", "")
        out_path = record.get("output_path", "")
        
        try:
            dt = __import__('datetime').datetime.fromisoformat(time_str)
            time_display = dt.strftime("%b %d, %H:%M")
        except:
            time_display = time_str
            
        color = AppTheme.SUCCESS if status == "Completed" else AppTheme.ERROR
        bg_color = AppTheme.SUCCESS_BG if status == "Completed" else AppTheme.ERROR_BG
        icon = ft.Icons.CHECK_CIRCLE if status == "Completed" else ft.Icons.ERROR
        
        def open_folder(e):
            if out_path and __import__('os').path.exists(__import__('os').path.dirname(out_path)):
                __import__('os').startfile(__import__('os').path.dirname(out_path))

        def remove_record(e):
            from src.backend.history_manager import HistoryManager
            HistoryManager().remove_record(record)
            self.history_view.content = self._build_history_view()
            self.update()
                
        actions = []
        if status == "Completed" and out_path:
            actions.append(ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                icon_color=AppTheme.PRIMARY,
                tooltip="Open Folder",
                on_click=open_folder
            ))
            
        actions.append(ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=AppTheme.ERROR,
            icon_size=18,
            tooltip="Remove from history",
            on_click=remove_record
        ))
            
        from src.backend.thumbnail_manager import get_thumbnail
        input_path = record.get("input_path", "")
        thumb_path = get_thumbnail(input_path) if input_path and os.path.exists(input_path) else None
        
        if thumb_path:
            file_icon = ft.Container(
                content=ft.Image(src=thumb_path, width=32, height=32, fit="cover", border_radius=6),
                width=32, height=32,
            )
        else:
            file_icon = ft.Container(
                content=ft.Icon(icon, color=color, size=20),
                width=32, height=32,
                alignment=ft.Alignment(0, 0)
            )
            
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    file_icon,
                    ft.Column([
                        ft.Text(filename, size=14, weight=ft.FontWeight.W_600, color=AppTheme.TEXT_PRIMARY),
                        ft.Text(f"Target: {target_fmt} • {time_display}", size=11, color=AppTheme.TEXT_MUTED),
                    ], spacing=2)
                ], spacing=12),
                ft.Row(actions)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=AppTheme.SURFACE_2,
            border_radius=10,
            padding=12
        )

    def _clear_history(self, e):
        from src.backend.history_manager import HistoryManager
        HistoryManager().clear_history()
        self.history_view.content = self._build_history_view()
        self.update()
    # ─────────────────────────────────────────────────────────────
    # Event handlers
    # ─────────────────────────────────────────────────────────────

    def _switch_tab(self, label):
        if self.active_tab == label: return
        self.active_tab = label
        
        # update nav items visuals
        for nav, l in [(self.nav_convert, "Convert"), (self.nav_history, "History"), (self.nav_settings, "Settings"), (self.nav_about, "About")]:
            active = (l == label)
            color = AppTheme.PRIMARY if active else AppTheme.TEXT_SECONDARY
            bg = AppTheme.SURFACE_VARIANT if active else ft.Colors.TRANSPARENT
            nav.bgcolor = bg
            nav.content.controls[0].color = color
            nav.content.controls[1].color = color
            nav.content.controls[1].weight = ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL
            try:
                nav.update()
            except RuntimeError:
                pass  # Not yet attached to page (e.g. during rebuild)
            
        # update view
        if label == "Convert":
            self.main_content_container.content = self.convert_view
        elif label == "History":
            if self._history_view is None:
                self._history_view = ft.Container(content=self._build_history_view(), expand=True)
            else:
                self._history_view.content = self._build_history_view()
            self.main_content_container.content = self._history_view
        elif label == "Settings":
            if self._settings_view is None:
                self._settings_view = SettingsView(self.main_page)
            self.main_content_container.content = self._settings_view
        elif label == "About":
            if self._about_view is None:
                self._about_view = AboutView(self.main_page)
            self.main_content_container.content = self._about_view
            
        try:
            self.main_content_container.update()
        except RuntimeError:
            pass  # Not yet attached to page (e.g. during rebuild)

    async def _open_picker(self, e):
        print("[DEBUG] Dropzone clicked! Opening file picker...")
        try:
            import tkinter as tk
            from tkinter import filedialog
            from src.ui.conversion_card import FORMAT_GROUPS
            
            # Use tkinter for file picking since custom flet_view lacks FilePicker
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # Build list of all supported extensions for the picker
            all_exts = []
            for exts in FORMAT_GROUPS.values():
                all_exts.extend([f"*.{ext}" for ext in exts])
            all_exts_str = ";".join(all_exts)
            
            file_paths = filedialog.askopenfilenames(
                title="Select Files to Convert",
                filetypes=[("Supported Files", all_exts_str), ("All Files", "*.*")]
            )
            
            root.destroy()
            
            if not file_paths:
                return
                
            class PickedFile:
                def __init__(self, path):
                    self.path = path
                    self.name = os.path.basename(path)
                    
            files = [PickedFile(p) for p in file_paths]
            print(f"[DEBUG] File picker returned: {[f.name for f in files]}")
            self._process_files(files)
        except Exception as ex:
            print(f"[ERROR] Failed to open file picker: {ex}")

    def _process_files(self, files):
        from src.ui.conversion_card import _get_format_group
        for f in files:
            ext = os.path.splitext(f.name)[1].lower().lstrip('.')
            if _get_format_group(ext) == 'other':
                print(f"[WARN] Ignored unsupported file format: {f.name}")
                continue
            
            # Smart default target format
            if ext in ['mkv', 'avi', 'mov', 'webm', 'wmv', 'flv', 'f4v', 'mxf', 'asf', 'mts', 'm2ts', 'vob', 'ts', '3gp', '3g2', 'ogv', 'rm', 'rmvb', 'vro', 'dat', 'mpg', 'mpeg']:
                target = 'mp4'
            elif ext in ['mp4']:
                target = 'mkv'
            elif ext in ['wav', 'flac', 'm4a', 'aac', 'ogg', 'aiff', 'alac', 'dff', 'dsf', 'mqa', 'mod', 's3m', 'xm', 'it', 'wma', 'ra', 'bwf', 'amr', 'ac3', 'eac3', 'thd', 'dts', 'dtshd', 'aob']:
                target = 'mp3'
            elif ext in ['mp3']:
                target = 'wav'
            elif ext in ['jpg', 'jpeg', 'webp', 'bmp', 'heic', 'heif', 'psd', 'tiff', 'tif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'avif', 'jxl']:
                target = 'png'
            elif ext == 'png':
                target = 'jpg'
            elif ext in ['glb', 'fbx']:
                target = 'obj'
            elif ext == 'gif':
                target = 'mp4'
            elif ext in ['md']:
                target = 'html'
            elif ext in ['pdf', 'epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv']:
                if ext in ['epub', 'mobi', 'azw3', 'azw', 'iba', 'djvu', 'djv']:
                    target = 'pdf'
                else:
                    target = 'png'
            elif ext in ['csv', 'xml', 'yaml', 'yml']:
                target = 'json'
            elif ext in ['json']:
                target = 'yaml'
            elif ext in [
                'doc', 'docx', 'docm', 'dot', 'dotx', 'dotm', 'rtf', 'txt', 'log', 'odt', 'mht', 'html', 'htm',
                'xls', 'xlsx', 'xlsm', 'xlsb', 'ods',
                'ppt', 'pptx', 'pptm', 'pps', 'odp'
            ]:
                target = 'pdf'
            elif ext in ['obj', 'stl', 'ply', 'off', 'dae', 'fbx', 'step', 'stp', 'iges', 'igs', 'dxf', 'dwg', '3mf']:
                target = 'glb'
            elif ext in ['glb', 'gltf']:
                target = 'obj'
            elif ext in ['sql', 'db', 'sqlite', 'sqlite3', 'mdb', 'accdb']:
                target = 'sqlite' if ext == 'sql' else 'sql'
            elif ext in ['geojson', 'kml', 'kmz', 'gpx', 'shp']:
                target = 'geojson' if ext in ['kml', 'kmz', 'gpx', 'shp'] else 'kml'
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz', 'tgz', 'bz2', 'tbz2', 'xz', 'txz', 'iso', 'img', 'mds', 'mdf']:
                target = '7z' if ext == 'zip' else 'zip'
            elif ext in ['srt', 'vtt', 'ass', 'ssa', 'sub', 'scc']:
                target = 'vtt' if ext == 'srt' else 'srt'
            elif ext in ['ttf', 'otf', 'woff', 'woff2']:
                target = 'woff2' if ext in ['ttf', 'otf', 'woff'] else 'ttf'
            elif ext in ['svg', 'ico']:
                target = 'png'
            else:
                target = 'mp4'

            job = self.converter_manager.add_job(f.path, target)
            card = ConversionCard(job, self.remove_card, self._refresh_ui)
            self.cards.append(card)
            self.list_view.controls.append(card)

        self._refresh_ui()


    def remove_card(self, card):
        if card.job.status == "Completed":
            self.total_converted += 1
        if card in self.cards:
            self.cards.remove(card)
        if card in self.list_view.controls:
            self.list_view.controls.remove(card)
        self._refresh_ui()

    def clear_all(self, e):
        self._queue_running = False
        for card in self.cards:
            if card.job.status == "Completed":
                self.total_converted += 1
        self.cards.clear()
        self.list_view.controls.clear()
        self._refresh_ui()

    def convert_all(self, e):
        self._queue_running = True
        self._process_queue()

    def _process_queue(self):
        if not getattr(self, '_queue_running', False):
            return
            
        from src.backend.settings import SettingsManager
        try:
            max_jobs = int(SettingsManager().get('max_concurrent_jobs', 3))
        except Exception:
            max_jobs = 3

        active_jobs = sum(1 for c in self.cards if c.job.status == "Converting")
        available_slots = max_jobs - active_jobs

        if available_slots > 0:
            pending_cards = [c for c in self.cards if c.job.status == "Pending"]
            for card in pending_cards[:available_slots]:
                card.job.status = "Converting"
                self.main_page.run_thread(card.job.run, card.update_status)

    def _refresh_ui(self):
        from src.backend.history_manager import HistoryManager
        count = len(self.cards)
        has_files = count > 0

        self.convert_all_btn.disabled = not has_files
        self.clear_btn.visible = has_files
        self.queue_section.visible = has_files

        plural = "file" if count == 1 else "files"
        self.file_count_text.value = f"{count} {plural} queued"

        for c in self.cards:
            if c.job.status in ("Completed", "Failed") and not getattr(c, '_recorded', False):
                c._recorded = True
                HistoryManager().add_record(
                    c.job.input_path, 
                    c.job.target_format, 
                    c.job.status, 
                    c.job.output_path, 
                    getattr(c.job, 'error_message', None)
                )

        converted = sum(1 for c in self.cards if c.job.status == "Completed")
        in_queue = sum(1 for c in self.cards if c.job.status in ("Pending", "Converting"))
        
        c_plural = "file" if self.total_converted + converted == 1 else "files"
        q_plural = "file" if in_queue == 1 else "files"
        
        self.stat_converted_text.value = f"{self.total_converted + converted} {c_plural}"
        self.stat_queue_text.value = f"{in_queue} {q_plural}"
        
        self._empty_state.visible = not has_files

        # Stop queue if no items are pending/converting
        if getattr(self, '_queue_running', False) and in_queue == 0:
            self._queue_running = False

        # Process next in queue if active
        if getattr(self, '_queue_running', False):
            self._process_queue()
        
        try:
            self.update()
        except Exception:
            pass

    def refresh_colors(self):
        """Update all sidebar and page-level colors in-place — no rebuild, no scroll jitter."""
        # Sidebar container background
        self.sidebar_container.bgcolor = AppTheme.SURFACE

        sidebar_col = self.sidebar_container.content  # ft.Column
        # Logo section (controls[0]): Container > Row > [logo_box, title]
        logo_section = sidebar_col.controls[0]
        logo_row = logo_section.content
        logo_box = logo_row.controls[0]       # the coloured square
        logo_box.bgcolor = AppTheme.PRIMARY
        logo_title = logo_row.controls[1]     # "AnyConv" text
        logo_title.color = AppTheme.TEXT_PRIMARY

        # Nav items column (controls[1]): Container > Column
        nav_col = sidebar_col.controls[1].content
        for nav, label in zip(nav_col.controls,
                              ["Convert", "History", "Settings"]):
            is_active = (label == self.active_tab)
            nav.bgcolor = AppTheme.SURFACE_VARIANT if is_active else ft.Colors.TRANSPARENT
            nav.content.controls[0].color = AppTheme.PRIMARY if is_active else AppTheme.TEXT_SECONDARY
            nav.content.controls[1].color = AppTheme.PRIMARY if is_active else AppTheme.TEXT_SECONDARY
            nav.content.controls[1].weight = (
                ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL
            )

        # Stats section (controls[3]): Container > Column
        stats_col = sidebar_col.controls[3].content
        # Divider
        stats_col.controls[0].color = AppTheme.BORDER
        # "Session Stats" label
        stats_col.controls[2].color = AppTheme.TEXT_MUTED
        # Converted row
        for row in [stats_col.controls[4], stats_col.controls[6]]:
            row.controls[0].color = AppTheme.TEXT_MUTED
            row.controls[1].color = AppTheme.TEXT_MUTED
            row.controls[3].color = AppTheme.TEXT_SECONDARY

        # Root vertical divider
        self.root_divider.color = AppTheme.BORDER
        
        # === TOPBAR ===
        topbar_col = self.convert_view.controls[0].controls[0].controls[0]
        topbar_col.controls[0].color = AppTheme.TEXT_PRIMARY
        topbar_col.controls[1].color = AppTheme.TEXT_MUTED

        # === DROPZONE ===
        self._dz_container.gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[AppTheme.SURFACE_2, AppTheme.SURFACE_3],
        )
        self._dz_icon.color = AppTheme.PRIMARY
        self._dz_title.color = AppTheme.TEXT_PRIMARY
        self._dz_sub.color = AppTheme.TEXT_SECONDARY
        self._dz_badge.bgcolor = AppTheme.SURFACE_VARIANT
        self._dz_badge.content.controls[0].color = AppTheme.PRIMARY
        self._dz_badge.content.controls[1].color = AppTheme.PRIMARY

        # === QUEUE HEADER ===
        queue_row = self.queue_section.content.controls[0]
        left_row = queue_row.controls[0]
        left_row.controls[0].color = AppTheme.PRIMARY
        left_row.controls[1].color = AppTheme.TEXT_PRIMARY
        self.file_count_text.color = AppTheme.TEXT_MUTED

        # Convert All Button
        self.convert_all_btn.style.bgcolor = {
            ft.ControlState.DEFAULT: AppTheme.PRIMARY,
            ft.ControlState.HOVERED: AppTheme.PRIMARY_HOVER,
            ft.ControlState.DISABLED: AppTheme.SURFACE_VARIANT,
        }
        
        # Clear All Button
        self.clear_btn.style.side = ft.BorderSide(1, AppTheme.ERROR)
        self.clear_btn.content.controls[0].color = AppTheme.ERROR
        self.clear_btn.content.controls[1].color = AppTheme.ERROR
        
        # === EMPTY STATE ===
        empty_col = self._empty_state.content
        empty_col.controls[0].color = AppTheme.TEXT_MUTED
        empty_col.controls[1].color = AppTheme.TEXT_MUTED
        empty_col.controls[2].color = AppTheme.TEXT_MUTED

        # === CACHED VIEWS ===
        if getattr(self, '_history_view', None) is not None:
            self._history_view.content = self._build_history_view()
        elif getattr(self, 'history_view', None) is not None:
            self.history_view.content = self._build_history_view()

        if getattr(self, '_about_view', None) is not None:
            self._about_view.content = self._about_view._build_content()

        # === CARDS ===
        for card in getattr(self, 'cards', []):
            if hasattr(card, 'refresh_colors'):
                card.refresh_colors()
            
        try:
            self.update()
        except Exception:
            pass
