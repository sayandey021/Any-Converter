import os
import platform
import subprocess
from src.backend.ffmpeg_manager import get_local_ffmpeg_exe

_CACHED_GPU_INFO = None


def detect_best_gpu(force_refresh=False):
    """
    Detects the best available GPU hardware acceleration on the machine.
    Returns a tuple: (accel_type, display_label, gpu_name)
    where accel_type is one of 'nvenc', 'qsv', 'amf', or 'none'.
    Runs ultra-fast (<0.01 seconds).
    """
    global _CACHED_GPU_INFO
    if _CACHED_GPU_INFO and not force_refresh:
        return _CACHED_GPU_INFO

    system_gpus = []
    if platform.system() == 'Windows':
        try:
            import winreg
            key_path = r'SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
                for i in range(100):
                    try:
                        sub_name = winreg.EnumKey(k, i)
                        with winreg.OpenKey(k, sub_name) as sub_k:
                            try:
                                desc, _ = winreg.QueryValueEx(sub_k, 'DriverDesc')
                                if desc and not any(x in desc.lower() for x in ['virtual', 'basic', 'remote']):
                                    system_gpus.append(desc)
                            except Exception:
                                pass
                    except OSError:
                        break
        except Exception:
            pass

    # Quick match from registry system GPUs
    for g in system_gpus:
        gupper = g.upper()
        if any(k in gupper for k in ['NVIDIA', 'GEFORCE', 'QUADRO', 'RTX', 'GTX']):
            _CACHED_GPU_INFO = ('nvenc', f"Auto (NVIDIA {g})", f"NVIDIA {g}")
            return _CACHED_GPU_INFO
        elif any(k in gupper for k in ['RADEON', 'AMD']):
            _CACHED_GPU_INFO = ('amf', f"Auto (AMD {g})", f"AMD {g}")
            return _CACHED_GPU_INFO
        elif any(k in gupper for k in ['INTEL', 'GRAPHICS', 'ARC']):
            _CACHED_GPU_INFO = ('qsv', f"Auto (Intel {g})", f"Intel {g}")
            return _CACHED_GPU_INFO

    # Fallback to FFmpeg probing if registry yielded no dedicated GPU
    ffmpeg_exe = get_local_ffmpeg_exe()
    if ffmpeg_exe and os.path.exists(ffmpeg_exe):
        encoders = [
            ('nvenc', 'h264_nvenc', 'NVIDIA (NVENC)'),
            ('qsv', 'h264_qsv', 'Intel (QuickSync)'),
            ('amf', 'h264_amf', 'AMD (AMF)'),
        ]
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        for accel_type, codec, label in encoders:
            try:
                cmd = [ffmpeg_exe, '-y', '-f', 'lavfi', '-i', 'color=c=black:s=64x64:d=0.1', '-vcodec', codec, '-f', 'null', '-']
                p = subprocess.run(cmd, capture_output=True, timeout=2, creationflags=flags)
                if p.returncode == 0:
                    _CACHED_GPU_INFO = (accel_type, f"Auto ({label})", label)
                    return _CACHED_GPU_INFO
            except Exception:
                pass

    _CACHED_GPU_INFO = ('none', 'Auto (CPU)', 'CPU (Software)')
    return _CACHED_GPU_INFO
