"""
AFOP Gear Swap Tool
====================
A GUI for swapping mgraphobject files in Avatar: Frontiers of Pandora.

How it works:
  The game resolves gear via mgraphobject file *names* in blue/graph objects/gear.
  To use an NPC/override model (e.g. Tsu'tey's head) on a base gear slot:
    1. Extract the source .mgraphobject from the game files
    2. This tool copies it into your mod folder, renamed to the target slot's name
  The game then loads the source model in place of the target gear slot.

Setup:
  Place this script alongside AFOP_Gear_Key.json.
  Optionally set DEFAULT_MOD_FOLDER below to pre-fill the mod folder path.
"""
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import shutil
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
GEAR_JSON_PATH  = "AFOP_Gear_Key.json"
PREFS_JSON_PATH = "afop_gear_swap_prefs.json"

# Pre-fill the mod folder. Leave as "" to always browse manually.
DEFAULT_MOD_FOLDER = r""   # e.g. r"C:\Games\AFOP\mods\MyMod\blue\graph objects\gear"

# ── Colours ────────────────────────────────────────────────────────────────────
BG       = "#0e0f14"
PANEL    = "#161822"
BORDER   = "#2a2d3e"
ACCENT   = "#4fc3f7"
ACCENT2  = "#80cbc4"
WARN     = "#ffb74d"
SUCCESS  = "#a5d6a7"
ERROR    = "#ef9a9a"
TEXT     = "#e8eaf6"
MUTED    = "#757997"
ENTRY_BG = "#1e2030"
BTN_BG   = "#263859"
BTN_HOV  = "#2e4470"
MONO     = "Consolas"


# ── Data ───────────────────────────────────────────────────────────────────────

def get_base_dir():
    """Return the directory of the exe (frozen) or script (dev)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def load_gear_data():
    json_path = get_base_dir() / GEAR_JSON_PATH
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f).get("gear", {})
    return {}


def load_prefs():
    prefs_path = get_base_dir() / PREFS_JSON_PATH
    if prefs_path.exists():
        try:
            with open(prefs_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_prefs(prefs: dict):
    prefs_path = get_base_dir() / PREFS_JSON_PATH
    try:
        with open(prefs_path, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)
    except Exception:
        pass


def flatten_items(gear_data):
    items = []
    for slot, entries in gear_data.items():
        for entry in entries:
            for name in entry.get("ui_names", ["(unknown)"]):
                items.append({
                    "slot":         slot,
                    "ui_name":      name,
                    "mgraphobject": entry.get("mgraphobject", []),
                    "models":       entry.get("models", []),
                    "textures":     entry.get("textures", []),
                    "all_ui_names": entry.get("ui_names", []),
                })
    return items


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_swap(src, tgt, src_file, mod_folder):
    """
    src_file   = full path to the .mgraphobject file the user picked (can be anywhere)
    mod_folder = destination: blue/graph objects/gear
    Returns (warnings, errors). Errors block execution; warnings ask for confirmation.
    """
    warnings, errors = [], []

    # Item data checks
    if not src["mgraphobject"]:
        errors.append("Source item has no mgraphobject entries in the gear key.")
    if not tgt["mgraphobject"]:
        errors.append("Target item has no mgraphobject entries in the gear key.")
    if (src["mgraphobject"] and tgt["mgraphobject"]
            and src["mgraphobject"] == tgt["mgraphobject"]):
        errors.append("Source and target share the same mgraphobject — nothing to swap.")

    # Slot mismatch
    if src["slot"] != tgt["slot"]:
        warnings.append(
            f"Slot mismatch: source is '{src['slot']}', target is '{tgt['slot']}'.\n"
            "  Cross-slot swaps may not display correctly or may crash in-game."
        )

    # Source file
    if not src_file:
        errors.append(
            "No source file selected.\n"
            "  Use 'Browse…' next to 'Source file' to locate your extracted .mgraphobject."
        )
    elif not os.path.isfile(src_file):
        errors.append(f"Source file not found:\n  {src_file}")
    else:
        # Warn if filename doesn't match expected mgraphobject names for this item
        stem = Path(src_file).stem
        expected = src["mgraphobject"]
        if expected and stem not in expected:
            warnings.append(
                f"Filename '{stem}' doesn't match expected mgraphobject name(s) for '{src['ui_name']}':\n"
                + "".join(f"    {m}\n" for m in expected)
                + "  The swap will still run — double-check you picked the right file."
            )

    # Mod folder
    if not mod_folder:
        errors.append(
            "No mod folder set.\n"
            "  Set the path to your mod's 'blue/graph objects/gear' folder."
        )
    elif not os.path.isdir(mod_folder):
        errors.append(f"Mod folder does not exist:\n  {mod_folder}")
    else:
        for mg in tgt.get("mgraphobject", []):
            dst = os.path.join(mod_folder, f"{mg}.mgraphobject")
            if os.path.exists(dst):
                warnings.append(f"Target already exists (will prompt to overwrite):\n  {mg}.mgraphobject")

    return warnings, errors


# ── Widgets ────────────────────────────────────────────────────────────────────

class SearchableList(tk.Frame):
    def __init__(self, parent, items, on_select=None, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._all_items = items
        self._on_select = on_select
        self._filtered  = []

        # Search
        sf = tk.Frame(self, bg=ENTRY_BG, highlightbackground=BORDER, highlightthickness=1)
        sf.pack(fill="x", pady=(0, 5))
        tk.Label(sf, text="⌕", bg=ENTRY_BG, fg=MUTED,
                 font=("Segoe UI", 11)).pack(side="left", padx=(7, 2))
        self._sv = tk.StringVar()
        self._sv.trace_add("write", self._refresh)
        tk.Entry(sf, textvariable=self._sv, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=ACCENT, relief="flat", font=("Segoe UI", 9), bd=0
                 ).pack(side="left", fill="x", expand=True, pady=6, padx=(0, 6))

        # Slot filter + count
        fr = tk.Frame(self, bg=BG)
        fr.pack(fill="x", pady=(0, 5))
        tk.Label(fr, text="Slot:", bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(side="left")
        slots = ["All slots"] + sorted({i["slot"] for i in items})
        self._slot_var = tk.StringVar(value="All slots")
        cb = ttk.Combobox(fr, textvariable=self._slot_var, values=slots,
                          state="readonly", width=12, font=("Segoe UI", 9))
        cb.pack(side="left", padx=(5, 0))
        cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        self._count_var = tk.StringVar()
        tk.Label(fr, textvariable=self._count_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 8)).pack(side="right")

        # Listbox
        wrap = tk.Frame(self, bg=BORDER, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        sb = tk.Scrollbar(wrap, bg=PANEL, troughcolor=BG, activebackground=ACCENT)
        sb.pack(side="right", fill="y")
        self._lb = tk.Listbox(wrap, bg=ENTRY_BG, fg=TEXT,
                               selectbackground=BTN_BG, selectforeground=ACCENT,
                               activestyle="none", relief="flat", bd=0,
                               font=("Segoe UI", 11), yscrollcommand=sb.set,
                               highlightthickness=0)
        self._lb.pack(side="left", fill="both", expand=True)
        sb.config(command=self._lb.yview)
        self._lb.bind("<<ListboxSelect>>", self._on_lb_select)
        self._refresh()

    def _refresh(self, *_):
        q    = self._sv.get().strip().lower()
        slot = self._slot_var.get()
        self._filtered = [
            i for i in self._all_items
            if (slot == "All slots" or i["slot"] == slot)
            and (not q or q in i["ui_name"].lower()
                 or any(q in mg.lower() for mg in i["mgraphobject"]))
        ]
        self._lb.delete(0, "end")
        for item in self._filtered:
            self._lb.insert("end", f"[{item['slot'].upper()}]  {item['ui_name']}")
        self._count_var.set(f"{len(self._filtered)} items")

    def _on_lb_select(self, _):
        sel = self._lb.curselection()
        if sel and self._on_select:
            self._on_select(self._filtered[sel[0]])

    def get_selected(self):
        sel = self._lb.curselection()
        return self._filtered[sel[0]] if sel else None


class ItemCard(tk.Frame):
    def __init__(self, parent, role_label, role_color, text_height=8, **kwargs):
        super().__init__(parent, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1, **kwargs)
        hdr = tk.Frame(self, bg=PANEL)
        hdr.pack(fill="x", padx=10, pady=(7, 3))
        tk.Label(hdr, text=role_label, bg=PANEL, fg=role_color,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self._slot_lbl = tk.Label(hdr, text="", bg=PANEL, fg=MUTED, font=("Segoe UI", 8))
        self._slot_lbl.pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._text = tk.Text(self, bg=PANEL, fg=TEXT, relief="flat",
                              font=(MONO, 8), bd=0, state="disabled",
                              wrap="word", padx=10, pady=7, highlightthickness=0, height=text_height)
        self._text.pack(fill="both", expand=True)
        self._text.tag_config("key",   foreground=MUTED)
        self._text.tag_config("val",   foreground=TEXT)
        self._text.tag_config("mg",    foreground=ACCENT, font=(MONO, 8, "bold"))
        self._text.tag_config("model", foreground=ACCENT2)
        self.clear()

    def clear(self):
        self._slot_lbl.config(text="")
        self._set([("key", "No item selected")])

    def show(self, item):
        self._slot_lbl.config(text=item["slot"])
        lines = [("key", "Name(s):\n")]
        for n in item["all_ui_names"]:
            lines += [("val", f"  {n}\n")]
        lines += [("key", "\nmgraphobject(s):\n")]
        for mg in item["mgraphobject"]:
            lines += [("mg", f"  {mg}.mgraphobject\n")]
        if item["models"]:
            lines += [("key", "\nModels:\n")]
            for m in item["models"]:
                lines += [("model", f"  {m}\n")]
        self._set(lines)

    def _set(self, segs):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        for tag, txt in segs:
            self._text.insert("end", txt, tag)
        self._text.config(state="disabled")


class PreviewPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1, **kwargs)
        tk.Label(self, text="Operation Preview", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 9, "bold"), padx=10, pady=7,
                 anchor="w").pack(fill="x")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._text = tk.Text(self, bg=PANEL, fg=TEXT, relief="flat",
                              font=(MONO, 8), bd=0, state="disabled",
                              wrap="word", padx=10, pady=8, highlightthickness=0, height=12)
        self._text.pack(fill="both", expand=True)
        self._text.tag_config("dim",  foreground=MUTED)
        self._text.tag_config("src",  foreground=WARN)
        self._text.tag_config("dst",  foreground=SUCCESS)
        self._text.tag_config("warn", foreground=WARN)
        self._text.tag_config("err",  foreground=ERROR)
        self._text.tag_config("hd",   foreground=ACCENT, font=(MONO, 8, "bold"))
        self.reset()

    def reset(self):
        self._set([("dim", "Select a source and target to preview.\n")])

    def show(self, src, tgt, src_file, mod_folder, warnings, errors):
        lines = []

        if errors:
            lines += [("hd", "ERRORS\n")]
            for e in errors:
                lines += [("err", f"  ✗  {e}\n")]
            lines += [("dim", "\nFix errors before executing.\n")]
            self._set(lines)
            return

        if warnings:
            lines += [("hd", "WARNINGS\n")]
            for w in warnings:
                lines += [("warn", f"  ⚠  {w}\n")]
            lines += [("dim", "\n")]

        lines += [("hd", "OPERATION\n")]
        if src_file:
            lines += [("dim", "  source  "), ("src", f"{Path(src_file).name}\n")]
        for tgt_mg in tgt["mgraphobject"]:
            lines += [("dim", "  output  "), ("dst", f"{tgt_mg}.mgraphobject\n")]
            if mod_folder and os.path.isdir(mod_folder):
                if os.path.exists(os.path.join(mod_folder, f"{tgt_mg}.mgraphobject")):
                    lines += [("warn", "           ⚠  already exists — will overwrite\n")]
        self._set(lines)

    def _set(self, segs):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        for tag, txt in segs:
            self._text.insert("end", txt, tag)
        self._text.config(state="disabled")


# ── Main App ───────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AFoP Gear Swapper | Made By: Jasper_Zebra | Version 1.0")
        self.geometry("1400x864")
        self.minsize(980, 680)
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=ENTRY_BG, background=ENTRY_BG,
                         foreground=TEXT, selectbackground=BTN_BG,
                         selectforeground=ACCENT, bordercolor=BORDER,
                         arrowcolor=ACCENT, relief="flat")
        style.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)])

        gear_data      = load_gear_data()
        self._items    = flatten_items(gear_data)
        self._src      = None
        self._tgt      = None
        self._prefs    = load_prefs()
        # _src_file is the actual file on disk (from anywhere — game files, temp folder, etc.)
        # _mod_folder is the destination: blue/graph objects/gear

        self._build_ui()

        if not self._items:
            self._status(
                f"⚠  {GEAR_JSON_PATH} not found next to this script — gear lists are empty.",
                color=WARN)

    def _build_ui(self):
        # ── Title bar ──────────────────────────────────────────────────────────
        bar = tk.Frame(self, bg=PANEL, height=48)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="AFOP  GEAR  SWAP  TOOL",
                 bg=PANEL, fg=ACCENT, font=(MONO, 13, "bold"), padx=16
                 ).pack(side="left", fill="y")
        tk.Label(bar, text="Avatar: Frontiers of Pandora  ·  mgraphobject swap utility",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 9)
                 ).pack(side="left", fill="y")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Row: Mod folder ────────────────────────────────────────────────────
        self._folder_var = tk.StringVar(value=self._prefs.get("mod_folder", DEFAULT_MOD_FOLDER))
        self._folder_var.trace_add("write", lambda *_: self._update_preview())
        self._make_path_row(
            label="Mod folder  (…/blue/graph objects/gear):",
            var=self._folder_var,
            browse_cmd=self._browse_mod_folder,
            pick_file=False,
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Row: Source file ───────────────────────────────────────────────────
        self._src_file_var = tk.StringVar(value="")
        self._src_file_var.trace_add("write", lambda *_: self._update_preview())
        self._make_path_row(
            label="Source .mgraphobject  (extracted from game files — can be anywhere):",
            var=self._src_file_var,
            browse_cmd=self._browse_src_file,
            pick_file=True,
        )
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Main columns ───────────────────────────────────────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Source list (left)
        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=12)
        tk.Label(left, text="① SOURCE  — model to apply",
                 bg=BG, fg=WARN, font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 6))
        self._src_list = SearchableList(left, self._items, on_select=self._on_src)
        self._src_list.pack(fill="both", expand=True)

        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y", pady=12)

        # Centre column
        mid = tk.Frame(main, bg=BG, width=340)
        mid.pack(side="left", fill="both", padx=6, pady=12)
        mid.pack_propagate(False)

        self._src_card = ItemCard(mid, "SOURCE", WARN, text_height=5)
        self._src_card.pack(fill="both", expand=True, pady=(0, 6))

        self._tgt_card = ItemCard(mid, "TARGET", SUCCESS, text_height=9)
        self._tgt_card.pack(fill="both", expand=True, pady=(0, 6))

        self._preview = PreviewPanel(mid)
        self._preview.pack(fill="both", expand=True, pady=(0, 8))

        tk.Button(mid, text="⚙   EXECUTE SWAP",
                  bg=BTN_BG, fg=ACCENT,
                  activebackground=BTN_HOV, activeforeground=ACCENT,
                  relief="flat", font=(MONO, 10, "bold"),
                  cursor="hand2", pady=10, command=self._execute
                  ).pack(fill="x")

        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y", pady=12)

        # Target list (right)
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(6, 12), pady=12)
        tk.Label(right, text="② TARGET  — slot to replace",
                 bg=BG, fg=SUCCESS, font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 6))
        self._tgt_list = SearchableList(right, self._items, on_select=self._on_tgt)
        self._tgt_list.pack(fill="both", expand=True)

        # ── Status bar ─────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        self._status_var = tk.StringVar(value="Ready.")
        self._status_lbl = tk.Label(self, textvariable=self._status_var,
                                     bg=PANEL, fg=MUTED,
                                     font=("Segoe UI", 8), anchor="w", padx=12, pady=5)
        self._status_lbl.pack(fill="x")

    def _make_path_row(self, label, var, browse_cmd, pick_file):
        row = tk.Frame(self, bg=PANEL, height=42)
        row.pack(fill="x")
        row.pack_propagate(False)
        tk.Label(row, text=label, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9), padx=12).pack(side="left", fill="y")
        tk.Entry(row, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                 insertbackground=ACCENT, relief="flat", font=(MONO, 8), bd=4
                 ).pack(side="left", fill="both", expand=True, pady=7)
        tk.Button(row, text="Browse…", bg=BTN_BG, fg=TEXT,
                  activebackground=BTN_HOV, activeforeground=ACCENT,
                  relief="flat", font=("Segoe UI", 9), padx=10, cursor="hand2",
                  command=browse_cmd
                  ).pack(side="left", padx=(6, 12), pady=7)

    # ── Callbacks ──────────────────────────────────────────────────────────────

    def _browse_mod_folder(self):
        folder = filedialog.askdirectory(
            title="Select your mod's 'graph objects/gear' folder",
            initialdir=self._folder_var.get() or self._prefs.get("mod_folder") or None)
        if folder:
            self._folder_var.set(folder)
            self._prefs["mod_folder"] = folder
            save_prefs(self._prefs)
            self._status(f"Mod folder: {folder}")

    def _browse_src_file(self):
        current = self._src_file_var.get()
        initial = (str(Path(current).parent) if current and os.path.exists(Path(current).parent)
                   else self._prefs.get("src_dir") or None)
        path = filedialog.askopenfilename(
            title="Select the source .mgraphobject file",
            filetypes=[("mgraphobject files", "*.mgraphobject"), ("All files", "*.*")],
            initialdir=initial)
        if path:
            self._src_file_var.set(path)
            self._prefs["src_dir"] = str(Path(path).parent)
            save_prefs(self._prefs)
            self._status(f"Source file: {Path(path).name}")

    def _on_src(self, item):
        self._src = item
        self._src_card.show(item)
        self._update_preview()
        self._status(f"Source item: [{item['slot']}] {item['ui_name']}")

    def _on_tgt(self, item):
        self._tgt = item
        self._tgt_card.show(item)
        self._update_preview()
        self._status(f"Target item: [{item['slot']}] {item['ui_name']}")

    def _update_preview(self):
        if self._src and self._tgt:
            src_file   = self._src_file_var.get().strip()
            mod_folder = self._folder_var.get().strip()
            w, e = validate_swap(self._src, self._tgt, src_file, mod_folder)
            self._preview.show(self._src, self._tgt, src_file, mod_folder, w, e)
        else:
            self._preview.reset()

    def _execute(self):
        src        = self._src
        tgt        = self._tgt
        src_file   = self._src_file_var.get().strip()
        mod_folder = self._folder_var.get().strip()

        if not src or not tgt:
            messagebox.showwarning("Nothing selected",
                                   "Select both a SOURCE and TARGET item first.")
            return

        warns, errs = validate_swap(src, tgt, src_file, mod_folder)

        if errs:
            messagebox.showerror("Cannot execute", "\n\n".join(errs))
            return

        if warns:
            if not messagebox.askyesno("Warnings — continue?",
                                        "Warnings:\n\n" + "\n\n".join(warns) +
                                        "\n\nProceed anyway?"):
                return

        # Build list of (dst_path, dst_name) — we copy the single source file to each target name
        targets = [
            (Path(mod_folder) / f"{mg}.mgraphobject", mg)
            for mg in tgt["mgraphobject"]
        ]

        # Overwrite check
        existing = [(p, n) for p, n in targets if p.exists()]
        if existing:
            names = "\n".join(f"  {n}.mgraphobject" for _, n in existing)
            if not messagebox.askyesno("Overwrite?",
                                        f"These files already exist:\n\n{names}\n\nOverwrite?"):
                return

        # Execute
        done, failed = [], []
        src_name = Path(src_file).name
        for dst_path, tgt_mg in targets:
            try:
                shutil.copy2(src_file, dst_path)
                done.append(f"✓  {src_name}  →  {tgt_mg}.mgraphobject")
            except OSError as exc:
                failed.append(f"✗  {tgt_mg}.mgraphobject: {exc}")

        if done and not failed:
            messagebox.showinfo("Swap complete", "\n".join(done))
            self._status("Swap complete.", color=SUCCESS)
        elif done:
            messagebox.showwarning("Partial success",
                                    "\n".join(done) + "\n\nFailed:\n" + "\n".join(failed))
            self._status("Partial success — check results.", color=WARN)
        else:
            messagebox.showerror("Swap failed", "\n\n".join(failed))
            self._status("Swap failed.", color=ERROR)

        self._update_preview()

    def _status(self, msg, color=MUTED):
        self._status_var.set(msg)
        self._status_lbl.config(fg=color)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().mainloop()