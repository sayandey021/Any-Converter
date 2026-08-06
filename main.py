import os
import sys
import flet as ft

# Add local flet_view to path for dev mode
if not getattr(sys, 'frozen', False):
    _local_flet_view = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".flet_view", "flet"
    )
    if os.path.isfile(os.path.join(_local_flet_view, "flet.exe")):
        os.environ.setdefault("FLET_VIEW_PATH", _local_flet_view)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.theme import AppTheme
from src.ui.main_view import MainView


def main(page: ft.Page):
    # Window is hidden by default using FLET_APP_HIDDEN view

    AppTheme.apply()

    page.title = "Any Converter"
    # Safely resolve absolute path to icon.ico to avoid crashes on fresh PCs (where CWD is different)
    icon_path = os.path.join(sys._MEIPASS, "assets", "icon.ico") if getattr(sys, 'frozen', False) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")
    if os.path.exists(icon_path):
        try:
            page.window.icon = icon_path
        except Exception:
            pass
    page.window.width = 1080
    page.window.height = 720
    page.window.min_width = 800
    page.window.min_height = 550
    page.theme = AppTheme.get_theme()
    page.theme_mode = ft.ThemeMode.LIGHT if AppTheme.MODE == 'light' else ft.ThemeMode.DARK
    page.bgcolor = AppTheme.BACKGROUND
    page.padding = 0
    page.fonts = {
        "Inter": "https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2",
    }

    from src.backend.ffmpeg_manager import is_ffmpeg_available, download_ffmpeg

    if is_ffmpeg_available():
        main_view = MainView(page)
        page.add(main_view)
        # Hook windnd for native Windows drag-and-drop (works in both dev and compiled)
        import threading
        def _hook_dnd():
            import time
            time.sleep(0.8)  # Wait for Flet window to fully appear
            main_view._setup_dnd()
        threading.Thread(target=_hook_dnd, daemon=True).start()
    else:
        # ── First-time setup screen ───────────────────────────────
        progress_bar = ft.ProgressBar(
            width=360,
            color=AppTheme.PRIMARY,
            bgcolor=AppTheme.SURFACE_VARIANT,
            value=0,
            border_radius=4,
            height=5,
        )
        status_text = ft.Text(
            "Checking dependencies…",
            size=13, color=AppTheme.TEXT_SECONDARY,
        )

        loading_view = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Image(
                        src="icon.png",
                        width=64,
                        height=64,
                        fit=ft.BoxFit.CONTAIN,
                        border_radius=16,
                    ),
                    width=64, height=64,
                    border_radius=16,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=12),
                ft.Text(
                    "Any Converter",
                    size=28, weight=ft.FontWeight.W_800,
                    color=AppTheme.TEXT_PRIMARY,
                ),
                ft.Text(
                    "First Time Setup",
                    size=16, color=AppTheme.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Container(height=24),
                ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(
                            width=40, height=40,
                            color=AppTheme.PRIMARY,
                            stroke_width=3,
                        ),
                        ft.Container(height=16),
                        ft.Text(
                            "Downloading FFmpeg media engine…",
                            size=14, color=AppTheme.TEXT_PRIMARY,
                            weight=ft.FontWeight.W_600,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "This only happens once. Please wait.",
                            size=12, color=AppTheme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        progress_bar,
                        ft.Container(height=8),
                        status_text,
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    bgcolor=AppTheme.SURFACE,
                    border_radius=20,
                    padding=ft.Padding(left=40, right=40, top=32, bottom=32),
                    border=ft.Border(
                        top=ft.BorderSide(1, AppTheme.BORDER),
                        right=ft.BorderSide(1, AppTheme.BORDER),
                        bottom=ft.BorderSide(1, AppTheme.BORDER),
                        left=ft.BorderSide(1, AppTheme.BORDER),
                    ),
                    width=420,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
               alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            bgcolor=AppTheme.BACKGROUND,
        )
        page.add(loading_view)

        def update_progress(percent, text):
            progress_bar.value = percent / 100.0 if percent > 0 else None
            status_text.value = text
            page.update()

        def download_task():
            import threading
            try:
                download_ffmpeg(update_progress)
                page.controls.clear()
                page.add(MainView(page))
                page.update()
            except Exception as e:
                status_text.value = f"Failed: {e}"
                status_text.color = AppTheme.ERROR
                progress_bar.color = AppTheme.ERROR
                progress_bar.value = 1.0
                page.update()

        import threading
        threading.Thread(target=download_task, daemon=True).start()

    # Show fully rendered window
    try:
        page.window.visible = True
    except Exception:
        pass
    page.update()


if __name__ == "__main__":
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
    if getattr(sys, 'frozen', False):
        assets_dir = os.path.join(sys._MEIPASS, "assets")

    ft.run(main, assets_dir=assets_dir, view=ft.AppView.FLET_APP_HIDDEN)
