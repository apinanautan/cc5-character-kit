# CC5 Character Studio: paste a story's character list -> each character goes step by step to a finished .iAvatar.
#   python app.py   (or double-click "CC5 Character Studio" on the Desktop)
import glob, json, os, queue, subprocess, sys, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), "studio")]
import kit
import planner, runner, wardrobe

FONT = ("Leelawadee UI", 10)
MARK = {"ok": "✓", "skip": "–", "run": "…", "fail": "✗"}
EDIT_COLS = ("use", "name", "sex", "age", "folder", "notes")


def mark(v):
    v = v or ""
    return MARK.get(v.split(":")[0], "")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CC5 Character Studio — ทำตัวละครตามเรื่อง")
        self.geometry("1280x760")
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        self.option_add("*Font", FONT)
        style = ttk.Style(self)
        style.configure("Treeview", rowheight=26, font=FONT)
        style.configure("Treeview.Heading", font=(FONT[0], 10, "bold"))
        self.q = queue.Queue()
        self.rows = []          # editable rows before the story is created
        self.story_path = None  # set once created / opened
        self.worker = None
        self.run_obj = None
        self.img = None
        self._build()
        self.after(200, self._poll)

    # ---------- layout ----------
    def _build(self):
        top = ttk.Frame(self, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text="ชื่อเรื่อง").pack(side="left")
        self.title_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.title_var, width=28).pack(side="left", padx=4)
        ttk.Label(top, text="เก็บไฟล์ที่").pack(side="left", padx=(12, 0))
        self.out_var = tk.StringVar(value=kit.CFG["out_root"])
        ttk.Entry(top, textvariable=self.out_var, width=40).pack(side="left", padx=4)
        ttk.Button(top, text="...", width=3, command=self._pick_out).pack(side="left")
        ttk.Label(top, text="   เปิดเรื่องเดิม").pack(side="left")
        self.open_var = tk.StringVar()
        self.open_box = ttk.Combobox(top, textvariable=self.open_var, width=34, state="readonly")
        self.open_box.pack(side="left", padx=4)
        self.open_box.bind("<<ComboboxSelected>>", lambda e: self._open_story())
        self._refresh_stories()

        opts = ttk.Frame(self, padding=(6, 0))
        opts.pack(fill="x")
        self.opt_fabric = tk.BooleanVar(value=True)
        self.opt_weights = tk.BooleanVar(value=False)
        self.opt_export = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="สร้างลายผ้าใหม่ด้วย AI ทุกตัว", variable=self.opt_fabric).pack(side="left")
        ttk.Checkbutton(opts, text="เกลี่ยน้ำหนักแขนเสื้อ (ทดลอง)", variable=self.opt_weights).pack(side="left", padx=12)
        ttk.Checkbutton(opts, text="Export iAvatar อัตโนมัติ (ห้ามจับเมาส์ตอนนั้น)", variable=self.opt_export).pack(side="left")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=6)

        left = ttk.Frame(body)
        ttk.Label(left, text="1) วางรายชื่อตัวละคร (บรรทัดละข้อ)").pack(anchor="w")
        self.list_txt = tk.Text(left, width=30, height=20, font=FONT, wrap="word")
        self.list_txt.pack(fill="both", expand=True)
        ttk.Button(left, text="อ่านรายชื่อ ➜", command=self._parse).pack(fill="x", pady=4)
        ttk.Label(left, text="ดับเบิลคลิกช่องในตารางเพื่อแก้ (เพศ: m/f, อายุ: ตัวเลข)\n"
                             "หมายเหตุใส่ได้: แผลไฟไหม้ที่แขน/หน้า/ขา, ผอม, ท้อง",
                  foreground="#555").pack(anchor="w")
        body.add(left, weight=1)

        mid = ttk.Frame(body)
        cols = list(EDIT_COLS) + [k for k, _ in runner.STEPS]
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", selectmode="browse")
        heads = {"use": "ทำ", "name": "ชื่อ", "sex": "เพศ", "age": "อายุ", "folder": "โฟลเดอร์", "notes": "หมายเหตุ"}
        heads.update(dict(runner.STEPS))
        widths = {"use": 34, "name": 190, "sex": 36, "age": 40, "folder": 140, "notes": 120}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths.get(c, 58), stretch=c in ("name", "folder"), anchor="w" if c in ("name", "folder", "notes") else "center")
        self.tree.tag_configure("run", background="#fff3b0")
        self.tree.tag_configure("fail", background="#ffd6d6")
        self.tree.tag_configure("done", background="#d8f5d0")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._edit_cell)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._show_selected())
        btns = ttk.Frame(mid)
        btns.pack(fill="x", pady=4, before=self.tree, side="bottom")
        self.create_btn = ttk.Button(btns, text="2) ยืนยัน + สุ่มชุด/ผม", command=self._create)
        self.create_btn.pack(side="left")
        self.start_btn = ttk.Button(btns, text="3) ▶ เริ่ม / ทำต่อ", command=self._start)
        self.start_btn.pack(side="left", padx=6)
        ttk.Button(btns, text="■ หยุด (หลังสเต็ปนี้)", command=self._stop).pack(side="left")
        btns2 = ttk.Frame(mid)
        btns2.pack(fill="x", before=btns, side="bottom")
        ttk.Label(btns2, text="ตัวที่เลือก:").pack(side="left")
        ttk.Button(btns2, text="สุ่มชุดตัวนี้ใหม่", command=self._reroll).pack(side="left", padx=4)
        ttk.Button(btns2, text="ทำตัวนี้ใหม่ทั้งหมด", command=lambda: self._redo("fabric")).pack(side="left", padx=4)
        ttk.Button(btns2, text="ทำใหม่ตั้งแต่สร้างตัว", command=lambda: self._redo("build")).pack(side="left", padx=4)
        ttk.Button(btns2, text="เปิดโฟลเดอร์งาน", command=self._open_folder).pack(side="left", padx=4)
        body.add(mid, weight=4)

        right = ttk.Frame(body)
        self.pic = ttk.Label(right, text="(รูปตัวละครจะขึ้นที่นี่)", anchor="center")
        self.pic.pack(fill="both", expand=True)
        self.info = tk.Text(right, height=7, width=36, font=FONT, wrap="word")
        self.info.pack(fill="x")
        ttk.Label(right, text="บันทึกการทำงาน").pack(anchor="w")
        self.log_txt = tk.Text(right, height=10, width=36, font=(FONT[0], 9), wrap="word")
        self.log_txt.pack(fill="both", expand=True)
        body.add(right, weight=2)

    # ---------- list / table ----------
    def _pick_out(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get())
        if d:
            self.out_var.set(os.path.normpath(d))

    def _refresh_stories(self):
        files = sorted(glob.glob(os.path.join(kit.REPO, "stories", "*.json")), key=os.path.getmtime, reverse=True)
        self.story_files = {}
        for f in files:
            try:
                t = json.load(open(f, encoding="utf-8-sig")).get("title", "")
            except ValueError:
                continue
            self.story_files["%s  (%s)" % (t, os.path.basename(f)[:-5])] = f
        self.open_box["values"] = list(self.story_files)

    def _parse(self):
        self.rows = planner.parse(self.list_txt.get("1.0", "end"))
        self.story_path = None
        self._fill_rows()
        unknown = [r["name"] for r in self.rows if r["use"] and r["sex"] == "?"]
        if unknown:
            messagebox.showinfo("เช็กเพศ", "ยังไม่รู้เพศของ:\n" + "\n".join(unknown) + "\n\nดับเบิลคลิกช่อง 'เพศ' แล้วใส่ m หรือ f")

    def _fill_rows(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(i), values=("✓" if r["use"] else "", r["name"], r["sex"], r["age"],
                                                            r["folder"], r["notes"]))

    def _edit_cell(self, ev):
        if self.story_path:
            return  # after the story is created the list is fixed (use the per-character buttons)
        row, col = self.tree.identify_row(ev.y), self.tree.identify_column(ev.x)
        if not row:
            return
        key = self.tree["columns"][int(col[1:]) - 1]
        if key not in EDIT_COLS:
            return
        r = self.rows[int(row)]
        if key == "use":
            r["use"] = not r["use"]
            self._fill_rows()
            return
        x, y, w, h = self.tree.bbox(row, col)
        e = ttk.Entry(self.tree)
        e.insert(0, str(r[key]))
        e.place(x=x, y=y, width=max(w, 80), height=h)
        e.focus()

        def done(_=None):
            v = e.get().strip()
            if key == "age":
                v = int(v) if v.isdigit() else r["age"]
            if key == "sex":
                v = {"ช": "m", "ชาย": "m", "ญ": "f", "หญิง": "f"}.get(v, v.lower()[:1] or "?")
            r[key] = v
            e.destroy()
            self._fill_rows()

        e.bind("<Return>", done)
        e.bind("<FocusOut>", done)

    # ---------- story ----------
    def _create(self):
        if self.story_path:
            messagebox.showinfo("", "เรื่องนี้สร้างแล้ว กด เริ่ม/ทำต่อ ได้เลย")
            return
        title = self.title_var.get().strip()
        if not title or not self.rows:
            messagebox.showwarning("", "ใส่ชื่อเรื่อง แล้วกด 'อ่านรายชื่อ' ก่อน")
            return
        bad = [r["name"] for r in self.rows if r["use"] and r["sex"] not in ("m", "f")]
        if bad:
            messagebox.showwarning("เพศ", "ใส่เพศ m/f ให้ครบก่อน:\n" + "\n".join(bad))
            return
        self.story_path = runner.create_story(title, self.rows, self.out_var.get())
        self._refresh_stories()
        self._load_table()
        self.log("สร้างเรื่องแล้ว: " + os.path.basename(self.story_path) + " — สุ่มชุด/ผม/ลายผ้าให้ทุกตัวแล้ว")

    def _open_story(self):
        f = self.story_files.get(self.open_var.get())
        if not f:
            return
        self.story_path = f
        s = runner.load(f)
        self.title_var.set(s.get("title", ""))
        if s.get("out_dir"):
            self.out_var.set(os.path.dirname(s["out_dir"]))
        self._load_table()

    def _load_table(self):
        s = runner.load(self.story_path)
        self.tree.delete(*self.tree.get_children())
        for job, c in s["characters"].items():
            st = s.get("status", {}).get(job, {})
            vals = ["✓", c["name"], "m" if c.get("sex") == "male" else "f", c.get("age", ""), c.get("folder", ""),
                    c.get("notes", "")] + [mark(st.get(k)) for k, _ in runner.STEPS]
            tag = "fail" if any(str(v).startswith("fail") for v in st.values()) else \
                "run" if "run" in st.values() else "done" if mark(st.get("export")) in ("✓", "–") else ""
            self.tree.insert("", "end", iid=job, values=vals, tags=(tag,))

    def _sel_job(self):
        sel = self.tree.selection()
        return sel[0] if sel and self.story_path else None

    def _show_selected(self):
        job = self._sel_job()
        if not job:
            return
        s = runner.load(self.story_path)
        c = s["characters"].get(job)
        if not c:
            return
        d = os.path.join(kit.JOBS, job)
        for p in (os.path.join(d, c["name"] + ".png"), os.path.join(d, "face.png")):
            if os.path.exists(p):
                self._show_image(p)
                break
        pool = json.load(open(wardrobe.POOL, encoding="utf-8"))
        names = {i["spec"]: i["name"] for k in ("tops", "bottoms", "full", "shoes") for i in pool[k]}
        lines = ["%s  (%s, %s ปี)" % (c["name"], "ชาย" if c["sex"] == "male" else "หญิง", c.get("age"))]
        for spec, fab in c["outfit"]:
            lines.append("• %s%s" % (names.get(spec, spec), "  ลาย: " + fab[4:] if fab and fab.startswith("gen:") else ""))
        lines += ["• ลาย: " + d_ for d_ in c.get("fabric_designs", []) if not any((f or "").startswith("gen:") for _, f in c["outfit"])]
        if c.get("hair"):
            lines.append("• ผม: " + os.path.splitext(os.path.basename(c["hair"]))[0])
        st = s.get("status", {}).get(job, {})
        lines += ["%s: %s" % (dict(runner.STEPS)[k], v) for k, v in st.items() if str(v).startswith("fail")]
        self.info.delete("1.0", "end")
        self.info.insert("end", "\n".join(lines))

    def _show_image(self, path):
        try:
            from PIL import Image, ImageTk
            im = Image.open(path)
            im.thumbnail((420, 470))
            self.img = ImageTk.PhotoImage(im)
            self.pic.configure(image=self.img, text="")
        except Exception as e:
            self.pic.configure(text=str(e)[:80])

    # ---------- run ----------
    def _start(self):
        if not self.story_path:
            messagebox.showwarning("", "กด 'ยืนยัน + สุ่มชุด/ผม' หรือเลือกเรื่องเดิมก่อน")
            return
        if self.worker and self.worker.is_alive():
            return
        opts = {"ai_fabric": self.opt_fabric.get(), "weights": self.opt_weights.get(), "export": self.opt_export.get()}
        self.run_obj = runner.Runner(self.story_path, opts, lambda kind, data: self.q.put((kind, data)))
        self.worker = threading.Thread(target=self.run_obj.run, daemon=True)
        self.worker.start()
        self.start_btn.state(["disabled"])
        self.log("เริ่มทำงาน — ระหว่าง Export ห้ามจับเมาส์/คีย์บอร์ด")

    def _stop(self):
        if self.run_obj:
            self.run_obj.stop = True
            self.log("จะหยุดหลังสเต็ปที่กำลังทำ ...")

    def _busy(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("", "กำลังทำงานอยู่ กดหยุดก่อน")
            return True
        return False

    def _reroll(self):
        job = self._sel_job()
        if job and not self._busy():
            runner.reroll(self.story_path, job)
            self._load_table()
            self.tree.selection_set(job)
            self.log("สุ่มชุดใหม่ให้ " + job)

    def _redo(self, step):
        job = self._sel_job()
        if job and not self._busy():
            runner.reset(self.story_path, job, step)
            self._load_table()
            self.log("ล้างสถานะ %s ตั้งแต่ %s" % (job, dict(runner.STEPS)[step]))

    def _open_folder(self):
        job = self._sel_job()
        path = os.path.join(kit.JOBS, job) if job else (runner.load(self.story_path)["out_dir"] if self.story_path else kit.JOBS)
        os.makedirs(path, exist_ok=True)
        subprocess.Popen(["explorer", path])

    def log(self, msg):
        self.log_txt.insert("end", msg + "\n")
        self.log_txt.see("end")

    def _poll(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "log":
                    self.log(data)
                elif kind == "status":
                    sel = self.tree.selection()
                    self._load_table()
                    if sel and self.tree.exists(sel[0]):
                        self.tree.selection_set(sel[0])
                    else:
                        self.tree.selection_set(data[0])
                elif kind == "image" and os.path.exists(data):
                    self._show_image(data)
                elif kind == "done":
                    self.start_btn.state(["!disabled"])
                    self._load_table()
        except queue.Empty:
            pass
        self.after(300, self._poll)


if __name__ == "__main__":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sharp Thai text on a scaled screen
    except Exception:
        pass
    App().mainloop()
