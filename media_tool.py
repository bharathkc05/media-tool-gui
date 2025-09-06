import os
import sys
import json
import shutil
import threading
import subprocess
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import webbrowser

APP_TITLE = "Media Tool GUI"
APP_VERSION = "1.0.0"
DEFAULT_PRESET_FILE = "tool_gui_presets.json"

# ---------------------------------------------------------------------------
# Theming (minimal, professional, compact). Two palettes: Light & Dark.
# ---------------------------------------------------------------------------
THEMES = {
    "Light": {
        # Surfaces
        "bg": "#FFFFFF",
        "surface1": "#FFFFFF",
        "surface2": "#F8FAFC",
        "surface3": "#F1F5F9",

        # Text
        "fg": "#0F172A",
        "subtle_fg": "#334155",
        "muted_fg": "#64748B",
        "inverse_fg": "#FFFFFF",

        # Brand / accent
        "accent": "#2563EB",
        "accent_hover": "#1D4ED8",
        "accent_pressed": "#1E40AF",
        "accent_on": "#FFFFFF",

        # Secondary
        "secondary_fill": "#7C3AED",
        "secondary_on": "#FFFFFF",

        # Links
        "link": "#2563EB",
        "link_hover": "#1D4ED8",
        "link_visited": "#7C3AED",

        # Borders & dividers
        "border": "#E5E7EB",
        "border_strong": "#CBD5E1",

        # Fields / editors (renamed from entry_bg/text_bg/text_fg; keep old keys as aliases if needed)
        "field_bg": "#FFFFFF",
        "field_border": "#E5E7EB",
        "field_text": "#0F172A",

        # Selection
        "select_bg": "#DBEAFE",
        "select_fg": "#0F172A",
        "selection_opacity": 1.0,

        # Neutral button (secondary)
        "secondary_bg": "#F1F5F9",
        "secondary_hover": "#E2E8F0",
        "secondary_pressed": "#CBD5E1",

        # Focus & overlays
        "focus_ring": "#93C5FD",
        "scrim": "rgba(0,0,0,0.40)",            # modals/sheets
        "overlay_hover": "rgba(0,0,0,0.02)",     # subtle elevation on hover
        "overlay_pressed": "rgba(0,0,0,0.04)",

        # Disabled (contrast-fixed)
        "disabled_bg": "#E5E7EB",
        "disabled_fg": "#4B5563",               # was #9CA3AF; now ~6.1:1 on #E5E7EB

        # Feedback
        "success_fg": "#166534",
        "success_surface": "#ECFDF5",
        "warning_fg": "#92400E",
        "warning_surface": "#FFFBEB",
        "error_fg": "#991B1B",
        "error_surface": "#FEF2F2",
        "info_fg": "#075985",
        "info_surface": "#ECFEFF",

        # Aliases (optional for backward compatibility)
        "entry_bg": "#FFFFFF",
        "entry_border": "#E5E7EB",
        "text_bg": "#F8FAFC",
        "text_fg": "#0F172A",
        "primary_pressed": "#1E40AF",
    },
    "Dark": {
        # Surfaces
        "bg": "#121212",
        "surface1": "#1E1E1E",
        "surface2": "#232323",
        "surface3": "#2A2A2A",

        # Text
        "fg": "#E5E7EB",
        "subtle_fg": "#D1D5DB",
        "muted_fg": "#9CA3AF",
        "inverse_fg": "#111827",

        # Brand / accent
        "accent": "#60A5FA",
        "accent_hover": "#93C5FD",
        "accent_pressed": "#BFDBFE",
        "accent_on": "#0B1220",

        # Secondary
        "secondary_fill": "#A78BFA",
        "secondary_on": "#0B1220",

        # Links
        "link": "#93C5FD",
        "link_hover": "#BFDBFE",
        "link_visited": "#C4B5FD",

        # Borders & dividers
        "border": "#2A2A2A",
        "border_strong": "#3A3A3A",

        # Fields / editors
        "field_bg": "#1E1E1E",
        "field_border": "#2A2A2A",
        "field_text": "#E5E7EB",

        # Selection
        "select_bg": "#1E3A8A",
        "select_fg": "#E5E7EB",
        "selection_opacity": 1.0,

        # Neutral button (secondary)
        "secondary_bg": "#1E1E1E",
        "secondary_hover": "#232323",
        "secondary_pressed": "#2A2A2A",

        # Focus & overlays
        "focus_ring": "#60A5FA",
        "scrim": "rgba(0,0,0,0.60)",
        "overlay_hover": "rgba(255,255,255,0.06)",   # subtle light overlay for elevation
        "overlay_pressed": "rgba(255,255,255,0.10)",

        # Disabled (contrast-improved)
        "disabled_bg": "#1F2937",
        "disabled_fg": "#9CA3AF",                    # was #6B7280; now ~5.78:1 on #1F2937

        # Feedback
        "success_fg": "#22C55E",
        "success_surface": "#0F2D26",
        "warning_fg": "#F59E0B",
        "warning_surface": "#2A1E04",
        "error_fg": "#F87171",
        "error_surface": "#2A0E0E",
        "info_fg": "#67E8F9",
        "info_surface": "#07283B",

        # Alias
        "entry_bg": "#1E1E1E",
        "entry_border": "#2A2A2A",
        "text_bg": "#232323",
        "text_fg": "#E5E7EB",
        "primary_pressed": "#BFDBFE",
    },
}


DEFAULT_THEME = "Dark"

def resource_path(relative: str) -> str:
    """Return absolute path to resource.

    Priority:
      1. PyInstaller _MEIPASS (when bundled)
      2. Directory containing this script
      3. Current working directory (fallback)
    """
    if hasattr(sys, "_MEIPASS"):
        base = getattr(sys, "_MEIPASS")  # type: ignore[attr-defined]
    else:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
        except NameError:  # interactive mode
            base = os.path.abspath(".")
    return os.path.join(base, relative)

def which(cmd):
    return shutil.which(cmd)

def find_exe(name):
    """Find executable in PATH, current directory, or subdirectories."""
    # First, try which (includes PATH)
    path = which(name)
    if path:
        return path
    # Then, check current directory with .exe
    exe_name = name + ".exe"
    if os.path.exists(exe_name):
        return os.path.abspath(exe_name)
    # Then, check in subdirectories of current
    for root, dirs, files in os.walk('.'):
        if exe_name in files:
            return os.path.abspath(os.path.join(root, exe_name))
    return None

class AsyncRunner:
    def __init__(self, text_widget, run_button, cancel_button):
        self.text = text_widget
        self.run_button = run_button
        self.cancel_button = cancel_button
        self.proc = None
        self.q = queue.Queue()
        self.reader_thread = None

    def log(self, msg):
        self.text.configure(state="normal")
        self.text.insert("end", msg + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def _reader(self, stream):
        for line in iter(stream.readline, b''):
            self.q.put(line.decode(errors="replace"))
        stream.close()

    def _drain_queue(self):
        try:
            while True:
                line = self.q.get_nowait()
                self.log(line.rstrip("\n"))
        except queue.Empty:
            pass
        if self.proc and self.proc.poll() is None:
            self.text.after(100, self._drain_queue)
        else:
            # final drain
            try:
                while True:
                    line = self.q.get_nowait()
                    self.log(line.rstrip("\n"))
            except queue.Empty:
                pass
            code = None if self.proc is None else self.proc.returncode
            self.log(f"[exit code] {code}")
            self.run_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")

    def run(self, cmd, cwd=None):
        if self.proc is not None and self.proc.poll() is None:
            messagebox.showwarning("Busy", "A process is already running.")
            return
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

        # Debug: Print the full command
        print(f"AsyncRunner executing: {cmd}")
        self.log("> " + " ".join(cmd))
        try:
            self.proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
        except Exception as e:
            self.log(f"Failed to start: {e}")
            return

        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.reader_thread = threading.Thread(target=self._reader, args=(self.proc.stdout,), daemon=True)
        self.reader_thread.start()
        self._drain_queue()

    def cancel(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

class PathPicker(ttk.Frame):
    def __init__(self, master, label, default_cmd=None, must_exist=True, **kwargs):
        super().__init__(master, **kwargs)
        self.must_exist = must_exist
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        self.var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.var, width=60)
        entry.grid(row=0, column=1, sticky="we", padx=4)
        self.columnconfigure(1, weight=1)
        ttk.Button(self, text="Browse", command=self.browse).grid(row=0, column=2, padx=2)
        if default_cmd:
            ttk.Button(self, text="Find in PATH", command=lambda: self.find_in_path(default_cmd)).grid(row=0, column=3, padx=2)

    def browse(self):
        path = filedialog.askopenfilename()
        if path:
            self.var.set(path)

    def find_in_path(self, cmd):
        p = which(cmd)
        if p:
            self.var.set(p)
        else:
            messagebox.showinfo("Not found", f"'{cmd}' not found in PATH.")

    def get(self):
        v = self.var.get().strip()
        if self.must_exist and v and not os.path.isfile(v):
            messagebox.showerror("Path error", f"File not found: {v}")
            return None
        return v or ""

class FilePicker(ttk.Frame):
    def __init__(self, master, label, mode="open", must_exist=True, **kwargs):
        super().__init__(master, **kwargs)
        self.mode = mode
        self.must_exist = must_exist
        ttk.Label(self, text=label).grid(row=0, column=0, sticky="w")
        self.var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.var, width=60)
        entry.grid(row=0, column=1, sticky="we", padx=4)
        self.columnconfigure(1, weight=1)
        ttk.Button(self, text="Browse", command=self.browse).grid(row=0, column=2)

    def browse(self):
        if self.mode == "open":
            path = filedialog.askopenfilename()
        else:
            path = filedialog.asksaveasfilename()
        if path:
            self.var.set(path)

    def get(self):
        v = self.var.get().strip()
        if self.must_exist and v and not os.path.isfile(v):
            messagebox.showerror("File error", f"File not found: {v}")
            return None
        return v or ""

class Collapsible(ttk.Frame):
    def __init__(self, master, title="Advanced", **kwargs):
        super().__init__(master, **kwargs)
        self.shown = tk.BooleanVar(value=False)
        self.btn = ttk.Checkbutton(self, text=title, variable=self.shown, command=self.toggle, style="Toolbutton")
        self.btn.grid(row=0, column=0, sticky="w")
        self.body = ttk.Frame(self)
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_remove()

    def toggle(self):
        if self.shown.get():
            self.body.grid()
        else:
            self.body.grid_remove()

class DoviToolTab(ttk.Frame):
    def __init__(self, master, runner: AsyncRunner, **kwargs):
        super().__init__(master, **kwargs)
        self.runner = runner

        # Tool path
        self.path_picker = PathPicker(self, "dovi_tool path:", default_cmd="dovi_tool")
        self.path_picker.grid(row=0, column=0, columnspan=4, sticky="we", pady=4)
        self.columnconfigure(1, weight=1)
        
        # Auto-populate dovi_tool path if it exists
        dovi_path = find_exe("dovi_tool")
        if dovi_path:
            self.path_picker.var.set(dovi_path)
            print(f"Auto-found dovi_tool: {dovi_path}")

        # Subcommand
        ttk.Label(self, text="Subcommand:").grid(row=1, column=0, sticky="w")
        self.subcmd = tk.StringVar(value="extract-rpu")
        dovi_subs = ["convert", "demux", "editor", "export", "extract-rpu", "inject-rpu", "generate", "info", "mux", "plot", "remove"]
        ttk.Combobox(self, textvariable=self.subcmd, values=dovi_subs, state="readonly", width=20).grid(row=1, column=1, sticky="w", pady=2)

        # IO
        self.in_file = FilePicker(self, "Input:", mode="open", must_exist=True)
        self.in_file.grid(row=2, column=0, columnspan=3, sticky="we", pady=2)
        self.out_file = FilePicker(self, "Output:", mode="save", must_exist=False)
        self.out_file.grid(row=3, column=0, columnspan=3, sticky="we", pady=2)

        # RPU in/out
        self.rpu_in = FilePicker(self, "RPU in (inject):", mode="open", must_exist=True)
        self.rpu_in.grid(row=4, column=0, columnspan=3, sticky="we", pady=2)
        self.rpu_out = FilePicker(self, "RPU out (extract):", mode="save", must_exist=False)
        self.rpu_out.grid(row=5, column=0, columnspan=3, sticky="we", pady=2)

        # Common options
        adv = Collapsible(self, "Advanced options")
        adv.grid(row=6, column=0, columnspan=4, sticky="we", pady=4)
        opt_row = 0
        
        # Mode selection with help
        ttk.Label(adv.body, text="Mode (--mode):").grid(row=opt_row, column=0, sticky="w")
        self.mode = tk.StringVar(value="")
        mode_box = ttk.Combobox(adv.body, textvariable=self.mode, values=["", "0", "1", "2", "3", "4", "5"], width=8, state="readonly")
        mode_box.grid(row=opt_row, column=1, sticky="w")
        # Mode help text
        mode_help = ttk.Label(adv.body, text="0=Parse, 1=MEL, 2=8.1, 3=5→8.1, 4=8.4, 5=8.1+map", font=("Arial", 8), foreground="gray")
        mode_help.grid(row=opt_row, column=2, sticky="w", padx=(5,0))
        opt_row += 1
        
        # Crop option
        self.crop = tk.BooleanVar(adv.body, False)
        ttk.Checkbutton(adv.body, text="--crop (Remove letterbox bars)", variable=self.crop).grid(row=opt_row, column=0, sticky="w", columnspan=2)
        opt_row += 1
        
        # Drop HDR10+ option
        self.drop_hdr10p = tk.BooleanVar(adv.body, False)
        ttk.Checkbutton(adv.body, text="--drop-hdr10plus (Ignore HDR10+ metadata)", variable=self.drop_hdr10p).grid(row=opt_row, column=0, sticky="w", columnspan=2)
        opt_row += 1
        
        # Edit config
        ttk.Label(adv.body, text="--edit-config (JSON file):").grid(row=opt_row, column=0, sticky="w")
        self.edit_cfg = FilePicker(adv.body, "", mode="open", must_exist=True)
        self.edit_cfg.grid(row=opt_row, column=1, sticky="we", columnspan=2)
        opt_row += 1
        
        # Start code
        ttk.Label(adv.body, text="--start-code:").grid(row=opt_row, column=0, sticky="w")
        self.start_code = tk.StringVar(value="")
        start_code_box = ttk.Combobox(adv.body, textvariable=self.start_code, values=["", "four", "annex-b"], width=10, state="readonly")
        start_code_box.grid(row=opt_row, column=1, sticky="w")
        start_code_help = ttk.Label(adv.body, text="four=4-byte, annex-b=Annex B", font=("Arial", 8), foreground="gray")
        start_code_help.grid(row=opt_row, column=2, sticky="w", padx=(5,0))
        opt_row += 1

        # Raw args
        ttk.Label(self, text="Extra args (advanced):").grid(row=7, column=0, sticky="w")
        self.extra = tk.StringVar()
        ttk.Entry(self, textvariable=self.extra, width=80).grid(row=7, column=1, columnspan=3, sticky="we", pady=2)

        # Run/Cancel
        btns = ttk.Frame(self)
        btns.grid(row=8, column=0, columnspan=4, sticky="we", pady=4)
        # Primary action button
        self.run_btn = ttk.Button(btns, text="Run", command=self.run, style="Primary.TButton")
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(btns, text="Cancel", command=self.runner.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.runner.run_button = self.run_btn
        self.runner.cancel_button = self.cancel_btn

    def build_cmd(self):
        exe = self.path_picker.get()
        if not exe:
            raise ValueError("dovi_tool path is required")
        sub = self.subcmd.get().strip()
        cmd = [exe, sub]

        # I/O by subcommand
        inf = self.in_file.get()
        outf = self.out_file.get()
        if sub in ["extract-rpu", "convert", "demux", "mux", "remove", "export", "plot", "info", "editor", "inject-rpu", "generate"]:
            if inf:
                cmd += [inf]
        # outputs
        if outf:
            cmd += ["-o", outf]

        # RPU in/out
        if sub == "inject-rpu":
            rpu_in = self.rpu_in.get()
            if rpu_in:
                cmd += ["--rpu-in", rpu_in]
        if sub == "extract-rpu":
            rpu_out = self.rpu_out.get()
            if rpu_out:
                cmd += ["-o", rpu_out]

        # global options - build them in the correct order
        global_opts = []
        if self.mode.get():
            global_opts.extend(["-m", self.mode.get()])
        if self.crop.get():
            global_opts.append("-c")
        if self.drop_hdr10p.get():
            global_opts.append("--drop-hdr10plus")
        editc = self.edit_cfg.get()
        if editc:
            global_opts.extend(["--edit-config", editc])
        if self.start_code.get():
            global_opts.extend(["--start-code", self.start_code.get()])
        
        # Rebuild command with global options before subcommand
        if global_opts:
            cmd = [exe] + global_opts + [sub] + cmd[2:]

        # extra args
        extra = self.extra.get().strip()
        if extra:
            cmd += extra.split()

        return cmd

    def run(self):
        try:
            cmd = self.build_cmd()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.runner.run(cmd)

class Mp4MuxerTab(ttk.Frame):
    def __init__(self, master, runner: AsyncRunner, **kwargs):
        super().__init__(master, **kwargs)
        self.runner = runner
        self.inputs = []

        self.path_picker = PathPicker(self, "mp4muxer path:", default_cmd="mp4muxer")
        self.path_picker.grid(row=0, column=0, columnspan=6, sticky="we", pady=4)
        self.columnconfigure(1, weight=1)
        
        # Auto-populate mp4muxer path if it exists
        mp4muxer_path = find_exe("mp4muxer")
        if mp4muxer_path:
            self.path_picker.var.set(mp4muxer_path)
            print(f"Auto-found mp4muxer: {mp4muxer_path}")

        # Inputs area
        self.in_frame = ttk.LabelFrame(self, text="Inputs (add multiple)")
        self.in_frame.grid(row=1, column=0, columnspan=6, sticky="we", pady=4)
        self._add_input_row()

        ttk.Button(self, text="Add input", command=self._add_input_row).grid(row=2, column=0, sticky="w")

        # Output and flags
        self.out_file = FilePicker(self, "Output .mp4:", mode="save", must_exist=False)
        self.out_file.grid(row=3, column=0, columnspan=5, sticky="we", pady=2)

        self.dv_profile = tk.StringVar(value="")
        ttk.Label(self, text="--dv-profile:").grid(row=4, column=0, sticky="w")
        dv_profile_box = ttk.Combobox(self, textvariable=self.dv_profile, values=["", "4", "5", "7", "8", "9"], width=6, state="readonly")
        dv_profile_box.grid(row=4, column=1, sticky="w")
        dv_help = ttk.Label(self, text="4=BL+EL, 5=SL, 7=BL+EL+BD, 8=SL+SDR, 9=AVC", font=("Arial", 8), foreground="gray")
        dv_help.grid(row=4, column=2, sticky="w", padx=(5,0))

        self.dv_bl_compat = tk.StringVar(value="")
        ttk.Label(self, text="--dv-bl-compatible-id:").grid(row=5, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.dv_bl_compat, width=6).grid(row=5, column=1, sticky="w")
        compat_help = ttk.Label(self, text="Required for profile 8 (1-4)", font=("Arial", 8), foreground="gray")
        compat_help.grid(row=5, column=2, sticky="w", padx=(5,0))

        self.brands = tk.StringVar(value="mp42,iso6,isom,msdh,dby1")
        ttk.Label(self, text="--mpeg4-comp-brand:").grid(row=6, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.brands, width=40).grid(row=6, column=1, columnspan=2, sticky="we")
        brands_help = ttk.Label(self, text="Comma-separated brand list", font=("Arial", 8), foreground="gray")
        brands_help.grid(row=6, column=3, sticky="w", padx=(5,0))

        self.hvc1flag = tk.BooleanVar(self, False)
        self.dvh1flag = tk.BooleanVar(self, False)
        self.overwrite = tk.BooleanVar(self, True)
        ttk.Checkbutton(self, text="--hvc1flag 0 (Use hvc1 sample entry)", variable=self.hvc1flag).grid(row=7, column=0, sticky="w")
        ttk.Checkbutton(self, text="--dvh1flag 0 (Use dvh1 sample entry)", variable=self.dvh1flag).grid(row=7, column=1, sticky="w")
        ttk.Checkbutton(self, text="--overwrite (Overwrite existing file)", variable=self.overwrite).grid(row=7, column=2, sticky="w")

        ttk.Label(self, text="Extra args (advanced):").grid(row=8, column=0, sticky="w")
        self.extra = tk.StringVar()
        ttk.Entry(self, textvariable=self.extra, width=80).grid(row=8, column=1, columnspan=5, sticky="we", pady=2)

        btns = ttk.Frame(self)
        btns.grid(row=9, column=0, columnspan=6, sticky="we", pady=4)
        # Primary action button
        self.run_btn = ttk.Button(btns, text="Run", command=self.run, style="Primary.TButton")
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(btns, text="Cancel", command=self.runner.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.runner.run_button = self.run_btn
        self.runner.cancel_button = self.cancel_btn

    def _add_input_row(self):
        row = len(self.inputs)
        frame = ttk.Frame(self.in_frame)
        frame.grid(row=row, column=0, sticky="we", padx=4, pady=2)
        fp = FilePicker(frame, f"Input {row}:", mode="open", must_exist=True)
        fp.grid(row=0, column=0, columnspan=3, sticky="we")
        lang = tk.StringVar()
        tscale = tk.StringVar()
        fr = tk.StringVar()
        ttk.Entry(frame, textvariable=lang, width=8)
        ttk.Label(frame, text="--media-lang").grid(row=0, column=3)
        ttk.Entry(frame, textvariable=lang, width=8).grid(row=0, column=4)
        ttk.Label(frame, text="--media-timescale").grid(row=0, column=5)
        ttk.Entry(frame, textvariable=tscale, width=8).grid(row=0, column=6)
        ttk.Label(frame, text="--input-video-frame-rate").grid(row=0, column=7)
        ttk.Entry(frame, textvariable=fr, width=10).grid(row=0, column=8)
        self.inputs.append((fp, lang, tscale, fr))

    def build_cmd(self):
        exe = self.path_picker.get()
        if not exe:
            raise ValueError("mp4muxer path is required")
        cmd = [exe]

        for fp, lang, tscale, fr in self.inputs:
            f = fp.get()
            if f:
                cmd += ["-i", f]
                if lang.get().strip():
                    cmd += ["--media-lang", lang.get().strip()]
                if tscale.get().strip():
                    cmd += ["--media-timescale", tscale.get().strip()]
                if fr.get().strip():
                    cmd += ["--input-video-frame-rate", fr.get().strip()]

        out = self.out_file.get()
        if out:
            cmd += ["-o", out]

        if self.dv_profile.get():
            cmd += ["--dv-profile", self.dv_profile.get()]
        if self.dv_bl_compat.get().strip():
            cmd += ["--dv-bl-compatible-id", self.dv_bl_compat.get().strip()]
        if self.brands.get().strip():
            cmd += ["--mpeg4-comp-brand", self.brands.get().strip()]
        if self.hvc1flag.get():
            cmd += ["--hvc1flag", "0"]
        if self.dvh1flag.get():
            cmd += ["--dvh1flag", "0"]
        if self.overwrite.get():
            cmd += ["--overwrite"]

        extra = self.extra.get().strip()
        if extra:
            cmd += extra.split()

        return cmd

    def run(self):
        try:
            cmd = self.build_cmd()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.runner.run(cmd)

class FFmpegTab(ttk.Frame):
    def __init__(self, master, runner: AsyncRunner, **kwargs):
        super().__init__(master, **kwargs)
        self.runner = runner

        # Tool path
        self.path_picker = PathPicker(self, "ffmpeg path:", default_cmd="ffmpeg")
        self.path_picker.grid(row=0, column=0, columnspan=4, sticky="we", pady=4)
        self.columnconfigure(1, weight=1)
        
        # Auto-populate ffmpeg path if it exists
        ffmpeg_path = find_exe("ffmpeg")
        if ffmpeg_path:
            self.path_picker.var.set(ffmpeg_path)
            print(f"Auto-found ffmpeg: {ffmpeg_path}")

        # Operation type
        ttk.Label(self, text="Operation:").grid(row=1, column=0, sticky="w")
        self.operation = tk.StringVar(value="convert")
        op_box = ttk.Combobox(self, textvariable=self.operation, values=["convert", "extract_audio", "extract_video", "merge", "info", "custom"], state="readonly", width=15)
        op_box.grid(row=1, column=1, sticky="w")
        op_help = ttk.Label(self, text="convert=Convert, extract_audio=Audio only, extract_video=Video only, merge=Combine, info=Analyze, custom=Raw command", font=("Arial", 8), foreground="gray")
        op_help.grid(row=1, column=2, sticky="w", padx=(5,0))

        # Input files
        self.input_file = FilePicker(self, "Input file:", mode="open", must_exist=True)
        self.input_file.grid(row=2, column=0, columnspan=3, sticky="we", pady=2)
        
        self.input2_file = FilePicker(self, "Input 2 (for merge):", mode="open", must_exist=True)
        self.input2_file.grid(row=3, column=0, columnspan=3, sticky="we", pady=2)

        # Output file
        self.output_file = FilePicker(self, "Output file:", mode="save", must_exist=False)
        self.output_file.grid(row=4, column=0, columnspan=3, sticky="we", pady=2)

        # Video settings
        video_frame = ttk.LabelFrame(self, text="Video Settings")
        video_frame.grid(row=5, column=0, columnspan=4, sticky="we", pady=4)
        
        # Codec
        ttk.Label(video_frame, text="Video Codec:").grid(row=0, column=0, sticky="w")
        self.video_codec = tk.StringVar(value="")
        vcodec_box = ttk.Combobox(video_frame, textvariable=self.video_codec, values=["", "libx264", "libx265", "copy", "libvpx-vp9", "libaom-av1"], width=12, state="readonly")
        vcodec_box.grid(row=0, column=1, sticky="w")
        vcodec_help = ttk.Label(video_frame, text="libx264=H.264, libx265=H.265, copy=No re-encode", font=("Arial", 8), foreground="gray")
        vcodec_help.grid(row=0, column=2, sticky="w", padx=(5,0))

        # Quality
        ttk.Label(video_frame, text="Quality:").grid(row=1, column=0, sticky="w")
        self.quality = tk.StringVar(value="")
        quality_box = ttk.Combobox(video_frame, textvariable=self.quality, values=["", "18", "20", "22", "24", "26", "28", "30"], width=8, state="readonly")
        quality_box.grid(row=1, column=1, sticky="w")
        quality_help = ttk.Label(video_frame, text="18=Best, 28=Good, 30=OK (lower=better)", font=("Arial", 8), foreground="gray")
        quality_help.grid(row=1, column=2, sticky="w", padx=(5,0))

        # Resolution
        ttk.Label(video_frame, text="Resolution:").grid(row=2, column=0, sticky="w")
        self.resolution = tk.StringVar(value="")
        res_box = ttk.Combobox(video_frame, textvariable=self.resolution, values=["", "1920x1080", "1280x720", "3840x2160", "2560x1440", "854x480"], width=12, state="readonly")
        res_box.grid(row=2, column=1, sticky="w")
        res_help = ttk.Label(video_frame, text="1920x1080=1080p, 3840x2160=4K", font=("Arial", 8), foreground="gray")
        res_help.grid(row=2, column=2, sticky="w", padx=(5,0))

        # Audio settings
        audio_frame = ttk.LabelFrame(self, text="Audio Settings")
        audio_frame.grid(row=6, column=0, columnspan=4, sticky="we", pady=4)
        
        # Audio codec
        ttk.Label(audio_frame, text="Audio Codec:").grid(row=0, column=0, sticky="w")
        self.audio_codec = tk.StringVar(value="")
        acodec_box = ttk.Combobox(audio_frame, textvariable=self.audio_codec, values=["", "aac", "mp3", "ac3", "eac3", "copy"], width=12, state="readonly")
        acodec_box.grid(row=0, column=1, sticky="w")
        acodec_help = ttk.Label(audio_frame, text="aac=Modern, mp3=Compatible, copy=No re-encode", font=("Arial", 8), foreground="gray")
        acodec_help.grid(row=0, column=2, sticky="w", padx=(5,0))

        # Audio bitrate
        ttk.Label(audio_frame, text="Audio Bitrate:").grid(row=1, column=0, sticky="w")
        self.audio_bitrate = tk.StringVar(value="")
        abitrate_box = ttk.Combobox(audio_frame, textvariable=self.audio_bitrate, values=["", "128k", "192k", "256k", "320k", "512k"], width=8, state="readonly")
        abitrate_box.grid(row=1, column=1, sticky="w")
        abitrate_help = ttk.Label(audio_frame, text="128k=Good, 320k=High quality", font=("Arial", 8), foreground="gray")
        abitrate_help.grid(row=1, column=2, sticky="w", padx=(5,0))

        # Preset
        ttk.Label(audio_frame, text="Preset:").grid(row=2, column=0, sticky="w")
        self.preset = tk.StringVar(value="")
        preset_box = ttk.Combobox(audio_frame, textvariable=self.preset, values=["", "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"], width=12, state="readonly")
        preset_box.grid(row=2, column=1, sticky="w")
        preset_help = ttk.Label(audio_frame, text="ultrafast=Fast, slow=Better quality", font=("Arial", 8), foreground="gray")
        preset_help.grid(row=2, column=2, sticky="w", padx=(5,0))

        # Custom command
        ttk.Label(self, text="Custom FFmpeg command:").grid(row=7, column=0, sticky="w")
        self.custom_cmd = tk.StringVar()
        ttk.Entry(self, textvariable=self.custom_cmd, width=80).grid(row=7, column=1, columnspan=3, sticky="we", pady=2)
        custom_help = ttk.Label(self, text="Override all settings above. Use full ffmpeg command without 'ffmpeg'", font=("Arial", 8), foreground="gray")
        custom_help.grid(row=8, column=0, columnspan=4, sticky="w")

        # Run/Cancel buttons
        btns = ttk.Frame(self)
        btns.grid(row=9, column=0, columnspan=4, sticky="we", pady=4)
        # Primary action button
        self.run_btn = ttk.Button(btns, text="Run", command=self.run, style="Primary.TButton")
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(btns, text="Cancel", command=self.runner.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.runner.run_button = self.run_btn
        self.runner.cancel_button = self.cancel_btn

    def build_cmd(self):
        exe = self.path_picker.get()
        if not exe:
            raise ValueError("ffmpeg path is required")
        
        # Check for custom command
        custom = self.custom_cmd.get().strip()
        if custom:
            return [exe] + custom.split()
        
        # Build command based on operation
        operation = self.operation.get()
        cmd = [exe]
        
        # Input file
        input_file = self.input_file.get()
        if not input_file:
            raise ValueError("Input file is required")
        cmd += ["-i", input_file]
        
        # Second input for merge
        if operation == "merge":
            input2 = self.input2_file.get()
            if input2:
                cmd += ["-i", input2]
        
        # Video settings
        if operation in ["convert", "extract_video", "merge"]:
            vcodec = self.video_codec.get()
            if vcodec:
                cmd += ["-c:v", vcodec]
            
            quality = self.quality.get()
            if quality:
                cmd += ["-crf", quality]
            
            resolution = self.resolution.get()
            if resolution:
                cmd += ["-s", resolution]
            
            preset = self.preset.get()
            if preset:
                cmd += ["-preset", preset]
        
        # Audio settings
        if operation in ["convert", "extract_audio", "merge"]:
            acodec = self.audio_codec.get()
            if acodec:
                cmd += ["-c:a", acodec]
            
            abitrate = self.audio_bitrate.get()
            if abitrate:
                cmd += ["-b:a", abitrate]
        
        # Operation-specific settings
        if operation == "extract_audio":
            cmd += ["-vn"]  # No video
        elif operation == "extract_video":
            cmd += ["-an"]  # No audio
        elif operation == "info":
            cmd = [exe, "-i", input_file]
            return cmd
        
        # Output file
        output_file = self.output_file.get()
        if not output_file:
            raise ValueError("Output file is required")
        cmd += [output_file]
        
        return cmd

    def run(self):
        try:
            cmd = self.build_cmd()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.runner.run(cmd)

class MKVToolNixTab(ttk.Frame):
    def __init__(self, master, runner: AsyncRunner, **kwargs):
        super().__init__(master, **kwargs)
        self.runner = runner

        self.mkvmerge = PathPicker(self, "mkvmerge path:", default_cmd="mkvmerge")
        self.mkvmerge.grid(row=0, column=0, columnspan=4, sticky="we", pady=2)
        self.mkvextract = PathPicker(self, "mkvextract path:", default_cmd="mkvextract")
        self.mkvextract.grid(row=1, column=0, columnspan=4, sticky="we", pady=2)
        self.mkvinfo = PathPicker(self, "mkvinfo path:", default_cmd="mkvinfo")
        self.mkvinfo.grid(row=2, column=0, columnspan=4, sticky="we", pady=2)
        self.mkvpropedit = PathPicker(self, "mkvpropedit path:", default_cmd="mkvpropedit")
        self.mkvpropedit.grid(row=3, column=0, columnspan=4, sticky="we", pady=2)
        self.columnconfigure(1, weight=1)
        
        # Auto-populate tool paths if they exist in PATH
        self.auto_find_tools()

        ttk.Label(self, text="Tool:").grid(row=4, column=0, sticky="w")
        self.tool = tk.StringVar(value="mkvmerge")
        tool_box = ttk.Combobox(self, textvariable=self.tool, values=["mkvmerge", "mkvextract", "mkvinfo", "mkvpropedit"], state="readonly", width=12)
        tool_box.grid(row=4, column=1, sticky="w")
        tool_help = ttk.Label(self, text="merge=Create, extract=Extract, info=Analyze, propedit=Edit", font=("Arial", 8), foreground="gray")
        tool_help.grid(row=4, column=2, sticky="w", padx=(5,0))

        self.src = FilePicker(self, "Source:", mode="open", must_exist=True)
        self.src.grid(row=5, column=0, columnspan=4, sticky="we", pady=2)

        self.out = FilePicker(self, "Output (where applicable):", mode="save", must_exist=False)
        self.out.grid(row=6, column=0, columnspan=4, sticky="we", pady=2)

        ttk.Label(self, text="Args (raw, appended after tool and before files):").grid(row=7, column=0, sticky="w")
        self.args = tk.StringVar()
        ttk.Entry(self, textvariable=self.args, width=80).grid(row=7, column=1, columnspan=3, sticky="we")
        args_help = ttk.Label(self, text="Examples: 'tracks 0:video.h264 1:audio.aac' or 'chapters chapters.xml'", font=("Arial", 8), foreground="gray")
        args_help.grid(row=8, column=0, columnspan=4, sticky="w")

        btns = ttk.Frame(self)
        btns.grid(row=9, column=0, columnspan=4, sticky="we", pady=4)
        # Primary action button
        self.run_btn = ttk.Button(btns, text="Run", command=self.run, style="Primary.TButton")
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(btns, text="Cancel", command=self.runner.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.runner.run_button = self.run_btn
        self.runner.cancel_button = self.cancel_btn

    def auto_find_tools(self):
        """Auto-populate tool paths if they exist in PATH, current dir, or subdirs."""
        tools = [
            ("mkvmerge", self.mkvmerge),
            ("mkvextract", self.mkvextract), 
            ("mkvinfo", self.mkvinfo),
            ("mkvpropedit", self.mkvpropedit)
        ]
        
        for tool_name, path_picker in tools:
            tool_path = find_exe(tool_name)
            if tool_path:
                path_picker.var.set(tool_path)
                print(f"Auto-found {tool_name}: {tool_path}")

    def pick_tool(self):
        t = self.tool.get()
        if t == "mkvmerge":
            return self.mkvmerge.get()
        if t == "mkvextract":
            return self.mkvextract.get()
        if t == "mkvinfo":
            return self.mkvinfo.get()
        if t == "mkvpropedit":
            return self.mkvpropedit.get()
        return None

    def run(self):
        exe = self.pick_tool()
        if not exe:
            messagebox.showerror("Error", f"{self.tool.get()} path is required. Please set the path using 'Find in PATH' or browse to the executable.")
            return
        src = self.src.get()
        if not src:
            messagebox.showerror("Error", "Source file is required")
            return
        args = self.args.get().strip().split() if self.args.get().strip() else []
        out = self.out.get()

        # Debug: Log what we're trying to execute
        print(f"Debug: Tool = {self.tool.get()}")
        print(f"Debug: Executable = {exe}")
        print(f"Debug: Source = {src}")
        print(f"Debug: Args = {args}")

        # Validate executable exists
        if not os.path.isfile(exe):
            messagebox.showerror("Error", f"Executable not found: {exe}")
            return

        cmd = [exe] + args
        # For mkvmerge, append -o out if provided
        if self.tool.get() == "mkvmerge" and out:
            cmd += ["-o", out]
        # mkvpropedit expects the file before actions; mkvextract has modes; mkvinfo just takes file
        # Here we adopt a simple pattern: put source at the end for mkvmerge/info; for others we place src first
        if self.tool.get() in ["mkvinfo", "mkvmerge"]:
            if src:
                cmd += [src]
        else:
            # mkvextract/mkvpropedit: put src immediately after exe
            cmd = [exe]
            if src:
                cmd += [src]
            cmd += args
            # mkvextract modes and output targets must be expressed via args field

        if self.tool.get() == "mkvpropedit" and out:
            # Not typically used; mkvpropedit edits in-place; ignore out
            pass

        self.runner.run(cmd)

class LogPane(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.text = tk.Text(self, height=14, wrap="word", state="disabled")
        self.text.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

def load_presets():
    if os.path.isfile(DEFAULT_PRESET_FILE):
        try:
            with open(DEFAULT_PRESET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_presets(data):
    try:
        with open(DEFAULT_PRESET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        messagebox.showerror("Save presets", str(e))

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x700")
        self.minsize(980, 620)
        # ------------------------------------------------------------------
        # Window icon setup
        # Priority (Windows): app.ico -> favicon.ico -> PNG set via iconphoto
        # On other platforms: PNG set via iconphoto (multi-resolution hint)
        # Keep references so they are not garbage collected.
        # ------------------------------------------------------------------
        self._icon_images = []
        try:
            debug_icons = os.environ.get("DEBUG_ICONS", "0") == "1"
            def dbg(msg):
                if debug_icons:
                    print(f"[ICON] {msg}")

            if os.name == 'nt':  # Prefer .ico for proper taskbar representation
                for candidate in ('app.ico', 'favicon.ico'):
                    p = resource_path(candidate)
                    dbg(f"Checking ICO: {p} exists={os.path.exists(p)}")
                    if os.path.exists(p):
                        try:
                            self.iconbitmap(p)
                            dbg(f"Loaded ICO: {p}")
                            break
                        except Exception as e:
                            dbg(f"Failed ICO load {p}: {e}")
            # PNG fallbacks / multi-size stacking (works cross-platform & alt-tab on some WMs)
            png_candidates = [
                'apple-touch-icon.png',   # 180x180
                'favicon-256.png',        # Optional 256x256 if provided
                'favicon-128.png',        # Optional 128x128
                'favicon-64.png',         # Optional 64x64
                'favicon-48.png',         # Optional 48x48
                'favicon-32x32.png',      # 32x32
                'favicon-16x16.png',      # 16x16
            ]
            for fn in png_candidates:
                p = resource_path(fn)
                if os.path.exists(p):
                    try:
                        img = tk.PhotoImage(file=p)
                        self._icon_images.append(img)
                        dbg(f"Loaded PNG: {p} size={img.width()}x{img.height()}")
                    except Exception as e:
                        dbg(f"Failed PNG load {p}: {e}")
            if self._icon_images:
                # True applies to this window and future toplevels
                self.iconphoto(True, *self._icon_images)
                dbg(f"Applied {len(self._icon_images)} PNG icon(s)")
            else:
                dbg("No PNG icons loaded")
        except Exception as e:
            # Silently ignore icon issues to avoid crashing the GUI, but optional debug
            if os.environ.get("DEBUG_ICONS") == "1":
                print(f"[ICON] Exception: {e}")

        # Theme / style setup
        self.style = ttk.Style()
        base = "clam" if "clam" in self.style.theme_names() else self.style.theme_use()
        self.style.theme_use(base)
        self.current_theme = DEFAULT_THEME
        self.font_small = ("Segoe UI", 8)
        self.font_base = ("Segoe UI", 9)
        self.option_add("*Font", self.font_base)

        # Layout: top tabs + bottom log
        top = ttk.Frame(self)
        top.pack(fill="both", expand=True)
        bottom = ttk.Frame(self)
        bottom.pack(fill="x")

        nb = ttk.Notebook(top)
        nb.pack(fill="both", expand=True)

        # Shared log pane
        log_pane = LogPane(self)
        log_pane.pack(fill="both", expand=False, padx=6, pady=6)
        dummy_btn = ttk.Button(self, text="Run")
        dummy_cancel = ttk.Button(self, text="Cancel")
        self.runner = AsyncRunner(log_pane.text, dummy_btn, dummy_cancel)

        self.dovi_tab = DoviToolTab(nb, self.runner)
        self.mp4_tab = Mp4MuxerTab(nb, self.runner)
        self.mkv_tab = MKVToolNixTab(nb, self.runner)
        self.ffmpeg_tab = FFmpegTab(nb, self.runner)

        nb.add(self.dovi_tab, text="Dolby Vision (dovi_tool)")
        nb.add(self.mp4_tab, text="MP4 Muxer (mp4muxer)")
        nb.add(self.mkv_tab, text="Matroska (MKVToolNix)")
        nb.add(self.ffmpeg_tab, text="FFmpeg")

        # Menus
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label="Load presets", command=self.load_presets)
        filem.add_command(label="Save presets", command=self.save_presets)
        filem.add_separator()
        filem.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filem)
        themem = tk.Menu(menubar, tearoff=0)
        self.theme_var = tk.StringVar(value=self.current_theme)
        for name in THEMES.keys():
            themem.add_radiobutton(label=name, value=name, variable=self.theme_var, command=self._theme_changed)
        menubar.add_cascade(label="Theme", menu=themem)
        toolsm = tk.Menu(menubar, tearoff=0)
        toolsm.add_command(label="Check external tools", command=self.check_external_tools)
        menubar.add_cascade(label="Tools", menu=toolsm)
        self.config(menu=menubar)

        self.presets = load_presets()
        self.apply_theme(self.current_theme)
        # Defer tool check until mainloop idle so window appears quickly
        self.after(250, self.check_external_tools)
        # ---------------- External Tools Check -----------------
    def check_external_tools(self):
        """Verify required external command-line tools exist; prompt user if missing."""
        # (exe_name, friendly, url)
        tools = [
            ("dovi_tool", "dovi_tool (Dolby Vision)", "https://github.com/quietvoid/dovi_tool/releases"),
            ("mp4muxer", "mp4muxer", "https://github.com/DolbyLaboratories/dlb_mp4base/blob/master/bin"),
            ("mkvmerge", "mkvmerge (MKVToolNix)", "https://mkvtoolnix.download/downloads.html"),
            ("mkvextract", "mkvextract (MKVToolNix)", "https://mkvtoolnix.download/downloads.html"),
            ("mkvinfo", "mkvinfo (MKVToolNix)", "https://mkvtoolnix.download/downloads.html"),
            ("mkvpropedit", "mkvpropedit (MKVToolNix)", "https://mkvtoolnix.download/downloads.html"),
            ("ffmpeg", "FFmpeg", "https://ffmpeg.org/download.html"),
        ]

        missing = []
        found_any = False
        for exe, friendly, url in tools:
            # Attempt to locate;
            located = find_exe(exe)
            if located:
                found_any = True
                # Auto-populate path pickers if empty
                try:
                    if exe == "dovi_tool" and not self.dovi_tab.path_picker.var.get():
                        self.dovi_tab.path_picker.var.set(located)
                    elif exe == "mp4muxer" and not self.mp4_tab.path_picker.var.get():
                        self.mp4_tab.path_picker.var.set(located)
                    elif exe == "ffmpeg" and not self.ffmpeg_tab.path_picker.var.get():
                        self.ffmpeg_tab.path_picker.var.set(located)
                    elif exe == "mkvmerge" and not self.mkv_tab.mkvmerge.var.get():
                        self.mkv_tab.mkvmerge.var.set(located)
                    elif exe == "mkvextract" and not self.mkv_tab.mkvextract.var.get():
                        self.mkv_tab.mkvextract.var.set(located)
                    elif exe == "mkvinfo" and not self.mkv_tab.mkvinfo.var.get():
                        self.mkv_tab.mkvinfo.var.set(located)
                    elif exe == "mkvpropedit" and not self.mkv_tab.mkvpropedit.var.get():
                        self.mkv_tab.mkvpropedit.var.set(located)
                except Exception:
                    pass
            else:
                missing.append((exe, friendly, url))

        if not missing:
            # Optionally inform only if user explicitly used menu action
            # Avoid noisy popup at startup if everything is fine.
            return

        self._show_missing_tools_dialog(missing)

    def _show_missing_tools_dialog(self, missing):
        win = tk.Toplevel(self)
        win.title("Missing External Tools")
        win.transient(self)
        win.grab_set()
        msg = tk.Label(win, text="Some required/optional tools were not found. Download and install them, then restart or use the path pickers.", wraplength=520, justify="left")
        msg.pack(anchor="w", padx=12, pady=(12,6))

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=12)

        def open_url(url):
            try:
                webbrowser.open_new_tab(url)
            except Exception:
                messagebox.showerror("Open URL", f"Could not open browser for: {url}")

        for exe, friendly, url in missing:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=2)
            lbl = ttk.Label(row, text=friendly)
            lbl.pack(side="left")
            link = tk.Label(row, text="Download", fg="#2563EB", cursor="hand2")
            link.pack(side="right")
            link.bind("<Button-1>", lambda e, u=url: open_url(u))
            # Hover underline
            link.bind("<Enter>", lambda e, w=link: w.config(font=("Segoe UI", 9, "underline")))
            link.bind("<Leave>", lambda e, w=link: w.config(font=("Segoe UI", 9, "normal")))

        btns = ttk.Frame(win)
        btns.pack(fill="x", pady=10, padx=12)
        def open_all():
            for _, _, url in missing:
                open_url(url)
        ttk.Button(btns, text="Open All Download Pages", command=open_all, style="Primary.TButton").pack(side="left")
        ttk.Button(btns, text="Close", command=win.destroy).pack(side="right")
        win.geometry("640x400")
        win.minsize(520, 300)
        win.focus_set()

    # ---------------- Theming -----------------
    def _theme_changed(self):
        self.apply_theme(self.theme_var.get())

    def apply_theme(self, name: str):
        if name not in THEMES:
            return
        self.current_theme = name
        t = THEMES[name]
        # Root & general backgrounds
        self.configure(bg=t["bg"])
        # Token extraction
        fg = t["fg"]; subtle = t["subtle_fg"]; muted = t["muted_fg"]
        accent = t["accent"]; accent_h = t["accent_hover"]; accent_p = t["accent_pressed"]
        entry_bg = t["entry_bg"]; entry_border = t["entry_border"]; border = t["border"]
        # Base containers & labels
        self.style.configure("TFrame", background=t["bg"])
        self.style.configure("TLabel", background=t["bg"], foreground=fg)
        self.style.configure("TLabelframe", background=t["bg"], foreground=fg, bordercolor=border, relief="groove")
        self.style.configure("TLabelframe.Label", background=t["bg"], foreground=fg, font=("Segoe UI", 9, "bold"))
        # Form controls
        self.style.configure("TCheckbutton", background=t["bg"], foreground=fg)
        self.style.configure("TRadiobutton", background=t["bg"], foreground=fg)
        # Notebook / tabs
        self.style.configure("TNotebook", background=t["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(10, 4), font=("Segoe UI", 9), focuscolor=t["bg"])
        self.style.map("TNotebook.Tab", background=[("selected", t["surface2"])], foreground=[("disabled", muted)])
        # Secondary (default) button style
        self.style.configure("TButton", background=t["secondary_bg"], foreground=fg, borderwidth=1)
        self.style.map(
            "TButton",
            background=[
                ("pressed", t["secondary_pressed"]),
                ("active", t["secondary_hover"]),
                ("disabled", t["disabled_bg"]),
            ],
            foreground=[("disabled", t["disabled_fg"])],
        )
        # Primary button style
        self.style.configure("Primary.TButton", background=accent, foreground=t["accent_on"], borderwidth=1)
        self.style.map(
            "Primary.TButton",
            background=[
                ("pressed", accent_p),
                ("active", accent_h),
                ("disabled", t["disabled_bg"]),
            ],
            foreground=[("disabled", t["disabled_fg"])],
        )
        # Inputs / entries
        self.style.configure("TEntry", fieldbackground=entry_bg, background=entry_bg, foreground=fg, bordercolor=entry_border)
        self.style.map("TEntry", fieldbackground=[("disabled", t["disabled_bg"])], foreground=[("disabled", t["disabled_fg"])])
        # Combobox
        self.style.configure("TCombobox", fieldbackground=entry_bg, background=entry_bg, foreground=fg)
        self.style.map("TCombobox", fieldbackground=[("disabled", t["disabled_bg"])], foreground=[("disabled", t["disabled_fg"])])
        # Scale minimal paddings globally
        self.option_add("*TCombobox*Listbox.background", entry_bg)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        # Text widget(s)
        self._apply_recursive_widget_palette(self, t)

    def _apply_recursive_widget_palette(self, widget, theme):
        for child in widget.winfo_children():
            cls = child.winfo_class()
            if isinstance(child, tk.Text):
                child.configure(bg=theme["text_bg"], fg=theme["text_fg"], insertbackground=theme["accent"], selectbackground=theme["select_bg"], selectforeground=theme["select_fg"])
            elif isinstance(child, (tk.Frame, ttk.Frame, ttk.Notebook)):
                try:
                    child.configure(bg=theme["bg"])
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Menu):
                try:
                    child.configure(bg=theme["bg"], fg=theme["fg"], activebackground=theme["accent"], activeforeground=theme["select_fg"])
                except tk.TclError:
                    pass
            # Labels & others auto styled by ttk.Style
            self._apply_recursive_widget_palette(child, theme)

    def gather_state(self):
        state = {
            "dovi": {
                "path": self.dovi_tab.path_picker.var.get(),
                "subcmd": self.dovi_tab.subcmd.get(),
                "in": self.dovi_tab.in_file.var.get(),
                "out": self.dovi_tab.out_file.var.get(),
                "rpu_in": self.dovi_tab.rpu_in.var.get(),
                "rpu_out": self.dovi_tab.rpu_out.var.get(),
                "mode": self.dovi_tab.mode.get(),
                "crop": self.dovi_tab.crop.get(),
                "drop_hdr10p": self.dovi_tab.drop_hdr10p.get(),
                "edit_cfg": self.dovi_tab.edit_cfg.var.get(),
                "start_code": self.dovi_tab.start_code.get(),
                "extra": self.dovi_tab.extra.get(),
            },
            "mp4": {
                "path": self.mp4_tab.path_picker.var.get(),
                "out": self.mp4_tab.out_file.var.get(),
                "dv_profile": self.mp4_tab.dv_profile.get(),
                "dv_bl_compat": self.mp4_tab.dv_bl_compat.get(),
                "brands": self.mp4_tab.brands.get(),
                "hvc1flag": self.mp4_tab.hvc1flag.get(),
                "dvh1flag": self.mp4_tab.dvh1flag.get(),
                "overwrite": self.mp4_tab.overwrite.get(),
                "extra": self.mp4_tab.extra.get(),
                "inputs": [
                    {
                        "file": fp.var.get(),
                        "lang": lang.get(),
                        "tscale": tscale.get(),
                        "fr": fr.get(),
                    }
                    for (fp, lang, tscale, fr) in self.mp4_tab.inputs
                ]
            },
            "mkv": {
                "mkvmerge": self.mkv_tab.mkvmerge.var.get(),
                "mkvextract": self.mkv_tab.mkvextract.var.get(),
                "mkvinfo": self.mkv_tab.mkvinfo.var.get(),
                "mkvpropedit": self.mkv_tab.mkvpropedit.var.get(),
                "tool": self.mkv_tab.tool.get(),
                "src": self.mkv_tab.src.var.get(),
                "out": self.mkv_tab.out.var.get(),
                "args": self.mkv_tab.args.get(),
            },
            "ffmpeg": {
                "path": self.ffmpeg_tab.path_picker.var.get(),
                "operation": self.ffmpeg_tab.operation.get(),
                "input": self.ffmpeg_tab.input_file.var.get(),
                "input2": self.ffmpeg_tab.input2_file.var.get(),
                "output": self.ffmpeg_tab.output_file.var.get(),
                "video_codec": self.ffmpeg_tab.video_codec.get(),
                "quality": self.ffmpeg_tab.quality.get(),
                "resolution": self.ffmpeg_tab.resolution.get(),
                "audio_codec": self.ffmpeg_tab.audio_codec.get(),
                "audio_bitrate": self.ffmpeg_tab.audio_bitrate.get(),
                "preset": self.ffmpeg_tab.preset.get(),
                "custom_cmd": self.ffmpeg_tab.custom_cmd.get(),
            }
        }
        return state

    def apply_state(self, state):
        try:
            d = state.get("dovi", {})
            self.dovi_tab.path_picker.var.set(d.get("path", ""))
            self.dovi_tab.subcmd.set(d.get("subcmd", "extract-rpu"))
            self.dovi_tab.in_file.var.set(d.get("in", ""))
            self.dovi_tab.out_file.var.set(d.get("out", ""))
            self.dovi_tab.rpu_in.var.set(d.get("rpu_in", ""))
            self.dovi_tab.rpu_out.var.set(d.get("rpu_out", ""))
            self.dovi_tab.mode.set(d.get("mode", ""))
            self.dovi_tab.crop.set(bool(d.get("crop", False)))
            self.dovi_tab.drop_hdr10p.set(bool(d.get("drop_hdr10p", False)))
            self.dovi_tab.edit_cfg.var.set(d.get("edit_cfg", ""))
            self.dovi_tab.start_code.set(d.get("start_code", ""))
            self.dovi_tab.extra.set(d.get("extra", ""))

            m = state.get("mp4", {})
            self.mp4_tab.path_picker.var.set(m.get("path", ""))
            self.mp4_tab.out_file.var.set(m.get("out", ""))
            self.mp4_tab.dv_profile.set(m.get("dv_profile", ""))
            self.mp4_tab.dv_bl_compat.set(m.get("dv_bl_compat", ""))
            self.mp4_tab.brands.set(m.get("brands", "mp42,iso6,isom,msdh,dby1"))
            self.mp4_tab.hvc1flag.set(bool(m.get("hvc1flag", False)))
            self.mp4_tab.dvh1flag.set(bool(m.get("dvh1flag", False)))
            self.mp4_tab.overwrite.set(bool(m.get("overwrite", True)))
            self.mp4_tab.extra.set(m.get("extra", ""))
            # reset inputs
            for child in self.mp4_tab.in_frame.winfo_children():
                child.destroy()
            self.mp4_tab.inputs = []
            for it in m.get("inputs", []):
                self.mp4_tab._add_input_row()
                fp, lang, tscale, fr = self.mp4_tab.inputs[-1]
                fp.var.set(it.get("file", ""))
                lang.set(it.get("lang", ""))
                tscale.set(it.get("tscale", ""))
                fr.set(it.get("fr", ""))

            k = state.get("mkv", {})
            self.mkv_tab.mkvmerge.var.set(k.get("mkvmerge", ""))
            self.mkv_tab.mkvextract.var.set(k.get("mkvextract", ""))
            self.mkv_tab.mkvinfo.var.set(k.get("mkvinfo", ""))
            self.mkv_tab.mkvpropedit.var.set(k.get("mkvpropedit", ""))
            self.mkv_tab.tool.set(k.get("tool", "mkvmerge"))
            self.mkv_tab.src.var.set(k.get("src", ""))
            self.mkv_tab.out.var.set(k.get("out", ""))
            self.mkv_tab.args.set(k.get("args", ""))

            f = state.get("ffmpeg", {})
            self.ffmpeg_tab.path_picker.var.set(f.get("path", ""))
            self.ffmpeg_tab.operation.set(f.get("operation", "convert"))
            self.ffmpeg_tab.input_file.var.set(f.get("input", ""))
            self.ffmpeg_tab.input2_file.var.set(f.get("input2", ""))
            self.ffmpeg_tab.output_file.var.set(f.get("output", ""))
            self.ffmpeg_tab.video_codec.set(f.get("video_codec", ""))
            self.ffmpeg_tab.quality.set(f.get("quality", ""))
            self.ffmpeg_tab.resolution.set(f.get("resolution", ""))
            self.ffmpeg_tab.audio_codec.set(f.get("audio_codec", ""))
            self.ffmpeg_tab.audio_bitrate.set(f.get("audio_bitrate", ""))
            self.ffmpeg_tab.preset.set(f.get("preset", ""))
            self.ffmpeg_tab.custom_cmd.set(f.get("custom_cmd", ""))

        except Exception as e:
            messagebox.showerror("Apply presets", str(e))

    def load_presets(self):
        data = load_presets()
        if not data:
            messagebox.showinfo("Presets", "No presets found.")
            return
        # pick first by default or prompt selection
        names = list(data.keys())
        name = tk.simpledialog.askstring("Load preset", f"Available: {', '.join(names)}\nEnter name:")
        if not name:
            return
        if name not in data:
            messagebox.showerror("Presets", f"Preset '{name}' not found.")
            return
        self.apply_state(data[name])

    def save_presets(self):
        name = tk.simpledialog.askstring("Save preset", "Enter preset name:")
        if not name:
            return
        data = load_presets()
        data[name] = self.gather_state()
        save_presets(data)
        messagebox.showinfo("Presets", f"Saved preset '{name}'.")

if __name__ == "__main__":
    App().mainloop()
