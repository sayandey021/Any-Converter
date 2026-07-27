import flet as ft
from src.backend.settings import SettingsManager


class AppTheme:
    # ── Current palette (mutable at runtime) ──
    PRIMARY = "#7c3aed"        # Violet
    PRIMARY_HOVER = "#6d28d9"
    PRIMARY_LIGHT = "#a78bfa"
    BACKGROUND = "#09090f"
    SURFACE = "#13131f"
    SURFACE_2 = "#1a1a2e"
    SURFACE_3 = "#222236"
    SURFACE_VARIANT = "#2d2d4a"
    TEXT_PRIMARY = "#f1f0ff"
    TEXT_SECONDARY = "#8b8aaa"
    TEXT_MUTED = "#5c5b75"
    ACCENT = "#38bdf8"
    GLASS_SURFACE = "#0Dffffff"
    GLASS_BORDER = "#18ffffff"
    GLASS_SURFACE_VARIANT = "#14ffffff"
    BG_IMAGE = ""
    BG_OPACITY = 0.1
    ERROR = "#ef4444"
    ERROR_BG = "#2d1515"
    SUCCESS = "#22c55e"
    SUCCESS_BG = "#0f2d1a"
    WARNING = "#f59e0b"
    INFO = "#38bdf8"
    BORDER = "#2a2a3e"

    ACCENT_COLORS = {
        'Violet': {'PRIMARY': "#7c3aed", 'PRIMARY_HOVER': "#6d28d9", 'PRIMARY_LIGHT': "#a78bfa"},
        'Indigo': {'PRIMARY': "#6366f1", 'PRIMARY_HOVER': "#4f46e5", 'PRIMARY_LIGHT': "#818cf8"},
        'Emerald': {'PRIMARY': "#10b981", 'PRIMARY_HOVER': "#059669", 'PRIMARY_LIGHT': "#34d399"},
        'Rose': {'PRIMARY': "#f43f5e", 'PRIMARY_HOVER': "#e11d48", 'PRIMARY_LIGHT': "#fb7185"},
        'Amber': {'PRIMARY': "#f59e0b", 'PRIMARY_HOVER': "#d97706", 'PRIMARY_LIGHT': "#fbbf24"},
        'Sky': {'PRIMARY': "#0ea5e9", 'PRIMARY_HOVER': "#0284c7", 'PRIMARY_LIGHT': "#38bdf8"},
        'Cyan': {'PRIMARY': "#06b6d4", 'PRIMARY_HOVER': "#0891b2", 'PRIMARY_LIGHT': "#22d3ee"},
    }

    # ── Palettes ──
    _DARK = {
        'PRIMARY': "#7c3aed",
        'PRIMARY_HOVER': "#6d28d9",
        'PRIMARY_LIGHT': "#a78bfa",
        'BACKGROUND': "#09090f",
        'SURFACE': "#13131f",
        'SURFACE_2': "#1a1a2e",
        'SURFACE_3': "#222236",
        'SURFACE_VARIANT': "#2d2d4a",
        'TEXT_PRIMARY': "#f1f0ff",
        'TEXT_SECONDARY': "#8b8aaa",
        'TEXT_MUTED': "#5c5b75",
        'ACCENT': "#38bdf8",
        'ERROR': "#ef4444",
        'ERROR_BG': "#2d1515",
        'SUCCESS': "#22c55e",
        'SUCCESS_BG': "#0f2d1a",
        'WARNING': "#f59e0b",
        'INFO': "#38bdf8",
        'BORDER': "#2a2a3e",
        'GLASS_SURFACE': "#0Dffffff",
        'GLASS_BORDER': "#18ffffff",
        'GLASS_SURFACE_VARIANT': "#14ffffff",
    }

    _LIGHT = {
        'PRIMARY': "#7c3aed",
        'PRIMARY_HOVER': "#6d28d9",
        'PRIMARY_LIGHT': "#a78bfa",
        'BACKGROUND': "#e2e8f0",
        'SURFACE': "#ffffff",
        'SURFACE_2': "#f8fafc",
        'SURFACE_3': "#f1f5f9",
        'SURFACE_VARIANT': "#e2e8f0",
        'TEXT_PRIMARY': "#0f172a",
        'TEXT_SECONDARY': "#334155",
        'TEXT_MUTED': "#64748b",
        'ACCENT': "#0284c7",
        'ERROR': "#ef4444",
        'ERROR_BG': "#fef2f2",
        'SUCCESS': "#22c55e",
        'SUCCESS_BG': "#f0fdf4",
        'WARNING': "#f59e0b",
        'INFO': "#0ea5e9",
        'BORDER': "#cbd5e1",
        'GLASS_SURFACE': "#88ffffff",
        'GLASS_BORDER': "#33000000",
        'GLASS_SURFACE_VARIANT': "#AAf1f5f9",
    }

    MODE = "dark"

    @classmethod
    def apply(cls, mode: str = None, accent: str = None, bg_image: str = None, bg_opacity: float = None):
        settings = SettingsManager()
        if mode is None:
            mode = settings.get('theme', 'dark')
        if accent is None:
            accent = settings.get('accent_color', 'Violet')
        if bg_image is None:
            bg_image = settings.get('bg_image_path', '')
        if bg_opacity is None:
            bg_opacity = settings.get('bg_image_opacity', 0.1)

        cls.MODE = mode
        cls.BG_IMAGE = bg_image
        cls.BG_OPACITY = bg_opacity

        palette = cls._LIGHT if mode == 'light' else cls._DARK
        for key, value in palette.items():
            setattr(cls, key, value)

        if accent in cls.ACCENT_COLORS:
            cls.PRIMARY = cls.ACCENT_COLORS[accent]['PRIMARY']
            cls.PRIMARY_HOVER = cls.ACCENT_COLORS[accent]['PRIMARY_HOVER']
            cls.PRIMARY_LIGHT = cls.ACCENT_COLORS[accent].get('PRIMARY_LIGHT', cls.PRIMARY)

    @classmethod
    def get_all_colors(cls):
        return {
            'PRIMARY': cls.PRIMARY,
            'PRIMARY_HOVER': cls.PRIMARY_HOVER,
            'PRIMARY_LIGHT': cls.PRIMARY_LIGHT,
            'BACKGROUND': cls.BACKGROUND,
            'SURFACE': cls.SURFACE,
            'SURFACE_2': cls.SURFACE_2,
            'SURFACE_3': cls.SURFACE_3,
            'SURFACE_VARIANT': cls.SURFACE_VARIANT,
            'TEXT_PRIMARY': cls.TEXT_PRIMARY,
            'TEXT_SECONDARY': cls.TEXT_SECONDARY,
            'TEXT_MUTED': cls.TEXT_MUTED,
            'ACCENT': cls.ACCENT,
            'ERROR': cls.ERROR,
            'ERROR_BG': cls.ERROR_BG,
            'SUCCESS': cls.SUCCESS,
            'SUCCESS_BG': cls.SUCCESS_BG,
            'WARNING': cls.WARNING,
            'INFO': cls.INFO,
            'BORDER': cls.BORDER,
            'GLASS_SURFACE': cls.GLASS_SURFACE,
            'GLASS_BORDER': cls.GLASS_BORDER,
            'GLASS_SURFACE_VARIANT': cls.GLASS_SURFACE_VARIANT,
        }

    @classmethod
    def get_theme(cls):
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=cls.PRIMARY,
                surface=cls.SURFACE,
                error=cls.ERROR,
            ),
            use_material3=True,
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
