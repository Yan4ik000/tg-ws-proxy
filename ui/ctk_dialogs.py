import io
import base64
import tkinter as tk
from typing import Any, Optional, Sequence, Tuple

from ui.ctk_theme import CtkTheme, center_ctk_geometry

def _clear_low_alpha(image: Any, threshold: int = 72) -> Any:
    alpha = image.getchannel("A")
    mask = alpha.point(lambda value: 0 if value < threshold else value)
    image.putalpha(mask)
    return image

def _modern_dialog_icon(kind: str, size: int = 40):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None

    scale = 4
    canvas = size * scale
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fill = (217, 52, 52, 255) if kind == "error" else (51, 144, 236, 255)
    pad = max(4, int(canvas * 0.08))
    draw.ellipse((pad, pad, canvas - pad - 1, canvas - pad - 1), fill=fill)
    text = "?" if kind == "question" else "i" if kind == "info" else "!"
    try:
        font_name = "segoeuib.ttf" if kind == "error" else "segoeui.ttf"
        font = ImageFont.truetype(font_name, int(canvas * 0.68))
    except Exception:
        font = ImageFont.load_default()
        
    if kind == "error":
        line = max(6, int(canvas * 0.13))
        inset = int(canvas * 0.31)
        draw.line((inset, inset, canvas - inset, canvas - inset), fill=(255, 255, 255, 255), width=line)
        draw.line((canvas - inset, inset, inset, canvas - inset), fill=(255, 255, 255, 255), width=line)
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (canvas - (bbox[2] - bbox[0])) / 2 - bbox[0]
        y = (canvas - (bbox[3] - bbox[1])) / 2 - bbox[1] + canvas * 0.01
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
    return _clear_low_alpha(img.resize((size, size), Image.Resampling.LANCZOS), 48)

def _photo_from_image(image: Any) -> Any:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return tk.PhotoImage(data=data)

def _appearance_is_dark(ctk: Any) -> bool:
    try:
        return str(ctk.get_appearance_mode()).lower() == "dark"
    except Exception:
        return False

def _build_dialog_base(
    ctk: Any,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    kind: str,
    icon_path: Optional[str]
) -> Tuple[Any, Any, Any, float]:
    dark = _appearance_is_dark(ctk)
    body_bg = "#2b2b2b" if dark else "#ffffff"
    text_color = theme.text_primary

    root = ctk.CTkToplevel(parent) if parent is not None else ctk.CTkToplevel()
    root.withdraw()
    root.title(title)
    root.configure(fg_color=body_bg)
    
    if parent is not None:
        try:
            root.transient(parent)
        except Exception:
            pass
            
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    if icon_path:
        try:
            root.after(200, lambda: root.iconbitmap(icon_path))
        except Exception:
            pass

    body = ctk.CTkFrame(root, fg_color=body_bg, corner_radius=0)
    body.pack(fill="both", expand=True, padx=20, pady=16)
    
    try:
        scaling = ctk.ScalingTracker.get_window_scaling(root)
    except Exception:
        scaling = root._get_window_scaling() if hasattr(root, "_get_window_scaling") else 1.0
    icon_size_scaled = int(40 * scaling)

    pil_icon = _modern_dialog_icon(kind, size=icon_size_scaled)
    if pil_icon is not None:
        tk_icon = _photo_from_image(pil_icon)
        icon_label = tk.Label(
            body,
            text="",
            image=tk_icon,
            width=icon_size_scaled,
            height=icon_size_scaled,
            bg=body_bg,
            bd=0,
            highlightthickness=0
        )
        icon_label.image = tk_icon # keep reference
        icon_label.pack(side="left", anchor="n", padx=(0, int(14 * scaling)))
    else:
        icon_label = None
    
    content_frame = ctk.CTkFrame(body, fg_color="transparent")
    content_frame.pack(side="left", fill="both", expand=True)

    text_label = ctk.CTkLabel(
        content_frame,
        text=message,
        justify="left",
        anchor="nw",
        font=(theme.ui_font_family, 13),
        text_color=text_color,
        wraplength=int(350 * scaling),
    )
    text_label.pack(fill="x")
    
    # Dynamic Alignment Logic
    dummy = ctk.CTkLabel(content_frame, text="A", font=(theme.ui_font_family, 13))
    dummy.pack()
    root.update_idletasks()
    
    line_h = dummy.winfo_reqheight()
    dummy.destroy()
    root.update_idletasks()
    
    text_h = text_label.winfo_reqheight()
    icon_h = icon_size_scaled
    
    num_lines = max(1, round(text_h / line_h))
    
    icon_top_pad = 0
    text_top_pad = 0
    
    if num_lines <= 2:
        if icon_h > text_h:
            text_top_pad = (icon_h - text_h) // 2
        else:
            icon_top_pad = (text_h - icon_h) // 2
    else:
        two_lines_h = line_h * 2
        if icon_h > two_lines_h:
            text_top_pad = (icon_h - two_lines_h) // 2
        else:
            icon_top_pad = (two_lines_h - icon_h) // 2

    if icon_label is not None and icon_top_pad > 0:
        icon_label.pack_configure(pady=(icon_top_pad, 0))
    if text_top_pad > 0:
        text_label.pack_configure(pady=(text_top_pad, 0))
    
    return root, body, content_frame, scaling

def show_ctk_dialog(
    ctk: Any,
    *,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    kind: str = "info",
    buttons: Sequence[Tuple[str, str, bool]] = (("OK", "ok", True),),
    default: str = "ok",
    icon_path: Optional[str] = None,
) -> str:
    root, body, content_frame, scaling = _build_dialog_base(ctk, parent, theme, title, message, kind, icon_path)
    
    dark = _appearance_is_dark(ctk)
    footer_bg = "#2b2b2b" if dark else "#f3f3f3"

    footer = ctk.CTkFrame(root, fg_color=footer_bg, corner_radius=0)
    footer.pack(fill="x", side="bottom")
    
    btn_frame = ctk.CTkFrame(footer, fg_color="transparent")
    btn_frame.pack(side="right", padx=16, pady=10)
    
    result = {"value": default}
    
    def close(value: str) -> None:
        result["value"] = value
        try:
            root.grab_release()
        except Exception:
            pass
        root.destroy()

    for i, (text, value, is_primary) in enumerate(buttons):
        btn = ctk.CTkButton(
            btn_frame,
            text=text,
            width=84,
            height=28,
            font=(theme.ui_font_family, 13),
            corner_radius=8,
            fg_color=theme.tg_blue if is_primary else theme.field_bg,
            hover_color=theme.tg_blue_hover if is_primary else theme.field_border,
            text_color="#ffffff" if is_primary else theme.text_primary,
            border_width=0 if is_primary else 1,
            border_color=theme.field_border,
            command=lambda v=value: close(v)
        )
        btn.pack(side="left", padx=(0 if i == 0 else 8, 0))
        if value == default:
            try:
                btn.focus_set()
            except Exception:
                pass

    root.protocol("WM_DELETE_WINDOW", lambda: close(default))
    root.bind("<Escape>", lambda _e: close(default))
    root.bind("<Return>", lambda _e: close(default))
    
    root.update_idletasks()
    width = max(260, int(root.winfo_reqwidth() / scaling))
    height = int(root.winfo_reqheight() / scaling)
    center_ctk_geometry(root, width, height)
    root.resizable(False, False)
    root.deiconify()
    
    try:
        root.grab_set()
    except Exception:
        pass
        
    root.wait_window()
    return result["value"]

def ask_yes_no(
    ctk: Any,
    *,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    icon_path: Optional[str] = None,
) -> bool:
    return show_ctk_dialog(
        ctk,
        parent=parent,
        theme=theme,
        title=title,
        message=message,
        kind="question",
        buttons=(("Да", "yes", True), ("Нет", "no", False)),
        default="no",
        icon_path=icon_path,
    ) == "yes"

def show_error(
    ctk: Any,
    *,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    icon_path: Optional[str] = None,
) -> bool:
    show_ctk_dialog(
        ctk,
        parent=parent,
        theme=theme,
        title=title,
        message=message,
        kind="error",
        buttons=(("OK", "ok", True),),
        icon_path=icon_path,
    )
    return True

def show_info(
    ctk: Any,
    *,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    icon_path: Optional[str] = None,
) -> bool:
    show_ctk_dialog(
        ctk,
        parent=parent,
        theme=theme,
        title=title,
        message=message,
        kind="info",
        buttons=(("OK", "ok", True),),
        icon_path=icon_path,
    )
    return True

def run_with_progress(
    ctk: Any,
    *,
    parent: Optional[Any],
    theme: CtkTheme,
    title: str,
    message: str,
    icon_path: Optional[str] = None,
    task: Any,
) -> None:
    import threading as _threading

    root, body, content_frame, scaling = _build_dialog_base(ctk, parent, theme, title, message, "info", icon_path)
    
    body.pack_configure(pady=(16, 26))

    status_label = ctk.CTkLabel(
        content_frame, text="",
        justify="left", anchor="w",
        font=(theme.ui_font_family, 11),
        text_color=theme.text_secondary,
        wraplength=int(350 * scaling),
    )
    status_label.pack(fill="x", pady=(6, 0))

    root.protocol("WM_DELETE_WINDOW", lambda: None)

    root.update_idletasks()
    width = max(320, int(root.winfo_reqwidth() / scaling))
    height = int(root.winfo_reqheight() / scaling)
    center_ctk_geometry(root, width, height)
    root.resizable(False, False)
    root.deiconify()

    try:
        root.grab_set()
    except Exception:
        pass

    def _set_status(msg: str) -> None:
        try:
            root.after(0, lambda: status_label.configure(text=msg))
        except Exception:
            pass

    def _run_task() -> None:
        try:
            task(_set_status)
        finally:
            try:
                root.after(0, root.destroy)
            except Exception:
                pass

    _threading.Thread(target=_run_task, daemon=True).start()
    root.wait_window()
