import flet as ft
import threading
import sys
import os
from src.ui.theme import AppTheme
from src.backend.settings import SettingsManager

_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'theme_debug.log')

def _dbg(msg):
    with open(_LOG, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg, flush=True)

class SettingsView(ft.Container):
    def __init__(self, page: ft.Page, on_back=None):
        super().__init__()
        self.main_page = page
        self.settings = SettingsManager()
        self.on_back = on_back
        self.expand = True
        self.scroll_col = None  # persists across theme changes to preserve scroll position
        self.build_ui()

    def build_ui(self):
        # General Section
        general_section = self._build_section(
            "General",
            ft.Icons.SETTINGS_OUTLINED,
            [
                self._build_dropdown(
                    "Max Concurrent Jobs",
                    "max_concurrent_jobs",
                    [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]
                ),
                self._build_folder_picker(
                    "Default Output Folder",
                    "output_dir"
                )
            ]
        )

        from src.backend.gpu_detector import detect_best_gpu
        _, auto_label, _ = detect_best_gpu()
        auto_display = auto_label if auto_label.startswith("Auto") else f"Auto ({auto_label})"

        # Video Section
        video_section = self._build_section(
            "Video Export",
            ft.Icons.VIDEO_FILE_OUTLINED,
            [
                self._build_dropdown(
                    "Hardware Acceleration",
                    "hw_accel",
                    [(auto_display, "auto"), ("None (CPU)", "none"), ("NVIDIA (NVENC)", "nvenc"), ("Intel (QuickSync)", "qsv"), ("AMD (AMF)", "amf")]
                ),
                self._build_dropdown(
                    "Default Video Codec",
                    "default_video_codec",
                    [("H.264 (Compatible)", "h264"), ("H.265 (High Efficiency)", "hevc"), ("Default (Fast)", "copy")]
                ),
                self._build_dropdown(
                    "Video Preset (Speed/Quality)",
                    "video_preset",
                    [("Fast", "fast"), ("Medium", "medium"), ("Slow", "slow")]
                )
            ]
        )

        # Audio Section
        audio_section = self._build_section(
            "Audio Export",
            ft.Icons.AUDIO_FILE_OUTLINED,
            [
                self._build_dropdown(
                    "Default Audio Codec",
                    "default_audio_codec",
                    [("AAC", "aac"), ("MP3", "mp3"), ("Default (Fast)", "copy")]
                ),
                self._build_dropdown(
                    "Audio Bitrate",
                    "audio_bitrate",
                    [("128 kbps", "128k"), ("192 kbps", "192k"), ("320 kbps", "320k")]
                )
            ]
        )

        # Appearance Section
        appearance_section = self._build_section(
            "Appearance",
            ft.Icons.PALETTE_OUTLINED,
            [
                self._build_dropdown(
                    "Theme Mode",
                    "theme",
                    [("Dark", "dark"), ("Light", "light")],
                    on_change=self._apply_theme_change
                ),
                self._build_dropdown(
                    "Accent Color",
                    "accent_color",
                    [(k, k) for k in AppTheme.ACCENT_COLORS.keys()],
                    on_change=self._apply_theme_change
                )
            ]
        )

        # Scrollable list of sections
        inner_container = ft.Container(
            content=ft.Column(
                [general_section, appearance_section, video_section, audio_section],
                spacing=20
            ),
            padding=ft.Padding(right=16, left=0, top=0, bottom=0)
        )

        if self.scroll_col is None:
            # First build — create the scroll column
            title_text = ft.Text("Settings", size=26, weight=ft.FontWeight.W_800, color=AppTheme.TEXT_PRIMARY)
            if self.on_back:
                self.header = ft.Row([
                    title_text,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=AppTheme.TEXT_PRIMARY,
                        tooltip="Close Settings",
                        on_click=lambda e: self.on_back()
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            else:
                self.header = None

            self.scroll_col = ft.Column(
                [inner_container],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
            
            controls = []
            if self.header:
                controls.extend([self.header, ft.Container(height=20)])
            controls.append(self.scroll_col)
            
            self.content = ft.Column(
                controls,
                spacing=0,
                expand=True
            )
        else:
            # Theme change — only swap inner content; scroll col (and its position) stays alive
            self.scroll_col.controls[0] = inner_container
            if self.header is not None:
                if isinstance(self.header, ft.Row):
                    self.header.controls[0].color = AppTheme.TEXT_PRIMARY
                    self.header.controls[1].icon_color = AppTheme.TEXT_PRIMARY
                else:
                    self.header.color = AppTheme.TEXT_PRIMARY


    def _build_section(self, title: str, icon: str, controls: list) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(icon, color=AppTheme.PRIMARY, size=20),
                        ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=AppTheme.TEXT_PRIMARY)
                    ], spacing=8),
                    ft.Divider(height=1, color=AppTheme.BORDER),
                    ft.Container(height=4),
                    *controls
                ],
                spacing=12
            ),
            bgcolor=AppTheme.SURFACE_2,
            border_radius=12,
            padding=ft.Padding(20, 20, 20, 24),
            border=ft.Border(
                top=ft.BorderSide(1, AppTheme.BORDER),
                right=ft.BorderSide(1, AppTheme.BORDER),
                bottom=ft.BorderSide(1, AppTheme.BORDER),
                left=ft.BorderSide(1, AppTheme.BORDER)
            )
        )

    def _build_dropdown(self, label: str, setting_key: str, options: list, on_change=None) -> ft.Container:
        def _on_change(e):
            val = e.control.value
            _dbg(f"[DROPDOWN] {setting_key} changed to: {val!r}")
            for display, real_val in options:
                if str(real_val) == str(val):
                    _dbg(f"[DROPDOWN] Matched — saving {setting_key}={real_val!r}")
                    self.settings.set(setting_key, real_val)
                    self.settings.save()
                    if on_change:
                        _dbg(f"[DROPDOWN] Calling on_change callback for {setting_key}")
                        on_change()
                    break
            else:
                _dbg(f"[DROPDOWN] WARNING: no match found for val={val!r} in options={options}")

        dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(str(opt[1]), opt[0]) for opt in options],
            value=str(self.settings.get(setting_key)),
            width=200,
            border_color=AppTheme.BORDER,
            bgcolor=AppTheme.SURFACE_3,
            color=AppTheme.TEXT_PRIMARY,
            text_size=13,
            content_padding=ft.Padding(12, 8, 12, 8),
            dense=True,
            border_radius=8,
            focused_border_color=AppTheme.PRIMARY,
        )
        dropdown.on_change = _on_change
        if hasattr(dropdown, 'on_select'):
            dropdown.on_select = _on_change

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(label, size=14, color=AppTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                    dropdown
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def _build_folder_picker(self, label: str, setting_key: str) -> ft.Container:
        current_val = self.settings.get(setting_key, "")
        
        display_text = ft.Text(
            current_val if current_val else "Same as Source", 
            size=13, 
            color=AppTheme.TEXT_PRIMARY if current_val else AppTheme.TEXT_MUTED,
            no_wrap=True,
            width=160,
            text_align=ft.TextAlign.RIGHT,
            tooltip=current_val if current_val else "Same as Source"
        )
        
        def _on_click(e):
            import tkinter as tk
            from tkinter import filedialog
            
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            folder = filedialog.askdirectory(title="Select Output Folder")
            root.destroy()
            
            if folder:
                self.settings.set(setting_key, folder)
                self.settings.save()
                display_text.value = folder
                display_text.color = AppTheme.TEXT_PRIMARY
                display_text.tooltip = folder
                display_text.update()
                
        def _on_clear(e):
            self.settings.set(setting_key, "")
            self.settings.save()
            display_text.value = "Same as Source"
            display_text.color = AppTheme.TEXT_MUTED
            display_text.tooltip = "Same as Source"
            display_text.update()

        change_btn = ft.OutlinedButton(
            "Change",
            style=ft.ButtonStyle(
                side=ft.BorderSide(1, AppTheme.BORDER),
                color=AppTheme.TEXT_PRIMARY,
                padding=ft.Padding(12, 6, 12, 6)
            ),
            on_click=_on_click
        )
        
        clear_btn = ft.IconButton(
            ft.Icons.CLEAR,
            icon_color=AppTheme.TEXT_MUTED,
            icon_size=18,
            tooltip="Reset to Source Folder",
            on_click=_on_clear
        )
        
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(label, size=14, color=AppTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                    ft.Row([
                        display_text,
                        clear_btn,
                        change_btn
                    ], spacing=4, alignment=ft.MainAxisAlignment.END)
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

    def _apply_theme_change(self):
        """Apply theme in-place — no page rebuild, no scroll jitter."""
        _dbg("[THEME] _apply_theme_change() called")
        try:
            AppTheme.apply()
            _dbg(f"[THEME] Mode changed to {AppTheme.MODE}")

            # Update page-level theme
            self.main_page.theme_mode = ft.ThemeMode.LIGHT if AppTheme.MODE == "light" else ft.ThemeMode.DARK
            self.main_page.theme = AppTheme.get_theme()
            self.main_page.bgcolor = AppTheme.BACKGROUND

            # Rebuild settings sections in-place (scroll_col stays alive — no position reset!)
            self.build_ui()

            # Update sidebar colors in-place
            main_view = self.main_page.controls[0]
            if hasattr(main_view, 'refresh_colors'):
                main_view.refresh_colors()

            # Single page update — no rebuild, no jitter
            self.main_page.update()
            _dbg("[THEME] page.update() called — theme switched completely")
        except Exception as ex:
            import traceback
            _dbg(f"[THEME ERROR] {ex}\n{traceback.format_exc()}")


