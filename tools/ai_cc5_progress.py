"""Compact, file-backed Ai-cc5 progress window."""

import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from argparse import Namespace
from tkinter import ttk

from ai_cc5 import flow_preview, next_command, use
from ai_cc5_state import PREPARATION, STEPS, Blocked, State, load, lock, digest
from ai_cc5_continue import approval_ready, approve_click
import ai_cc5_cloth3d as cloth3d

BG = "#F2F5F9"
WHITE = "#FFFFFF"
LINE = "#DCE3ED"
TEXT = "#172538"
MUTED = "#52647B"
BLUE, BLUE_BG = "#165BC7", "#EAF2FF"
GREEN, GREEN_BG = "#166C50", "#E8F5EE"
AMBER, AMBER_BG = "#895308", "#FFF1D8"
RED, RED_BG = "#A32E3E", "#FCECEF"
FONT = "Tahoma"
BUILD_STAGES = (
    ("face", "สร้างหน้า (Tidmunz)"),
    ("face_delivery", "ส่งภาพหน้าให้ตรวจ (ntfy)"),
    ("build", "สร้างตัว CC5 + Headshot"),
)
FINISHING_STEP = next(i for i, (key, *_) in enumerate(flow_preview.STEPS, 1) if key == "physics")


class Preview(tk.Tk):
    def __init__(self, store):
        super().__init__()
        self.store = store
        self.title("Ai-cc5 Preview")
        self.geometry("440x600+30+36")
        self.minsize(410, 550)
        self.layout_page = None
        self.configure(bg=BG)
        self.option_add("*Font", (FONT, 10))

        self.state_data = {}
        self.selection = None
        self.expanded = None
        self.log_text = None
        self.next = ""
        self.actors = {}
        self.preview = None
        self.page = "preview"
        self.prep_rows = []
        self.cloth_view = None
        self.cast_signature = None
        self.gallery_signature = None
        self.gallery_photos = []

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Choice.TCombobox", fieldbackground=WHITE, background=WHITE,
                        bordercolor=LINE, lightcolor=WHITE, darkcolor=WHITE,
                        foreground=TEXT, arrowcolor=MUTED, padding=4)
        style.map("Choice.TCombobox", fieldbackground=[("readonly", WHITE)],
                  foreground=[("readonly", TEXT)], selectbackground=[("readonly", WHITE)],
                  selectforeground=[("readonly", TEXT)])
        style.configure("Preview.Vertical.TScrollbar", background=LINE, troughcolor=WHITE,
                        bordercolor=WHITE, arrowcolor=MUTED)

        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=12, pady=10)

        header = tk.Frame(content, bg=BG)
        header.pack(fill="x", pady=(0, 7))
        label(header, "พรีวิวตัวละคร", size=14, bold=True).pack(side="left")
        self.pinned = tk.BooleanVar(value=False)
        pin = tk.Checkbutton(header, text="ปักหน้าต่าง", variable=self.pinned, bg=BG,
                             activebackground=BG, fg=MUTED, selectcolor=WHITE, padx=0,
                             command=lambda: self.attributes("-topmost", self.pinned.get()))
        pin.pack(side="right")

        select = tk.Frame(content, bg=BG)
        select.pack(fill="x", pady=(0, 7))
        select.columnconfigure(0, weight=1)
        self.story_title = ttk.Combobox(select, state="readonly", style="Choice.TCombobox")
        self.story_title.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        self.story_title.configure(state="disabled")
        self.actor = ttk.Combobox(select, state="readonly", style="Choice.TCombobox")
        self.actor.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.select_button = button(select, "เลือกงาน", self.choose, primary=True)
        # Monitoring only: selection is owned by the AI CLI.
        self.story_scope = label(select, "", color=MUTED, size=8, wraplength=365, justify="left")
        self.notice = label(content, "", color=RED, wraplength=380)

        summary = self.summary_panel = card(content)
        summary_top = tk.Frame(summary, bg=WHITE)
        summary_top.pack(fill="x", padx=9, pady=(5, 3))
        self.overall = label(summary_top, "", bg=WHITE, bold=True)
        self.overall.pack(side="left")
        self.phase = label(summary_top, "", bg=BLUE_BG, color=BLUE, size=8, bold=True, padx=6, pady=2)
        self.phase.pack(side="right")
        # One fixed progress area for whichever production step is active.
        progress_top = tk.Frame(summary, bg=WHITE)
        progress_top.pack(fill="x", padx=9, pady=(3, 2))
        self.progress_name = label(progress_top, "", bg=WHITE, size=9, bold=True)
        self.progress_name.pack(side="left", fill="x", expand=True)
        self.progress_percent = label(progress_top, "", bg=WHITE, size=12, bold=True, anchor="e")
        self.progress_percent.pack(side="right")
        self.progress_bar = bar(summary)
        self.progress_bar.configure(height=7)
        self.progress_bar.pack(fill="x", padx=9, pady=(0, 3))
        self.progress_detail = label(summary, "", bg=WHITE, color=MUTED, size=8,
                                     wraplength=350, justify="left")
        self.progress_detail.pack(fill="x", padx=9, pady=(0, 6))

        tabs = self.tabs = tk.Frame(content, bg=BG)
        tabs.pack(fill="x", pady=(0, 6))
        self.prep_tab = button(tabs, "เตรียมเรื่อง", lambda: self.change_page("prepare"))
        self.prep_tab.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.preview_tab = button(tabs, "พรีวิว", lambda: self.change_page("preview"))
        self.preview_tab.pack(side="left", fill="x", expand=True, padx=3)
        self.images_tab = button(tabs, "รูปภาพ", lambda: self.change_page("images"))
        self.images_tab.pack(side="left", fill="x", expand=True, padx=(3, 0))

        cast = self.cast_panel = card(content)
        cast_top = tk.Frame(cast, bg=WHITE)
        cast_top.pack(fill="x", padx=8, pady=(4, 1))
        self.cast_title = label(cast_top, "รายชื่อตัวละคร", bg=WHITE, bold=True)
        self.cast_title.pack(side="left", fill="x", expand=True)
        self.cast_open = button(cast_top, "เปิดไฟล์", self.open_cast_report)
        self.cast_open.pack(side="right")
        cast_body = tk.Frame(cast, bg=WHITE)
        cast_body.pack(fill="x", padx=5)
        self.cast_list = tk.Text(cast_body, height=4, wrap="word", relief="flat", borderwidth=0,
                                 highlightthickness=0, bg=WHITE, font=(FONT,9), state="disabled", cursor="arrow")
        cast_scroll = ttk.Scrollbar(cast_body, orient="vertical", command=self.cast_list.yview)
        cast_scroll.pack(side="right", fill="y")
        self.cast_list.configure(yscrollcommand=cast_scroll.set)
        self.cast_list.pack(fill="x", expand=True)
        self.cast_list.tag_configure("done", foreground="#000000")
        self.cast_list.tag_configure("pending", foreground="#B40000")
        label(cast, "* สำคัญ   ดำ = ทำแล้ว   แดง = ยังไม่เสร็จ", bg=WHITE, color=MUTED, size=8).pack(fill="x", padx=8, pady=(1,4))

        checklist = self.checklist = card(content)
        checklist.pack(fill="x", pady=(0, 7))
        self.rows = []
        for index, (_, title, owner, _) in enumerate(STEPS):
            row = tk.Frame(checklist, bg=WHITE, cursor="hand2", height=23)
            row.pack(fill="x")
            row.pack_propagate(False)
            dot = tk.Canvas(row, width=25, height=22, highlightthickness=0, bg=WHITE, cursor="hand2")
            dot.pack(side="left")
            text = label(row, title, bg=WHITE, size=10)
            text.pack(side="left", fill="x", expand=True)
            meta = label(row, "", bg=WHITE, size=8, anchor="e", padx=8)
            meta.pack(side="right")
            detail = tk.Frame(checklist, bg=BLUE_BG)
            description = label(detail, "", bg=BLUE_BG, color=TEXT, size=8,
                                justify="left", wraplength=345)
            description.pack(fill="x", padx=(25, 8), pady=(0, 4))
            # Expanded rows contain explanation only; no additional progress bars.
            for widget in (row, dot, text, meta):
                widget.bind("<Button-1>", lambda _, i=index: self.toggle(i))
            self.rows.append((row, dot, text, meta, detail, description, owner))

        # Actor build stages (face -> review -> CC5 body) shown between เลือกตัว and เปิดงาน.
        # Read-only: status comes from story["status"][<story>_<actor>] written by the face/build queues.
        self.build_rows = []
        for key, title in BUILD_STAGES:
            row = tk.Frame(checklist, bg=WHITE, height=23)
            row.pack_propagate(False)
            dot = tk.Canvas(row, width=25, height=22, highlightthickness=0, bg=WHITE)
            dot.pack(side="left")
            text = label(row, "   " + title, bg=WHITE, size=10)
            text.pack(side="left", fill="x", expand=True)
            meta = label(row, "", bg=WHITE, size=8, anchor="e", padx=8)
            meta.pack(side="right")
            row.pack(fill="x", before=self.rows[2][0])
            self.build_rows.append((key, row, dot, text, meta))

        self.cloth_row = tk.Frame(checklist, bg=AMBER_BG, height=23)
        self.cloth_row.pack_propagate(False)
        self.cloth_title = label(self.cloth_row, "   สร้างชุด AI 3D", bg=AMBER_BG, color=AMBER, size=10, bold=True)
        self.cloth_title.pack(side="left", fill="x", expand=True)
        self.cloth_meta = label(self.cloth_row, "", bg=AMBER_BG, color=AMBER, size=8, padx=8)
        self.cloth_meta.pack(side="right")

        render_index = next(i for i, (key, *_) in enumerate(STEPS) if key == "render")
        self.garment_before = self.rows[render_index][0]
        self.garment_row = tk.Frame(checklist, bg=WHITE, height=23, cursor="hand2", takefocus=True)
        self.garment_row.pack_propagate(False)
        self.garment_title = label(self.garment_row, "", bg=WHITE, size=10, padx=8)
        self.garment_title.pack(side="left", fill="x", expand=True)
        self.garment_status = label(self.garment_row, "", bg=WHITE, size=8, padx=8)
        self.garment_status.pack(side="right")
        self.garment_detail, self.garment_list = self.make_garment_detail(checklist)
        self.cloth_detail, self.cloth_list = self.make_garment_detail(checklist)
        self.garment_expanded = None
        for row, title, status, group in (
            (self.garment_row, self.garment_title, self.garment_status, "finishing"),
            (self.cloth_row, self.cloth_title, self.cloth_meta, "cloth"),
        ):
            row.configure(cursor="hand2", takefocus=True)
            for widget in (row, title, status):
                widget.bind("<Button-1>", lambda _, section=group: self.toggle_garment(section))
            row.bind("<Return>", lambda _, section=group: self.toggle_garment(section))

        self.prep_panel = card(content)
        prep_top = tk.Frame(self.prep_panel, bg=WHITE)
        prep_top.pack(fill="x", padx=8, pady=(5, 2))
        label(prep_top, "ไฟล์เตรียมเรื่อง", bg=WHITE, bold=True).pack(side="left")
        self.prep_folder_button = button(prep_top, "เปิดโฟลเดอร์", self.open_preparation_folder)
        self.prep_folder_button.pack(side="right")
        for index, (name, _) in enumerate(PREPARATION):
            row = tk.Frame(self.prep_panel, bg=WHITE)
            row.pack(fill="x", padx=8, pady=4)
            label(row, f"{index + 1}. {name}", bg=WHITE, size=9).pack(side="left")
            file_button = button(row, "เปิด", lambda i=index: self.open_preparation_file(i))
            file_button.pack(side="right")
            status = label(row, "", bg=WHITE, anchor="e", size=8, padx=7)
            status.pack(side="right")
            self.prep_rows.append((status, file_button))
        self.prep_hint = label(self.prep_panel, "", bg=WHITE, size=8, color=MUTED, wraplength=366,
                               justify="left")
        self.prep_hint.pack(fill="x", padx=8, pady=(5, 7))

        self.images_panel = card(content)
        gallery_header = tk.Frame(self.images_panel, bg=WHITE)
        gallery_header.pack(fill="x", padx=8, pady=(5,2))
        self.gallery_title = label(gallery_header, "ภาพที่ส่ง NTFY", bg=WHITE, bold=True)
        self.gallery_title.pack(side="left")
        self.gallery_canvas = tk.Canvas(self.images_panel, bg=WHITE, highlightthickness=0, height=200)
        self.gallery_scroll = ttk.Scrollbar(self.images_panel, orient="vertical", command=self.gallery_canvas.yview)
        self.gallery_scroll.pack(side="right", fill="y")
        self.gallery_canvas.pack(side="left", fill="both", expand=True)
        self.gallery_canvas.configure(yscrollcommand=self.gallery_scroll.set)
        self.gallery_inner = tk.Frame(self.gallery_canvas, bg=WHITE)
        self.gallery_window = self.gallery_canvas.create_window((0,0), window=self.gallery_inner, anchor="nw")
        self.gallery_inner.bind("<Configure>", lambda e: self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all")))
        self.gallery_canvas.bind("<Configure>", lambda e: self.gallery_canvas.itemconfigure(self.gallery_window,width=e.width))
        self.gallery_inner.columnconfigure(0,weight=1)
        self.gallery_inner.columnconfigure(1,weight=1)

        journal = self.journal = card(content)
        journal.pack(fill="both", expand=True)
        toolbar = tk.Frame(journal, bg=WHITE)
        toolbar.pack(fill="x", padx=7, pady=3)
        label(toolbar, "บันทึกงาน", bg=WHITE, bold=True).pack(side="left", padx=2)
        self.toolbar = toolbar
        self.approval_button = button(toolbar, "อนุมัติและทำต่อ", self.approve_current, primary=True)
        self.copy_button = button(toolbar, "คัดลอกคำสั่ง", self.copy_command)
        # No CLI command controls in the monitoring window.
        self.preview_button = button(toolbar, "เปิดภาพ", self.open_preview)
        self.preview_button.pack(side="right", padx=(0, 4))
        self.output = tk.Text(journal, height=4, wrap="word", relief="flat", borderwidth=0,
                              highlightthickness=0, bg=WHITE, fg=MUTED, padx=8, pady=3,
                              font=(FONT, 8), state="disabled", cursor="arrow")
        scroll = ttk.Scrollbar(journal, orient="vertical", style="Preview.Vertical.TScrollbar",
                               command=self.output.yview)
        scroll.pack(side="right", fill="y")
        self.log_scroll = scroll
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("error", foreground=RED)
        self.output.tag_configure("time", foreground=BLUE)

        self.refresh()

    def actor_choices(self, story, manifest, selected):
        inventory = load(self.store.runs / story / "CAST_QA_INVENTORY.json", {}).get("actors", {})
        self.actors = {}
        characters = manifest.get("characters")
        for key, actor in (characters.items() if isinstance(characters, dict) else ()):
            if not isinstance(actor, dict):
                continue
            if key not in inventory or not key.startswith(story + "_"):
                continue
            name = inventory[key].get("name") or actor.get("name") or key
            display = f"{name} · {actor.get('age', '—')} ปี"
            if display in self.actors:
                display += f" · {key.removeprefix(story + '_')}"
            self.actors[display] = key.removeprefix(story + "_")
        self.actor.configure(values=list(self.actors))
        self.actor.set(next((text for text, key in self.actors.items() if key == selected), "เลือกตัวละคร / ช่วงวัย"))

    def choose(self):
        story = self.state_data.get("story")
        actor = self.actors.get(self.actor.get())
        if not story or not actor:
            return
        args = Namespace(story=story, actor=actor, label=None, donor_map=None)
        try:
            with lock(self.store.runs / ".ai_cc5.lock"):
                if self.store.active().get("story") != story:
                    raise Blocked("AI รับงานเรื่องใหม่แล้ว")
                use(self.store, args)
        except (Blocked, OSError, ValueError, KeyError) as exc:
            self.show_notice(str(exc))
            return
        self.notice.pack_forget()
        self.update_view()

    def show_notice(self, text):
        self.notice.configure(text=text)
        if not self.notice.winfo_manager():
            self.notice.pack(fill="x", before=self.overall.master.master, pady=(0, 5))

    def toggle(self, index):
        current = len(self.state_data.get("done", ()))
        shown = self.expanded
        self.expanded = -1 if shown == index else index
        self.draw_rows()

    def garment_busy(self, state):
        """True while a clothing job (old StableGen or the 20-step garment flow) is unfinished:
        main steps from ใส่ชุด onward must wait for it."""
        if not state:
            return False
        if cloth3d.active(self.store, state):
            return True
        try:
            flow = flow_preview.read_flow(self.store, state)
        except ValueError:
            return False
        return bool(flow and flow[1].get("label") and flow_preview.next_number(flow[2]) is not None)

    def draw_build(self, state, manifest):
        story, actor = state.get("story"), state.get("actor")
        job = f"{story}_{actor}" if story and actor else None
        status = (manifest.get("status") or {}).get(job, {}) if job else {}
        char = (manifest.get("characters") or {}).get(job, {}) if job else {}
        for key, row, dot, text, meta in self.build_rows:
            value = status.get(key)
            if key in ("face", "face_delivery") and char.get("head_from") and not value:
                right, color = "ใช้หัวเดิม", GREEN
            elif value == "ok":
                right, color = "เสร็จ", GREEN
            elif value in ("fail", "error", "blocked"):
                right, color = "ค้าง", RED
            elif value == "review":
                right, color = "รอตรวจภาพ", AMBER
            elif value:
                right, color = str(value), AMBER
            elif not job:
                right, color = "รอเลือกตัว", MUTED
            else:
                right, color = "รอดำเนินการ", MUTED
            done = color == GREEN
            dot.delete("all")
            dot.create_oval(9, 7, 17, 15, fill=color if color != MUTED else WHITE,
                            outline=color if color != MUTED else "#A1AFC1", width=1)
            text.configure(fg=color if color in (RED, AMBER) else TEXT)
            meta.configure(text=right, fg=color)

    def draw_rows(self):
        state = self.state_data
        focused = len(state.get("done", ()))
        if self.garment_busy(state):
            focused = min(focused,3)
        phase = state.get("phase", "พร้อม")
        active, tint = phase_colors(phase) if state else (AMBER, AMBER_BG)
        for index, (row, dot, text, meta, panel, description, owner) in enumerate(self.rows):
            is_current = index == focused and not (self.garment_busy(state) and index>=3)
            done = index < focused
            opened = index == self.expanded
            color, bg = (active, tint) if is_current else (GREEN, WHITE) if done else (MUTED, WHITE)
            row.configure(bg=bg)
            dot.configure(bg=bg)
            dot.delete("all")
            dot.create_oval(9, 7, 17, 15, fill=color if done or is_current else bg,
                            outline=color if done or is_current else "#A1AFC1", width=1)
            mark = "▾" if opened else "›"
            text.configure(text=f"{STEPS[index][1]}  {mark}", fg=color if is_current else TEXT,
                           bg=bg, font=(FONT, 10, "bold" if is_current else "normal"))
            if is_current and state:
                right = phase if phase != "พร้อม" else ("รอผู้ใช้" if STEPS[index][0] == "approve" else "ถัดไป")
            elif done:
                right = "เสร็จ"
            elif self.garment_busy(state) and index>=3:
                right = "รอชุดใหม่"
            else:
                right = "รอดำเนินการ"
            meta.configure(text=right, bg=bg, fg=color)
            if opened:
                panel.configure(bg=bg)
                message = STEPS[index][3]
                if is_current and not state:
                    message = "รอ AI รับงาน"
                elif is_current and STEPS[index][0] == "approve" and approval_ready(self.store, state):
                    message = "ภาพพร้อมตรวจ · กดอนุมัติและทำต่อ หรืออนุมัติในแชต"
                    look = load(self.store.fitting(state) / "look.json", {})
                    poly = look.get("visual_review", {}).get("polygon_total")
                    if poly and poly > 80000:
                        message += f" · {poly:,} โพลิกอน เกินงบอ้างอิง"
                description.configure(text=message, bg=bg)
                if not panel.winfo_manager():
                    panel.pack(fill="x", after=row)
            elif panel.winfo_manager():
                panel.pack_forget()

    def approve_current(self):
        if cloth3d.active(self.store,self.state_data):
            self.show_notice("ยังไม่ผ่านการฟิตและตรวจชุด AI 3D")
            return
        self.approval_button.configure(state="disabled")
        try:
            token = approve_click(self.store, self.state_data)
            executable = Path(sys.executable)
            if executable.name.lower() == "pythonw.exe":
                executable = executable.with_name("python.exe")
            subprocess.Popen(
                [str(executable), "-B", str(self.store.root / "tools/ai_cc5_continue.py"), token],
                cwd=self.store.root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (Blocked, OSError, ValueError, KeyError, RuntimeError) as error:
            self.show_notice(str(error))
        self.update_view()

    def preparation_story(self):
        return self.state_data.get("story")

    def change_page(self, page):
        self.page = page
        self.update_view()

    def open_path(self, path):
        if path and path.exists():
            try:
                os.startfile(path)
            except OSError as exc:
                self.show_notice(str(exc))

    def open_preparation_folder(self):
        story = self.preparation_story()
        if story:
            self.open_path(self.store.preparation_folder(story))

    def open_preparation_file(self, index):
        story = self.preparation_story()
        if story:
            rows, _ = self.store.preparation(story)
            self.open_path(rows[index][1])

    def draw_preparation(self):
        story = self.preparation_story()
        folder = self.store.preparation_folder(story) if story else None
        rows, gate = self.store.preparation(story) if story else ((), {})
        self.prep_folder_button.configure(state="normal" if folder and folder.is_dir() else "disabled")
        ready = sum(status == "พร้อม" for _, _, status in rows)
        for index, (status, file_button) in enumerate(self.prep_rows):
            _, path, value = rows[index] if rows else ("", None, "รอข้อมูล")
            color = TEXT if value == "พร้อม" else RED
            status.configure(text=value, fg=color)
            file_button.configure(state="normal" if path and path.is_file() else "disabled")
        if gate.get("status") == "BLOCKED":
            hint = "ยังไม่พร้อมทำตัวละคร · เปิดผลตรวจเพื่อดูข้อมูลที่ขาด"
        elif ready == len(PREPARATION):
            hint = "เตรียมเอกสารครบแล้ว"
        elif folder and folder.is_dir():
            hint = "เปิดเอกสารแต่ละขั้นเพื่อตรวจและเตรียมข้อมูลต่อ"
        else:
            hint = "เรื่องนี้ยังไม่มีแฟ้มเตรียมเรื่อง"
        self.prep_hint.configure(text=hint)
        return ready

    def open_cast_report(self):
        story = self.preparation_story()
        if story:
            self.open_path(self.store.cast_report(story))

    def draw_cast(self, story, state, manifest):
        rows = self.store.cast_rows(story,state,manifest) if story else []
        signature = (story,tuple(rows))
        path = self.store.cast_report(story) if story else None
        self.cast_open.configure(state="normal" if path and path.is_file() else "disabled")
        if signature == self.cast_signature:
            return
        self.cast_signature = signature
        self.cast_title.configure(text=f"รายชื่อตัวละคร · {len(rows)} รายการ")
        self.cast_list.configure(height=max(4,min(12,len(rows)+1)))
        pos=self.cast_list.yview()[0]
        self.cast_list.configure(state="normal")
        self.cast_list.delete("1.0","end")
        for name,star,done in rows:
            self.cast_list.insert("end",("* " if star else "  ")+name+"\n","done" if done else "pending")
        if not rows:
            self.cast_list.insert("end","ยังไม่มีรายชื่อในบรีฟ")
        self.cast_list.configure(state="disabled")
        self.cast_list.yview_moveto(pos)

    def draw_gallery(self, story):
        from PIL import Image, ImageTk, ImageOps
        records = self.store.sent_images(story) if story else []
        signature=[]
        for record in records:
            path=record[3]
            try:
                st=path.stat()
                signature.append((record,st.st_size,st.st_mtime_ns))
            except OSError:
                signature.append((record,None,None))
        signature=tuple(signature)
        if signature == self.gallery_signature:
            return
        self.gallery_signature=signature
        for child in self.gallery_inner.winfo_children():
            child.destroy()
        self.gallery_photos=[]
        self.gallery_title.configure(text=f"ภาพที่ส่ง NTFY · {len(records)} ภาพ")
        if not records:
            label(self.gallery_inner,"ยังไม่มีภาพที่ยืนยันการส่ง",bg=WHITE,color=MUTED).grid(row=0,column=0,columnspan=2,padx=8,pady=12)
        for i,(date,name,kind,path,sha,receipt) in enumerate(records):
            tile=tk.Frame(self.gallery_inner,bg=WHITE,highlightbackground=LINE,highlightthickness=1)
            tile.grid(row=i//2,column=i%2,sticky="nsew",padx=3,pady=3)
            label(tile,name+" · "+kind,bg=WHITE,bold=True,size=8,wraplength=160,justify="left").pack(fill="x",padx=4,pady=(3,0))
            try:
                if not path.is_file() or digest(path)!=sha:
                    raise ValueError("ภาพต้นฉบับไม่ตรงใบยืนยัน")
                with Image.open(path) as im:
                    thumb=ImageOps.contain(im.convert("RGB"),(158,110))
                    photo=ImageTk.PhotoImage(thumb,master=self)
                self.gallery_photos.append(photo)
                pic=tk.Label(tile,image=photo,bg=WHITE,cursor="hand2")
                pic.pack(padx=3,pady=3)
                pic.bind("<Button-1>",lambda e,p=path:self.open_path(p))
            except (OSError,ValueError,SyntaxError):
                label(tile,"ไม่พบภาพเดิมที่ตรงใบยืนยัน",bg=WHITE,color=RED,size=8,wraplength=150).pack(padx=4,pady=14)
            label(tile,date.replace("T"," ")[:19],bg=WHITE,color=MUTED,size=7).pack(fill="x",padx=4,pady=(0,3))
        self.gallery_canvas.yview_moveto(0)

    def make_garment_detail(self, parent):
        detail = tk.Frame(parent, bg=BLUE_BG)
        listing = tk.Text(detail, height=5, wrap="word", bg=BLUE_BG, fg=TEXT,
                          font=(FONT, 9), relief="flat", state="disabled")
        scroll = ttk.Scrollbar(detail, command=listing.yview)
        listing.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        listing.pack(fill="x", padx=(8, 0))
        listing.content = None
        return detail, listing

    def toggle_garment(self, group):
        self.garment_expanded = None if self.garment_expanded == group else group
        self.draw_garment(self.state_data)

    def draw_garment(self, state):
        flow = flow_preview.read_flow(self.store, state)
        if not flow:
            self.garment_row.pack_forget()
            self.garment_detail.pack_forget()
            self.cloth_detail.pack_forget()
            self.cloth_title.configure(text="   สร้างชุด AI 3D")
            if not self.cloth_view:
                self.cloth_row.pack_forget()
            return
        run, config, records = flow
        current = flow_preview.next_number(records)
        total = len(flow_preview.STEPS)
        if not config.get("label"):
            status, color = "ยังไม่ได้ลงทะเบียน", MUTED
        elif current is None:
            status, color = "ยืนยันครบ", GREEN
        elif current < FINISHING_STEP:
            status, color = "รอขั้นสร้างชุด", MUTED
        else:
            record = records.get(flow_preview.STEPS[current - 1][0], {})
            status = f"ขั้น {current}/{total}"
            color = RED if record.get("status") == "fail" else AMBER
        self.garment_status.configure(text=status, fg=color)
        if not self.garment_row.winfo_manager():
            self.garment_row.pack(fill="x", before=self.garment_before)
        if not self.cloth_row.winfo_manager():
            self.cloth_row.pack(fill="x", before=self.rows[3][0])
        if not self.cloth_view:
            if current is None:
                cloth_text = "ครบแล้ว"
            elif current < FINISHING_STEP:
                cloth_text = f"ขั้น {current}/{total} · {flow_preview.STEPS[current - 1][0]}"
            else:
                cloth_text = f"เสร็จ 1–{FINISHING_STEP - 1}"
            self.cloth_meta.configure(text=cloth_text)
        rows = flow_preview.progress_rows(run, config, records)
        for group, row, title, text, detail, listing, start, stop in (
            ("cloth", self.cloth_row, self.cloth_title, "   สร้างชุด AI 3D",
             self.cloth_detail, self.cloth_list, 1, FINISHING_STEP),
            ("finishing", self.garment_row, self.garment_title, "เตรียมตัวละครก่อนตรวจ",
             self.garment_detail, self.garment_list, FINISHING_STEP, total + 1),
        ):
            expanded = self.garment_expanded == group
            title.configure(text=f"{text}  {'▾' if expanded else '›'}")
            if not expanded:
                detail.pack_forget()
                continue
            if not detail.winfo_manager():
                detail.pack(fill="x", after=row)
            lines = []
            for number in range(start, stop):
                name, step_status, note = rows[number - 1]
                lines.append(f"{number:02d}  [{step_status}]  {name}")
                if note:
                    lines.append(f"      {note}")
            if config.get("label") and current is not None and start <= current < stop:
                lines.extend(("", flow_preview.command_text(run, config, current)))
            content = "\n".join(lines)
            if content != listing.content:
                position = listing.yview()[0]
                listing.configure(state="normal")
                listing.delete("1.0", "end")
                listing.insert("1.0", content)
                listing.configure(state="disabled")
                listing.yview_moveto(position)
                listing.content = content

    def draw_tabs(self):
        pages={"prepare":self.prep_panel,"preview":self.checklist,"images":self.images_panel}
        for page, widget in (("prepare",self.prep_tab),("preview",self.preview_tab),("images",self.images_tab)):
            active=self.page==page
            widget.configure(bg=WHITE if active else BG,fg=TEXT if active else MUTED,
                             activebackground=WHITE,activeforeground=TEXT,
                             font=(FONT,9,"bold" if active else "normal"),
                             relief="solid" if active else "flat",borderwidth=1 if active else 0)
        for page,panel in pages.items():
            if page!=self.page:
                panel.pack_forget()
        if self.page == "preview":
            if not self.summary_panel.winfo_manager():
                self.summary_panel.pack(fill="x", pady=(0, 7), after=self.tabs)
        else:
            self.summary_panel.pack_forget()
        show=pages[self.page]
        if not show.winfo_manager():
            show.pack(fill="both" if self.page=="images" else "x",expand=self.page=="images",pady=(0,7),before=self.journal)
        if self.page == "prepare":
            if not self.cast_panel.winfo_manager():
                self.cast_panel.pack(fill="x", pady=(0, 6), after=self.prep_panel)
        else:
            self.cast_panel.pack_forget()
        if self.layout_page != self.page:
            # Use a taller default only for preparation, where the cast list lives.
            height = self.winfo_height()
            if self.layout_page is None:
                if self.page == "prepare":
                    self.geometry("440x710")
            elif self.page == "prepare" and height <= 600:
                self.geometry(f"{self.winfo_width()}x710")
            elif self.layout_page == "prepare" and height == 710:
                self.geometry(f"{self.winfo_width()}x600")
            self.layout_page = self.page
        self.journal.pack_configure(expand=self.page!="images",side="bottom" if self.page=="images" else "top")
        if self.page=="images":
            if self.output.winfo_manager():
                self.output.pack_forget()
            if self.log_scroll.winfo_manager():
                self.log_scroll.pack_forget()
        else:
            if not self.log_scroll.winfo_manager():
                self.log_scroll.pack(side="right",fill="y")
            if not self.output.winfo_manager():
                self.output.pack(fill="both",expand=True)

    def copy_command(self):
        if self.next:
            self.clipboard_clear()
            self.clipboard_append(self.next.replace("Ai-cc5 ", r".\Ai-cc5.cmd ", 1))

    def open_preview(self):
        if self.preview and self.preview.is_file():
            try:
                os.startfile(self.preview)
            except OSError as exc:
                self.show_notice(str(exc))

    def update_view(self):
        state = self.state_data = self.store.active()
        story = state.get("story")
        manifest = self.store.story_manifest(story) if story else {}
        draft = manifest.get("production_stage") == "planning" and not state.get("new_actor")
        selection = (story, state.get("actor"), state.get("label"))
        if selection != self.selection:
            self.expanded = None
            if story != (self.selection or (None,))[0] or self.selection is None:
                self.page = "prepare" if draft else "preview"
            self.selection = selection
            self.garment_expanded = None
            self.expanded = None
            self.actors = {}
            if story and not draft:
                self.actor_choices(story, manifest, state.get("actor"))
            else:
                self.actor.configure(values=())
        title = manifest.get("title") or story or "ยังไม่มีเรื่องที่ AI รับงาน"
        if self.story_title.get() != title:
            self.story_title.configure(values=(title,))
            self.story_title.set(title)

        completed, scheduled = self.store.actor_totals(state, manifest)
        target, required, pending = self.store.cast_target(manifest, scheduled)
        self.overall.configure(text=f"เสร็จ {completed} / {target}" if story else "ยังไม่เริ่มงาน")
        # Overall cast count stays textual; only current step has a meter.

        if draft:
            characters = manifest.get("characters", {})
            names = [f'{row["name"]} · {row["age"]} ปี' for row in characters.values()
                     if isinstance(row, dict) and row.get("name") and row.get("age") is not None]
            self.actor.set(names[0] if len(names) == 1 else "รายชื่อนักแสดงอยู่ในบรีฟ")
        elif not story:
            self.actor.set("รอเลือกตัวละคร / ช่วงวัย")
        if state.get("new_actor"):
            actor = manifest.get("characters", {}).get(f"{story}_{state.get('actor')}", {})
            self.actor.set(f'{actor.get("name") or state["actor"]} · {state.get("age") or ""}')
        self.actor.configure(state="disabled")
        self.select_button.configure(state="disabled")
        if pending:
            self.story_scope.configure(text=f"{', '.join(pending)} ยังไม่ระบุจำนวน")
            self.story_scope.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        else:
            self.story_scope.grid_remove()

        if story:
            try:
                self.store.sync_cast_report(story,state)
            except OSError:
                pass
        self.draw_cast(story,state,manifest)
        prepared_steps = self.draw_preparation()
        self.draw_tabs()
        if self.page == "images":
            self.draw_gallery(story)
        if self.page == "preview":
            self.cloth_view = cloth3d.display(self.store,state)
            self.draw_build(state, manifest)
            self.draw_rows()
            if self.cloth_view:
                stage, _, _ = self.cloth_view
                c, t = (RED, RED_BG) if stage == "blocked" else (GREEN, GREEN_BG) if stage in ("mesh_ready", "complete") else (AMBER, AMBER_BG)
                self.cloth_row.configure(bg=t)
                self.cloth_title.configure(bg=t, fg=c)
                self.cloth_meta.configure(text=cloth3d.PHASES[stage], bg=t, fg=c)
                if not self.cloth_row.winfo_manager():
                    self.cloth_row.pack(fill="x", before=self.rows[3][0])
            elif not state.get("actor"):
                self.cloth_row.pack_forget()
            self.draw_garment(state)
        else:
            self.cloth_view = None
        step = self.store.step(state) if state else None
        phase = state.get("phase", "พร้อม") if state else "รอรับงาน"
        if draft:
            phase = "เตรียมครบ" if prepared_steps == len(PREPARATION) else "เตรียมเรื่อง"
        elif state and not step:
            phase = "เสร็จครบ" if required and completed >= required else "รอตัวถัดไป"
        elif step and step[2].endswith("อนุญาต") and phase == "พร้อม":
            phase = "รออนุญาต"
        color, tint = phase_colors(phase)
        if self.garment_busy(state) and not self.cloth_view:
            phase, color, tint = "กำลังทำชุด 3D", AMBER, AMBER_BG
        if self.cloth_view and self.garment_busy(state):
            stage=self.cloth_view[0]
            phase="รอฟิตชุด" if stage=="mesh_ready" else "ชุด 3D มีปัญหา" if stage=="blocked" else "กำลังทำชุด 3D"
            color,tint=(RED,RED_BG) if stage=="blocked" else (AMBER,AMBER_BG)
        self.phase.configure(text=phase, fg=color, bg=tint)
        self.draw_shared_progress(state, draft, prepared_steps)

        self.next = next_command(self.store, state)
        self.copy_button.configure(state="normal" if state and "<" not in self.next else "disabled")
        if not draft and not self.garment_busy(state) and approval_ready(self.store, state):
            if not self.approval_button.winfo_manager():
                self.approval_button.pack(side="right", padx=(0, 4), before=self.preview_button)
            self.approval_button.configure(state="normal")
        else:
            self.approval_button.pack_forget()
        self.copy_button.pack_forget()
        self.preview = self.store.folder(state) / "review.png" if state else None
        self.preview_button.configure(state="normal" if self.preview and self.preview.is_file() else "disabled")
        new_log = self.store.log_view(state) or "รายการงานจะแสดงที่นี่เมื่อเริ่มขั้นแรก"
        if new_log != self.log_text:
            self.log_text = new_log
            follow = self.output.yview()[-1] >= .99
            position = self.output.yview()[0]
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            in_failure = False
            for line in self.log_text.splitlines():
                in_failure = in_failure or line.startswith("FAIL ล่าสุด")
                if in_failure or " FAIL " in line:
                    self.output.insert("end", line + "\n", "error")
                else:
                    timestamp, sep, event = line.partition(" +")
                    self.output.insert("end", timestamp[11:19] + sep if sep else timestamp, "time" if sep else ())
                    self.output.insert("end", event + "\n")
            self.output.configure(state="disabled")
            if follow:
                self.output.see("end")
            else:
                self.output.yview_moveto(position)

    def draw_shared_progress(self, state, draft, prepared_steps):
        if self.cloth_view and self.cloth_view[0]!="complete":
            stage,level,detail=self.cloth_view
            name="AI 3D · "+cloth3d.PHASES[stage]
            color=RED if stage=="blocked" else GREEN if stage in ("mesh_ready","complete") else AMBER
        else:
            name, level, detail, color = shared_progress(self.store, state, draft, prepared_steps)
            try:
                flow = flow_preview.read_flow(self.store, state) if state and not draft else None
            except ValueError:
                flow = None
            if flow and flow[1].get("label"):
                current = flow_preview.next_number(flow[2])
                if current is not None:
                    total = len(flow_preview.STEPS)
                    record = flow_preview.record_of(flow[2], flow_preview.STEPS[current - 1][0])
                    name = f"งานชุด · ขั้น {current}/{total}"
                    level = (current - 1) / total
                    detail = flow_preview.STEPS[current - 1][1]
                    color = RED if record.get("status") == "fail" else AMBER
        self.progress_name.configure(text=name)
        self.progress_percent.configure(text=f"{round(level * 100)}%" if level is not None else "—%", fg=color)
        self.progress_detail.configure(text=detail)
        self.progress_bar.level = level or 0
        paint(self.progress_bar, color)

    def refresh(self):
        try:
            self.update_view()
        except (Blocked, OSError, ValueError, KeyError) as exc:
            self.show_notice(str(exc))
        self.after(1200, self.refresh)


def shared_progress(store, state, draft=False, prepared_steps=0):
    """Single meter: measured evidence of the active step, never fake progress."""
    if not state:
        return "รอรับงาน", None, "ยังไม่มีงานที่กำลังทำ", MUTED
    if draft:
        total = len(PREPARATION)
        return "เตรียมเรื่อง", prepared_steps / total, f"เอกสารพร้อม {prepared_steps}/{total}", GREEN if prepared_steps == total else BLUE
    step = store.step(state)
    if not step:
        return "ตัวละครเสร็จแล้ว", 1.0, f"ผ่านครบ {len(STEPS)}/{len(STEPS)} ขั้น", GREEN
    phase = state.get("phase", "พร้อม")
    name = f"ขั้น {len(state.get('done', ()) ) + 1} · {step[1]}"
    color, _ = phase_colors(phase)
    measured, total = store.evidence_progress(state)
    live = store.live_detail(state)
    if total > 1:
        detail = f"หลักฐาน {measured}/{total}"
        if live:
            detail += f" · {live}"
        return name, min(1, measured / total), detail, color
    # No trustworthy fractional measurement exists in these steps.
    return name, None, live or ("กดอนุมัติด้านล่าง หรืออนุมัติในแชต" if step[0] == "approve" else phase), color


def label(parent, text, *, color=TEXT, bg=BG, size=9, bold=False, anchor="w", **options):
    return tk.Label(parent, text=text, fg=color, bg=bg, anchor=anchor,
                    font=(FONT, size, "bold" if bold else "normal"), **options)


def button(parent, text, command, primary=False):
    bg, fg = (BLUE, WHITE) if primary else (BG, TEXT)
    return tk.Button(parent, text=text, command=command, cursor="hand2", relief="flat",
                     borderwidth=0, highlightthickness=0, bg=bg, fg=fg, padx=8, pady=3,
                     activebackground="#124BA5" if primary else BLUE_BG,
                     activeforeground=fg, disabledforeground="#7A889B",
                     font=(FONT, 8, "bold" if primary else "normal"))


def card(parent):
    return tk.Frame(parent, bg=WHITE, highlightbackground=LINE, highlightthickness=1)


def bar(parent):
    canvas = tk.Canvas(parent, height=4, bg=LINE, highlightthickness=0)
    canvas.level, canvas.color = 0, BLUE
    canvas.bind("<Configure>", lambda _event: paint(canvas, canvas.color))
    return canvas


def paint(canvas, color):
    canvas.color = color
    canvas.delete("fill")
    if canvas.level:
        canvas.create_rectangle(0, 0, canvas.winfo_width() * canvas.level, canvas.winfo_height(),
                                fill=color, width=0, tags="fill")


def phase_colors(phase):
    if phase in ("FAIL", "ต้องตรวจ CC5"):
        return RED, RED_BG
    if phase == "กำลังทำ":
        return AMBER, AMBER_BG
    if phase in ("เสร็จครบ", "เตรียมครบ"):
        return GREEN, GREEN_BG
    if phase.startswith("รอ") or phase in ("ยังไม่เลือกงาน", "เตรียมเรื่อง"):
        return AMBER, AMBER_BG
    return BLUE, BLUE_BG


def show(store=None):
    Preview(store or State()).mainloop()
