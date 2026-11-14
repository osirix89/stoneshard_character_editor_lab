from __future__ import annotations
import copy, json, logging, os, re, shutil, sys, traceback, zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from .core import (decode_compressed_json, decode_compressed_json_bytes, encode_compressed_json, skill_records,
                  set_skill, compact_json, SaveFormatError, find_paths)

APP_TITLE = "Stoneshard Character Lab — Experimental Save Editor"
IDENTITY_FIELDS = [
    ("Nombre del personaje / nameKey", "nameKey"), ("Clase / classKey", "classKey"),
    ("playerClass", "playerClass"), ("Retrato / avatar", "avatar"),
    ("Cabeza / Head", "Head"), ("Cuerpo / BodySprite", "BodySprite"),
    ("Cadáver / CorpseSprite", "CorpseSprite"), ("Raza / raceKey", "raceKey"),
    ("Sexo / sexKey", "sexKey"),
]
CATALOG_FIELDS = ["perksList", "playerClass", "Head", "CorpseSprite", "classKey", "avatar", "BodySprite", "raceKey", "sexKey", "nameKey"]
STAT_FIELDS = [
    ("Fuerza", "STR"), ("Agilidad", "AGL"), ("Percepción", "PRC"),
    ("Vitalidad", "Vitality"), ("Voluntad", "WIL"),
    ("Nivel", "LVL"), ("Experiencia", "XP"),
    ("Puntos de atributos (AP)", "AP"), ("Puntos de habilidades (SP)", "SP"),
]

class CharacterLab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("1370x900"); self.minsize(1120,740)
        self.current_root=None; self.original_root=None; self.current_path=None
        self.char_folder=None; self.save_folder=None; self.folder_path=None
        self.character_map=None; self.save_map=None; self.reference_root=None
        self.reference_label=""; self.dirty=False; self.skill_filter=tk.StringVar()
        self.identity_vars={}; self.identity_widgets={}; self.stat_vars={}; self._skill_rows=[]
        self.catalog={}; self.catalog_sources={}; self.catalog_scanned_files=0; self.catalog_filter=tk.StringVar()
        self.log_path=Path.home()/".stoneshard_character_lab"/"stoneshard_character_lab.log"
        self.log_path.parent.mkdir(parents=True,exist_ok=True)
        logging.basicConfig(filename=self.log_path, level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
        self._style(); self._build()
        self.load_builtin_catalog()
        self.update_catalog_combos(); self.render_catalog()
        self.log("Programa iniciado. Ningún archivo del juego se modifica automáticamente.")
        self.log(f"Log detallado: {self.log_path}")

    def _style(self):
        self.configure(bg="#171b22")
        st=ttk.Style(self); st.theme_use("clam")
        st.configure("TFrame", background="#202630")
        st.configure("TLabel", background="#202630", foreground="#e6e9ef", font=("Segoe UI",10))
        st.configure("Title.TLabel", font=("Segoe UI",17,"bold"), foreground="#f2c879")
        st.configure("Sub.TLabel", foreground="#aeb8c7")
        st.configure("TButton", padding=7)
        st.configure("Accent.TButton", background="#a87937", foreground="#ffffff", padding=8)
        st.map("Accent.TButton", background=[("active","#c28d42")])
        st.configure("Save.TButton", background="#267a4b", foreground="#ffffff",
                     font=("Segoe UI", 13, "bold"), padding=(12, 10))
        st.map("Save.TButton", background=[("active", "#31965e")])
        st.configure("TNotebook", background="#171b22", borderwidth=0)
        st.configure("TNotebook.Tab", padding=(13,8), background="#303946", foreground="#e6e9ef")
        st.map("TNotebook.Tab", background=[("selected","#a87937")])
        st.configure("Treeview", background="#151a21", fieldbackground="#151a21", foreground="#e6e9ef", rowheight=25)
        st.configure("Treeview.Heading", background="#303946", foreground="#f2c879")

    def _build(self):
        top=ttk.Frame(self,padding=(14,10)); top.pack(fill="x")
        ttk.Label(top,text="STONESHARD CHARACTER LAB",style="Title.TLabel").pack(side="left")
        ttk.Label(top,text="Experimental · local save analysis · create backups",style="Sub.TLabel").pack(side="left",padx=18)
        actions=ttk.Frame(top); actions.pack(side="right")
        ttk.Button(actions,text="Abrir carpeta character_N",command=self.load_folder).pack(side="left",padx=3)
        ttk.Button(actions,text="Abrir data.sav",command=self.load_single).pack(side="left",padx=3)
        ttk.Button(actions,text="Cargar referencia",command=self.load_reference).pack(side="left",padx=3)

        # Always-visible primary save action: deliberately placed above the tabs,
        # not in the bottom action strip where it can be hidden by small screens.
        savebar=ttk.Frame(self,padding=(14,4)); savebar.pack(fill="x")
        ttk.Button(savebar,text="💾  GUARDAR data.sav (Ctrl+S)",style="Save.TButton",
                   command=self.save_data_sav).pack(fill="x",ipady=5)
        self.bind_all("<Control-s>",lambda _event:self.save_data_sav())

        self.status=tk.StringVar(value="Sin guardado cargado")
        statusbar=ttk.Frame(self,padding=(14,5)); statusbar.pack(fill="x")
        ttk.Label(statusbar,textvariable=self.status,style="Sub.TLabel").pack(side="left")
        self.checksum_label=ttk.Label(statusbar,text="CHECKSUM: —",foreground="#f2c879"); self.checksum_label.pack(side="right")

        self.nb=ttk.Notebook(self); self.nb.pack(fill="both",expand=True,padx=10,pady=(0,8))
        self.tab_session=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_session,text="Sesión / pruebas")
        self.tab_identity=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_identity,text="Identidad y apariencia")
        self.tab_stats=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_stats,text="Atributos y progresión")
        self.tab_perks=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_perks,text="Perks")
        self.tab_skills=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_skills,text="Habilidades")
        self.tab_compare=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_compare,text="Comparar")
        self.tab_raw=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_raw,text="JSON avanzado")
        self.tab_catalog=ttk.Frame(self.nb,padding=12); self.nb.add(self.tab_catalog,text="Catálogo de saves")
        self._build_session(); self._build_identity(); self._build_stats(); self._build_perks()
        self._build_skills(); self._build_compare(); self._build_raw(); self._build_catalog()
        bottom=ttk.Frame(self,padding=(10,4)); bottom.pack(fill="x")
        ttk.Button(bottom,text="Aplicar controles al JSON",style="Accent.TButton",command=self.apply_forms).pack(side="left",padx=3)
        ttk.Button(bottom,text="GUARDAR PERSONAJE PARA EL JUEGO",style="Accent.TButton",command=self.clone_character).pack(side="left",padx=3)
        ttk.Button(bottom,text="Validar guardado",command=self.validate).pack(side="left",padx=3)
        ttk.Button(bottom,text="Restaurar original en memoria",command=self.reset).pack(side="left",padx=3)
        ttk.Button(bottom,text="Exportar data.sav + backup ZIP",command=self.export_zip).pack(side="right",padx=3)

    def _build_session(self):
        self.tab_session.columnconfigure(0,weight=1); self.tab_session.columnconfigure(1,weight=1)
        box=ttk.LabelFrame(self.tab_session,text="Guardado cargado",padding=12); box.grid(row=0,column=0,sticky="nsew",padx=5,pady=5)
        self.session_info=tk.Text(box,height=13,wrap="word",bg="#151a21",fg="#e6e9ef",insertbackground="white",relief="flat")
        self.session_info.pack(fill="both",expand=True)
        slots=ttk.LabelFrame(self.tab_session,text="Slots encontrados en la carpeta",padding=10); slots.grid(row=0,column=1,sticky="nsew",padx=5,pady=5)
        self.slot_list=tk.Listbox(slots,height=13,bg="#151a21",fg="#e6e9ef",selectbackground="#a87937",relief="flat")
        self.slot_list.pack(fill="both",expand=True); self.slot_list.bind("<<ListboxSelect>>",self.select_slot)
        btns=ttk.Frame(self.tab_session); btns.grid(row=1,column=0,columnspan=2,sticky="ew",pady=6)
        ttk.Button(btns,text="GUARDAR PERSONAJE EDITADO EN characters_v1",style="Accent.TButton",command=self.clone_character).pack(side="left",padx=4)
        ttk.Button(btns,text="Abrir log de debug",command=self.open_log).pack(side="left",padx=4)
        ttk.Button(btns,text="Guardar informe de diagnóstico",command=self.save_report).pack(side="left",padx=4)
        ttk.Label(self.tab_session,text="GUARDADO PARA PROBAR EN EL JUEGO: al pulsar el botón se crea una carpeta character_N nueva con character.map, save.map y data.sav ya editados. Elegí la carpeta characters_v1 (la que contiene character_1, character_4, etc.). Después abrí el juego y comprobá el personaje. El original no se sobrescribe. Stoneshard debe estar cerrado.",style="Sub.TLabel",wraplength=1100).grid(row=2,column=0,columnspan=2,sticky="w",padx=8,pady=8)

    def _build_identity(self):
        ttk.Label(self.tab_identity,text="Editá el nombre y los identificadores. Los catálogos iniciales incluyen los valores detectados en Dirwin y Jonna; podés ampliarlos escaneando más partidas. nameKey se escribirá también en character.map y save.map. El juego podría tratarlo como clave interna: verificá el resultado en un clon.",style="Sub.TLabel",wraplength=1100).pack(anchor="w",pady=(0,10))
        grid=ttk.Frame(self.tab_identity); grid.pack(fill="x",anchor="nw")
        for i,(label,key) in enumerate(IDENTITY_FIELDS):
            r=i//2; c=(i%2)*2
            ttk.Label(grid,text=label).grid(row=r,column=c,sticky="w",padx=5,pady=7)
            var=tk.StringVar(); self.identity_vars[key]=var
            if key == "nameKey":
                widget=ttk.Entry(grid,textvariable=var,width=48)
            else:
                widget=ttk.Combobox(grid,textvariable=var,width=46,values=())
            widget.grid(row=r,column=c+1,sticky="ew",padx=5,pady=7)
            self.identity_widgets[key]=widget
        grid.columnconfigure(1,weight=1); grid.columnconfigure(3,weight=1)
        ttk.Label(self.tab_identity,text="Perfiles rápidos (copian los campos desde el guardado de referencia)",style="Sub.TLabel").pack(anchor="w",pady=(20,6))
        row=ttk.Frame(self.tab_identity); row.pack(anchor="w")
        ttk.Button(row,text="Copiar identidad de referencia",command=lambda:self.copy_reference("identity")).pack(side="left",padx=3)
        ttk.Button(row,text="Copiar apariencia de referencia",command=lambda:self.copy_reference("appearance")).pack(side="left",padx=3)

    def _build_stats(self):
        ttk.Label(self.tab_stats,text="Valores numéricos tomados de characterDataMap. No se fuerzan límites: esto es un laboratorio de pruebas.",style="Sub.TLabel").pack(anchor="w",pady=(0,12))
        grid=ttk.Frame(self.tab_stats); grid.pack(anchor="nw",fill="x")
        for i,(label,key) in enumerate(STAT_FIELDS):
            r=i//3;c=(i%3)*2
            ttk.Label(grid,text=label).grid(row=r,column=c,sticky="w",padx=8,pady=10)
            var=tk.StringVar();self.stat_vars[key]=var
            ttk.Entry(grid,textvariable=var,width=18).grid(row=r,column=c+1,sticky="w",padx=8,pady=10)
        ttk.Button(self.tab_stats,text="Copiar atributos y progresión de referencia",command=lambda:self.copy_reference("stats")).pack(anchor="w",pady=15)

    def _build_perks(self):
        ttk.Label(self.tab_perks,text="Un identificador por línea. Se guarda en characterDataMap.perksList. No inventes IDs: probá primero los que aparezcan en otros guardados o en el JSON.",style="Sub.TLabel",wraplength=1100).pack(anchor="w",pady=(0,8))
        self.perks_text=tk.Text(self.tab_perks,height=18,bg="#151a21",fg="#e6e9ef",insertbackground="white",relief="flat",font=("Consolas",10))
        self.perks_text.pack(fill="both",expand=True)
        row=ttk.Frame(self.tab_perks);row.pack(fill="x",pady=7)
        ttk.Button(row,text="Copiar perks de referencia (reemplazar)",command=lambda:self.copy_reference("perks")).pack(side="left",padx=3)
        ttk.Button(row,text="Acumular perks de referencia",command=self.merge_reference_perks).pack(side="left",padx=3)
        ttk.Button(row,text="Agregar perk manual",command=lambda:self.perks_text.insert("end","\no_perk_...")).pack(side="left",padx=3)
        ttk.Button(row,text="Agregar perks detectadas",command=self.merge_catalog_perks).pack(side="left",padx=3)
        ttk.Button(row,text="Quitar duplicados",command=self.dedupe_perks_text).pack(side="left",padx=3)

    def _build_skills(self):
        top=ttk.Frame(self.tab_skills);top.pack(fill="x",pady=(0,8))
        ttk.Label(top,text="Doble clic en una habilidad para alternar learned (campo 2 de cada bloque de cinco).",style="Sub.TLabel").pack(side="left")
        ttk.Entry(top,textvariable=self.skill_filter,width=35).pack(side="right")
        ttk.Label(top,text="Filtrar:").pack(side="right",padx=5)
        self.skill_filter.trace_add("write",lambda *_:self.render_skills())
        cols=("id","learned","block","offset")
        self.skill_tree=ttk.Treeview(self.tab_skills,columns=cols,show="headings",height=23)
        for col,title,width in [("id","ID interno",470),("learned","Aprendida",100),("block","Bloque completo",400),("offset","Índice",70)]:
            self.skill_tree.heading(col,text=title);self.skill_tree.column(col,width=width,anchor="w")
        self.skill_tree.pack(fill="both",expand=True);self.skill_tree.bind("<Double-1>",self.toggle_skill)
        row=ttk.Frame(self.tab_skills);row.pack(fill="x",pady=6)
        ttk.Button(row,text="Copiar habilidades de referencia",command=lambda:self.copy_reference("skills")).pack(side="left",padx=3)
        ttk.Button(row,text="Marcar todas aprendidas (prueba)",command=lambda:self.set_all_skills(True)).pack(side="left",padx=3)
        ttk.Button(row,text="Desmarcar todas (prueba)",command=lambda:self.set_all_skills(False)).pack(side="left",padx=3)

    def _build_compare(self):
        ttk.Label(self.tab_compare,text="Cargá otro data.sav como referencia. Podés comparar y copiar grupos completos sin tocar el archivo de referencia.",style="Sub.TLabel",wraplength=1100).pack(anchor="w",pady=(0,8))
        row=ttk.Frame(self.tab_compare);row.pack(fill="x")
        ttk.Button(row,text="Cargar / reemplazar referencia",command=self.load_reference).pack(side="left",padx=3)
        ttk.Button(row,text="Comparar campos",command=self.compare).pack(side="left",padx=3)
        self.ref_label=tk.StringVar(value="Sin referencia")
        ttk.Label(row,textvariable=self.ref_label,style="Sub.TLabel").pack(side="left",padx=10)
        self.diff_text=tk.Text(self.tab_compare,bg="#151a21",fg="#e6e9ef",insertbackground="white",relief="flat",font=("Consolas",9))
        self.diff_text.pack(fill="both",expand=True,pady=8)

    def _build_catalog(self):
        top=ttk.Frame(self.tab_catalog); top.pack(fill="x",pady=(0,8))
        ttk.Label(top,text="Escanea carpetas character_N o ZIPs de guardados. Solo lee data.sav; nunca modifica los archivos escaneados.",style="Sub.TLabel",wraplength=950).pack(side="left",fill="x",expand=True)
        actions=ttk.Frame(self.tab_catalog); actions.pack(fill="x",pady=4)
        ttk.Button(actions,text="Escanear carpeta",style="Accent.TButton",command=self.scan_save_folder).pack(side="left",padx=3)
        ttk.Button(actions,text="Escanear ZIP",command=self.scan_save_zip).pack(side="left",padx=3)
        ttk.Button(actions,text="Importar catálogo JSON",command=self.import_catalog).pack(side="left",padx=3)
        ttk.Button(actions,text="Exportar catálogo JSON",command=self.export_catalog).pack(side="left",padx=3)
        ttk.Label(actions,text="Filtrar:").pack(side="left",padx=(14,4))
        ent=ttk.Entry(actions,textvariable=self.catalog_filter,width=28); ent.pack(side="left")
        self.catalog_filter.trace_add("write",lambda *_:self.render_catalog())
        self.catalog_status=tk.StringVar(value="Todavía no se escanearon partidas.")
        ttk.Label(self.tab_catalog,textvariable=self.catalog_status,style="Sub.TLabel").pack(anchor="w",pady=(4,8))
        cols=("field","value","count","sources")
        self.catalog_tree=ttk.Treeview(self.tab_catalog,columns=cols,show="headings",height=22)
        for col,title,width in [("field","Campo",150),("value","Identificador / valor",330),("count","Partidas",90),("sources","Origen(es)",560)]:
            self.catalog_tree.heading(col,text=title); self.catalog_tree.column(col,width=width,anchor="w")
        self.catalog_tree.pack(fill="both",expand=True)
        self.catalog_tree.bind("<Double-1>",self.apply_catalog_selection)
        ttk.Label(self.tab_catalog,text="Doble clic: aplica el valor al campo de identidad correspondiente o acumula la perk en la lista. Los valores detectados no garantizan compatibilidad entre sí.",style="Sub.TLabel",wraplength=1100).pack(anchor="w",pady=7)

    def load_builtin_catalog(self):
        """Load the verified starter catalog bundled with the application."""
        seed = Path(__file__).resolve().parent.parent / "data" / "catalog_seed.json"
        if not seed.exists():
            self.log(f"No se encontró catálogo inicial: {seed}", "warning")
            return
        try:
            payload = json.loads(seed.read_text(encoding="utf-8"))
            values = payload.get("values", {})
            sources = payload.get("sources", {})
            for field, items in values.items():
                if field not in CATALOG_FIELDS or not isinstance(items, list):
                    continue
                for value in items:
                    srcs = sources.get(f"{field}\t{value}", ["Catálogo inicial"])
                    if not isinstance(srcs, list) or not srcs:
                        srcs = ["Catálogo inicial"]
                    for source in srcs:
                        self._catalog_add(field, value, str(source))
            self.catalog_scanned_files = max(self.catalog_scanned_files, int(payload.get("scanned_files", 0)))
            total = sum(len(v) for v in self.catalog.values())
            if hasattr(self, "catalog_status"):
                self.catalog_status.set(f"Catálogo inicial cargado: {total} valores únicos de Dirwin y Jonna ({self.catalog_scanned_files} saves analizados).")
            self.log(f"Catálogo inicial cargado desde {seed}; valores únicos={total}")
        except Exception as exc:
            self.log(f"No se pudo cargar catálogo inicial: {exc}\n{traceback.format_exc()}", "exception")

    def _catalog_add(self, field, value, source):
        if value is None or isinstance(value,(dict,list)): return
        value=str(value).strip()
        if not value: return
        self.catalog.setdefault(field,set()).add(value)
        self.catalog_sources.setdefault((field,value),set()).add(source)

    def _scan_save_blob(self, blob, pseudo_path, char_name, slot_name):
        decoded=decode_compressed_json_bytes(blob,Path(pseudo_path),"sav",char_name,slot_name)
        if not decoded.checksum_valid:
            self.log(f"CATÁLOGO: checksum no coincide: {pseudo_path}","warning")
            return False
        c=decoded.data.get("characterDataMap",{})
        if not isinstance(c,dict): return False
        source=f"{char_name}/{slot_name} · {c.get('nameKey','?')}"
        for field in CATALOG_FIELDS:
            value=c.get(field)
            if field=="perksList" and isinstance(value,list):
                for perk in value: self._catalog_add(field,perk,source)
            else:
                self._catalog_add(field,value,source)
        self.catalog_scanned_files+=1
        return True

    def scan_save_folder(self):
        folder=filedialog.askdirectory(title="Elegir carpeta que contiene character_N")
        if not folder:return
        root=Path(folder); found=0; errors=0
        self.log(f"Inicio de escaneo local: {root}")
        for p in root.rglob("data.sav"):
            try:
                slot=p.parent.name; char_name=p.parent.parent.name
                if not re.fullmatch(r"character_\d+",char_name,re.I): continue
                if not re.fullmatch(r"(?:auto|exit)?save_\d+",slot,re.I): continue
                if self._scan_save_blob(p.read_bytes(),p,char_name,slot): found+=1
            except Exception as e:
                errors+=1; self.log(f"Error escaneando {p}: {e}","exception")
        self.catalog_status.set(f"Escaneo terminado: {found} guardado(s) válido(s), {errors} error(es). Valores únicos: {sum(len(v) for v in self.catalog.values())}.")
        self.update_catalog_combos(); self.render_catalog()
        self.log(f"Escaneo terminado. saves válidos={found}; errores={errors}; valores={sum(len(v) for v in self.catalog.values())}")
        messagebox.showinfo("Escaneo terminado",self.catalog_status.get())

    def scan_save_zip(self):
        archive=filedialog.askopenfilename(title="Seleccionar ZIP con carpetas character_N",filetypes=[("ZIP","*.zip"),("Todos","*.*")])
        if not archive:return
        found=0; errors=0
        self.log(f"Inicio de escaneo ZIP: {archive}")
        try:
            with zipfile.ZipFile(archive,"r") as z:
                for info in z.infolist():
                    if info.is_dir() or not info.filename.lower().endswith("/data.sav"): continue
                    # ZIP paths are POSIX by convention, but tolerate archives
                    # produced on Windows that contain backslash separators.
                    parts=Path(info.filename.replace("\\", "/")).parts
                    if len(parts)<3: continue
                    char_name,slot=parts[-3],parts[-2]
                    if not re.fullmatch(r"character_\d+",char_name,re.I): continue
                    if not re.fullmatch(r"(?:auto|exit)?save_\d+",slot,re.I): continue
                    try:
                        if self._scan_save_blob(z.read(info),info.filename,char_name,slot): found+=1
                    except Exception as e:
                        errors+=1; self.log(f"Error en {info.filename}: {e}","exception")
        except Exception as e:
            self.log(f"No se pudo abrir ZIP: {e}\n{traceback.format_exc()}","exception"); messagebox.showerror("ZIP inválido",str(e)); return
        self.catalog_status.set(f"ZIP escaneado: {found} guardado(s) válido(s), {errors} error(es). Valores únicos: {sum(len(v) for v in self.catalog.values())}.")
        self.update_catalog_combos(); self.render_catalog()
        self.log(f"Escaneo ZIP terminado. saves válidos={found}; errores={errors}")
        messagebox.showinfo("Escaneo terminado",self.catalog_status.get())

    def update_catalog_combos(self):
        for field,widget in self.identity_widgets.items():
            vals=sorted(self.catalog.get(field,set()),key=str.casefold)
            current=self.identity_vars[field].get().strip()
            if current and current not in vals: vals.insert(0,current)
            if isinstance(widget,ttk.Combobox): widget.configure(values=vals)

    def render_catalog(self):
        if not hasattr(self,"catalog_tree"): return
        self.catalog_tree.delete(*self.catalog_tree.get_children())
        q=self.catalog_filter.get().strip().lower()
        for field in CATALOG_FIELDS:
            for value in sorted(self.catalog.get(field,set()),key=str.casefold):
                sources=sorted(self.catalog_sources.get((field,value),set()))
                src_text="; ".join(sources)
                if q and q not in field.lower() and q not in value.lower() and q not in src_text.lower(): continue
                self.catalog_tree.insert("","end",values=(field,value,len(sources),src_text))

    def apply_catalog_selection(self,event=None):
        if not self.require_loaded(): return
        item=self.catalog_tree.focus()
        if not item:return
        field,value,*_=self.catalog_tree.item(item,"values")
        if field=="perksList":
            lines=[x.strip() for x in self.perks_text.get("1.0","end").splitlines() if x.strip()]
            if value not in lines: lines.append(value)
            self.perks_text.delete("1.0","end"); self.perks_text.insert("1.0","\n".join(lines))
            self.log(f"Perk acumulada desde catálogo: {value}")
            self.nb.select(self.tab_perks)
        elif field in self.identity_vars:
            self.identity_vars[field].set(value); self.nb.select(self.tab_identity)
            self.log(f"Valor de catálogo aplicado al control {field}: {value}")

    def merge_catalog_perks(self):
        if not self.require_loaded():return
        lines=[x.strip() for x in self.perks_text.get("1.0","end").splitlines() if x.strip()]
        additions=sorted(self.catalog.get("perksList",set())-set(lines),key=str.casefold)
        lines.extend(additions)
        self.perks_text.delete("1.0","end"); self.perks_text.insert("1.0","\n".join(lines))
        self.log(f"Acumulación desde catálogo: {len(additions)} perk(s) agregada(s); no se quitaron las existentes.")

    def merge_reference_perks(self):
        if not self.require_loaded():return
        if self.reference_root is None:
            messagebox.showinfo("Sin referencia","Primero cargá un data.sav de referencia."); return
        src=self.reference_root.get("characterDataMap",{}).get("perksList",[])
        lines=[x.strip() for x in self.perks_text.get("1.0","end").splitlines() if x.strip()]
        additions=[str(x) for x in src if str(x) not in lines]
        lines.extend(additions)
        self.perks_text.delete("1.0","end"); self.perks_text.insert("1.0","\n".join(lines))
        self.log(f"Perks acumuladas desde referencia: {len(additions)} nuevas; las existentes se conservaron.")

    def dedupe_perks_text(self):
        lines=[x.strip() for x in self.perks_text.get("1.0","end").splitlines() if x.strip()]
        unique=list(dict.fromkeys(lines))
        self.perks_text.delete("1.0","end"); self.perks_text.insert("1.0","\n".join(unique))
        self.log(f"Perks: eliminados {len(lines)-len(unique)} duplicado(s) en el editor de texto.")

    def import_catalog(self):
        source=filedialog.askopenfilename(title="Importar catálogo Character Lab",filetypes=[("JSON","*.json"),("Todos","*.*")])
        if not source:return
        try:
            payload=json.loads(Path(source).read_text(encoding="utf-8"))
            values=payload.get("values",{})
            if not isinstance(values,dict): raise ValueError("El JSON no contiene un objeto values válido.")
            added=0
            for field,items in values.items():
                if field not in CATALOG_FIELDS or not isinstance(items,list): continue
                for value in items:
                    before=len(self.catalog.setdefault(field,set()))
                    self._catalog_add(field,value,f"CATÁLOGO IMPORTADO: {Path(source).name}")
                    added += len(self.catalog[field])-before
            self.catalog_status.set(f"Catálogo importado: {added} valor(es) nuevo(s). Total: {sum(len(v) for v in self.catalog.values())}.")
            self.update_catalog_combos(); self.render_catalog()
            self.log(f"Catálogo importado: {source}; valores nuevos={added}")
        except Exception as e:
            self.log(f"Error importando catálogo: {e}\n{traceback.format_exc()}","exception")
            messagebox.showerror("Catálogo inválido",str(e))

    def export_catalog(self):
        out=filedialog.asksaveasfilename(title="Exportar catálogo detectado",defaultextension=".json",initialfile="stoneshard_resource_catalog.json",filetypes=[("JSON","*.json")])
        if not out:return
        payload={"format":"Stoneshard Character Lab catalog","version":1,"scanned_files":self.catalog_scanned_files,"values":{k:sorted(v) for k,v in self.catalog.items()},"sources":{f"{k}\t{v}":sorted(src) for (k,v),src in self.catalog_sources.items()}}
        Path(out).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        self.log(f"Catálogo exportado: {out}")

    def _build_raw(self):
        bar=ttk.Frame(self.tab_raw);bar.pack(fill="x",pady=(0,6))
        ttk.Label(bar,text="JSON completo del data.sav (edición libre)",style="Sub.TLabel").pack(side="left")
        ttk.Button(bar,text="Recargar desde memoria",command=self.refresh_raw).pack(side="right",padx=3)
        ttk.Button(bar,text="Aplicar JSON editado",style="Accent.TButton",command=self.apply_raw).pack(side="right",padx=3)
        self.raw_text=tk.Text(self.tab_raw,wrap="none",bg="#10151b",fg="#dbe5ef",insertbackground="white",font=("Consolas",9),undo=True)
        y=ttk.Scrollbar(self.tab_raw,orient="vertical",command=self.raw_text.yview);x=ttk.Scrollbar(self.tab_raw,orient="horizontal",command=self.raw_text.xview)
        self.raw_text.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        self.raw_text.pack(side="top",fill="both",expand=True);y.pack(side="right",fill="y");x.pack(side="bottom",fill="x")

    def log(self,msg,level="info"):
        getattr(logging,level,logging.info)(msg)
        if hasattr(self,"session_info"):
            self.session_info.insert("end",f"\n[{datetime.now():%H:%M:%S}] {msg}")
            self.session_info.see("end")

    def require_loaded(self):
        if self.current_root is None:
            messagebox.showwarning("Sin guardado","Primero cargá un data.sav o una carpeta character_N.");return False
        return True

    def load_folder(self):
        folder=filedialog.askdirectory(title="Seleccionar carpeta character_N")
        if not folder:return
        root=Path(folder); char_name=root.name
        if not re.fullmatch(r"character_\d+",char_name,re.I):
            if not messagebox.askyesno("Nombre de carpeta",f"La carpeta se llama '{char_name}', no character_N. ¿Usarla igualmente para verificar firmas?"):return
        self.folder_path=root;self.char_folder=char_name
        try:
            cmap=root/"character.map"
            self.character_map=decode_compressed_json(cmap,"character_map",char_name)
            self.log(f"character.map: checksum {'OK' if self.character_map.checksum_valid else 'NO COINCIDE'}")
            slots=[]
            for p in sorted(root.iterdir()):
                if p.is_dir() and re.fullmatch(r"(?:auto|exit)?save_\d+",p.name,re.I) and (p/"data.sav").exists():slots.append(p)
            self.slot_list.delete(0,"end");self._slot_paths=slots
            for p in slots:
                try:
                    sv=decode_compressed_json(p/"data.sav","sav",char_name,p.name)
                    sm=decode_compressed_json(p/"save.map","save_map",char_name,p.name) if (p/"save.map").exists() else None
                    name=(sv.data.get("characterDataMap") or {}).get("nameKey","?")
                    self.slot_list.insert("end",f"{p.name}  |  {name}  |  MD5 {'OK' if sv.checksum_valid else 'ERROR'}  |  {sv.compressed_size:,} B")
                    self.log(f"Escaneado {p.name}/data.sav: checksum {'OK' if sv.checksum_valid else 'ERROR'}; JSON {sv.raw_size:,} bytes")
                    if sm and not sm.checksum_valid:self.log(f"ADVERTENCIA: {p.name}/save.map tiene checksum incorrecto","warning")
                except Exception as e:
                    self.slot_list.insert("end",f"{p.name}  |  ERROR: {e}");self.log(f"Error leyendo {p}: {e}","exception")
            if not slots:raise SaveFormatError("No se encontraron autosave_N/data.sav ni exitsave_N/data.sav.")
            self.status.set(f"Carpeta: {root} · {len(slots)} slot(s)")
            self.slot_list.selection_set(0);self.select_slot()
        except Exception as e:
            self.log(f"No se pudo abrir carpeta: {e}","exception");messagebox.showerror("Error al abrir carpeta",str(e))

    def select_slot(self,event=None):
        if not getattr(self,"_slot_paths",None):return
        sel=self.slot_list.curselection()
        if not sel:return
        p=self._slot_paths[sel[0]];self.load_save_path(p/"data.sav",self.char_folder,p.name)
        smp=p/"save.map"
        try:self.save_map=decode_compressed_json(smp,"save_map",self.char_folder,p.name) if smp.exists() else None
        except Exception as e:self.save_map=None;self.log(f"No se pudo leer save.map: {e}","exception")

    def load_single(self):
        f=filedialog.askopenfilename(title="Seleccionar Stoneshard data.sav",filetypes=[("Stoneshard save","data.sav *.sav"),("Todos","*.*")])
        if not f:return
        p=Path(f); sf=p.parent.name; cf=p.parent.parent.name
        if not re.fullmatch(r"character_\d+",cf,re.I):
            cf=simpledialog.askstring("Carpeta del personaje","No pude inferir character_N desde la ruta. Escribí el nombre exacto de la carpeta (ej. character_4):",initialvalue="character_4")
            if not cf:return
        self.folder_path=p.parent.parent;self.char_folder=cf
        self.character_map=None;self.save_map=None
        try:
            cmap=self.folder_path/"character.map"
            if cmap.exists(): self.character_map=decode_compressed_json(cmap,"character_map",cf)
            smap=p.parent/"save.map"
            if smap.exists(): self.save_map=decode_compressed_json(smap,"save_map",cf,sf)
        except Exception as e:
            self.log(f"Aviso leyendo metadatos adyacentes: {e}","warning")
        self.load_save_path(p,cf,sf)

    def load_save_path(self,path,char_folder,save_folder):
        try:
            decoded=decode_compressed_json(Path(path),"sav",char_folder,save_folder)
            self.current_path=Path(path);self.save_folder=save_folder
            self.current_root=decoded.data;self.original_root=copy.deepcopy(decoded.data);self.dirty=False
            self._refresh_forms();self.refresh_raw();self.render_skills()
            c=decoded.data.get("characterDataMap",{})
            self.status.set(f"Cargado: {char_folder}/{save_folder}/data.sav · {decoded.compressed_size:,} B")
            self.checksum_label.configure(text=f"CHECKSUM: {'VÁLIDO' if decoded.checksum_valid else 'NO COINCIDE'}",foreground="#71d69a" if decoded.checksum_valid else "#ff7777")
            self.log(f"Cargado {path}; checksum {'válido' if decoded.checksum_valid else 'NO válido'}; personaje={c.get('nameKey')} clase={c.get('classKey')}; {len(skill_records(decoded.data))} habilidades registradas")
            self.validate(show=False)
        except Exception as e:
            self.log(f"FALLO DE CARGA: {e}\n{traceback.format_exc()}","exception");messagebox.showerror("No se pudo cargar data.sav",str(e))

    def _refresh_forms(self):
        c=self.current_root.get("characterDataMap",{})
        for key,var in self.identity_vars.items():var.set(str(c.get(key,"")))
        for key,var in self.stat_vars.items():var.set(str(c.get(key,"")))
        self.perks_text.delete("1.0","end");self.perks_text.insert("1.0","\n".join(map(str,c.get("perksList",[]))))
        self.render_skills(); self.update_catalog_combos()

    def apply_forms(self, silent=False):
        if self.current_root is None:
            if not silent: self.require_loaded()
            return False
        c=self.current_root.get("characterDataMap")
        if not isinstance(c,dict):
            if not silent: messagebox.showerror("Estructura","No existe characterDataMap")
            return False
        try:
            for key,var in self.identity_vars.items():
                value=var.get().strip()
                if value:c[key]=value
                elif key in c:c[key]=""
            for key,var in self.stat_vars.items():
                raw=var.get().strip()
                if raw=="":continue
                n=float(raw);c[key]=int(n) if n.is_integer() else n
            perks=list(dict.fromkeys(x.strip() for x in self.perks_text.get("1.0","end").splitlines() if x.strip()))
            c["perksList"]=perks
            self.dirty=True;self.refresh_raw();self.log("Controles de identidad, atributos y perks aplicados al JSON en memoria.")
            self.status.set("Cambios aplicados en memoria; todavía falta guardar/exportar")
            return True
        except Exception as e:
            if not silent: messagebox.showerror("Valor inválido",str(e))
            self.log(f"Error aplicando controles: {e}","exception")
            return False

    def render_skills(self):
        if not hasattr(self,"skill_tree"):return
        self.skill_tree.delete(*self.skill_tree.get_children());self._skill_rows=[]
        if self.current_root is None:return
        q=self.skill_filter.get().strip().lower()
        for rec in skill_records(self.current_root):
            if q and q not in rec["id"].lower():continue
            block=json.dumps(rec["block"],ensure_ascii=False)
            iid=self.skill_tree.insert("","end",values=(rec["id"],"SÍ" if rec["learned"] else "no",block,rec["offset"]))
            self._skill_rows.append((iid,rec["id"]))
        self.log(f"Vista de habilidades: {len(self._skill_rows)} registros visibles") if q=="" else None

    def toggle_skill(self,event=None):
        if not self.require_loaded():return
        item=self.skill_tree.focus()
        if not item:return
        vals=self.skill_tree.item(item,"values");sid=vals[0];learned=vals[1]!="SÍ"
        if set_skill(self.current_root,sid,learned):
            self.dirty=True;self.render_skills();self.refresh_raw();self.log(f"Habilidad {sid}: learned={learned}")

    def set_all_skills(self,learned):
        if not self.require_loaded():return
        arr=self.current_root.get("skillsDataMap",{}).get("skillsAllDataList",[]);count=0
        for i in range(0,len(arr)-4,5):arr[i+1]=bool(learned);count+=1
        self.dirty=True;self.render_skills();self.refresh_raw();self.log(f"PRUEBA MASIVA: {count} registros marcados learned={learned}","warning")

    def load_reference(self):
        f=filedialog.askopenfilename(title="Seleccionar data.sav de referencia",filetypes=[("Stoneshard save","*.sav"),("Todos","*.*")])
        if not f:return
        p=Path(f);cf=p.parent.parent.name;sf=p.parent.name
        if not re.fullmatch(r"character_\d+",cf,re.I):
            cf=simpledialog.askstring("Carpeta del personaje","Nombre exacto character_N para validar checksum:",initialvalue="character_1")
            if not cf:return
        try:
            d=decode_compressed_json(p,"sav",cf,sf);self.reference_root=d.data;self.reference_label=f"{cf}/{sf} · {'MD5 OK' if d.checksum_valid else 'MD5 ERROR'}"
            self.ref_label.set(self.reference_label);self.log(f"Referencia cargada: {p} checksum={'OK' if d.checksum_valid else 'ERROR'}")
            self.compare()
        except Exception as e:self.log(f"Error cargando referencia: {e}","exception");messagebox.showerror("Referencia inválida",str(e))

    def copy_reference(self,group):
        if not self.require_loaded():return
        if self.reference_root is None:messagebox.showinfo("Sin referencia","Primero cargá un segundo data.sav como referencia.");return
        src=self.reference_root.get("characterDataMap",{});dst=self.current_root.get("characterDataMap",{})
        if group in ("identity","appearance"):
            keys=["nameKey","classKey","playerClass","raceKey","sexKey"] if group=="identity" else ["avatar","Head","BodySprite","CorpseSprite"]
            for k in keys:
                if k in src:dst[k]=copy.deepcopy(src[k])
        elif group=="stats":
            for k in [x[1] for x in STAT_FIELDS]:
                if k in src:dst[k]=copy.deepcopy(src[k])
        elif group=="perks":dst["perksList"]=copy.deepcopy(src.get("perksList",[]))
        elif group=="skills":
            self.current_root["skillsDataMap"]=copy.deepcopy(self.reference_root.get("skillsDataMap",{}))
        self.dirty=True;self._refresh_forms();self.refresh_raw();self.log(f"Copiado grupo '{group}' desde {self.reference_label}. ¡No se modificó el archivo de referencia!")

    def compare(self):
        if not hasattr(self,"diff_text"):return
        self.diff_text.delete("1.0","end")
        if self.current_root is None or self.reference_root is None:
            self.diff_text.insert("end","Cargá un guardado principal y otro de referencia.");return
        a=self.current_root.get("characterDataMap",{});b=self.reference_root.get("characterDataMap",{})
        self.diff_text.insert("end",f"PRINCIPAL: {self.char_folder}/{self.save_folder}\nREFERENCIA: {self.reference_label}\n\nIDENTIDAD / APARIENCIA / ATRIBUTOS\n")
        keys=sorted(set(a)|set(b))
        for k in keys:
            if a.get(k)!=b.get(k):self.diff_text.insert("end",f"{k}:\n  actual: {a.get(k)!r}\n  ref:    {b.get(k)!r}\n")
        sa={r['id']:r['learned'] for r in skill_records(self.current_root)};sb={r['id']:r['learned'] for r in skill_records(self.reference_root)}
        changed=[(k,sa.get(k),sb.get(k)) for k in sorted(set(sa)|set(sb)) if sa.get(k)!=sb.get(k)]
        self.diff_text.insert("end",f"\nHABILIDADES: {len(sa)} registros vs {len(sb)}; {len(changed)} diferencias learned\n")
        for k,x,y in changed[:300]:self.diff_text.insert("end",f"  {k}: actual={x} referencia={y}\n")
        self.log(f"Comparación realizada: {len([k for k in keys if a.get(k)!=b.get(k)])} campos characterDataMap y {len(changed)} estados de habilidades distintos")

    def refresh_raw(self):
        if self.current_root is None:return
        self.raw_text.delete("1.0","end");self.raw_text.insert("1.0",json.dumps(self.current_root,ensure_ascii=False,indent=2))

    def apply_raw(self):
        if not self.require_loaded():return
        try:
            obj=json.loads(self.raw_text.get("1.0","end"))
            if not isinstance(obj,dict) or not isinstance(obj.get("characterDataMap"),dict) or not isinstance(obj.get("skillsDataMap"),dict):
                raise ValueError("Faltan characterDataMap o skillsDataMap.")
            self.current_root=obj;self.dirty=True;self._refresh_forms();self.log("JSON avanzado validado y aplicado a memoria.")
        except Exception as e:messagebox.showerror("JSON inválido",str(e));self.log(f"JSON avanzado rechazado: {e}","exception")

    def reset(self):
        if not self.require_loaded():return
        if not messagebox.askyesno("Restaurar", "¿Descartar todos los cambios en memoria y volver al guardado original cargado?"):return
        self.current_root=copy.deepcopy(self.original_root);self.dirty=False;self._refresh_forms();self.refresh_raw();self.log("Memoria restaurada al JSON original.")

    def validate(self,show=True):
        if not self.require_loaded():return
        issues=[];warnings=[];root=self.current_root;c=root.get("characterDataMap")
        if not isinstance(c,dict):issues.append("No existe characterDataMap válido.")
        else:
            for k in ["nameKey","classKey","playerClass","avatar","Head","BodySprite","CorpseSprite","raceKey","sexKey"]:
                if not c.get(k):warnings.append(f"Campo de identidad vacío: {k}")
            for k in ["STR","AGL","PRC","Vitality","WIL","LVL","XP","AP","SP"]:
                if k not in c:warnings.append(f"No aparece el campo numérico {k}")
                elif not isinstance(c[k],(int,float)):issues.append(f"{k} no es numérico: {c[k]!r}")
            if not isinstance(c.get("perksList",[]),list):issues.append("perksList no es una lista.")
        skills=root.get("skillsDataMap",{}).get("skillsAllDataList")
        if not isinstance(skills,list):issues.append("skillsAllDataList no es una lista.")
        elif len(skills)%5: warnings.append(f"skillsAllDataList tiene {len(skills)} elementos; no es múltiplo de 5.")
        else:
            ids=[str(skills[i]) for i in range(0,len(skills),5)]
            if len(ids)!=len(set(ids)):warnings.append("Hay identificadores de habilidad duplicados.")
        if self.current_path and self.char_folder and self.save_folder:
            try:
                d=decode_compressed_json(self.current_path,"sav",self.char_folder,self.save_folder)
                if not d.checksum_valid: warnings.append("El checksum del archivo cargado no coincide con su ruta. Exportar puede ser peligroso.")
            except Exception as e:issues.append(str(e))
        self.log(f"VALIDACIÓN: {len(issues)} error(es), {len(warnings)} advertencia(s).")
        for x in issues:self.log("ERROR: "+x,"error")
        for x in warnings:self.log("AVISO: "+x,"warning")
        if show:
            msg="ERRORES:\n"+("\n".join(issues) if issues else "Ninguno")+"\n\nADVERTENCIAS:\n"+("\n".join(warnings) if warnings else "Ninguna")
            messagebox.showinfo("Diagnóstico",msg)
        return issues,warnings

    def _encoded_current(self,char_folder=None,save_folder=None):
        return encode_compressed_json(self.current_root,"sav",char_folder or self.char_folder,save_folder or self.save_folder)

    def save_data_sav(self):
        """Write the edited data.sav back to the loaded path, keeping a .bak copy."""
        if not self.require_loaded():
            return
        if not self.current_path or not self.char_folder or not self.save_folder:
            messagebox.showerror("No se puede guardar", "Cargá data.sav desde una carpeta character_N/slot para identificar el checksum.")
            return
        if not self.apply_forms(silent=True):
            return
        target=Path(self.current_path)
        backup=target.with_name(target.name + ".bak")
        if not messagebox.askyesno(
            "Guardar data.sav editado",
            f"Se van a escribir TODOS los cambios actuales directamente en:\n\n{target}\n\n"
            f"Antes se conservará una copia de seguridad en:\n{backup}\n\n"
            "Esto reemplaza el data.sav cargado. Cerrá Stoneshard antes de continuar. ¿Guardar ahora?"
        ):
            return
        try:
            encoded=self._encoded_current()
            # Preserve the exact original bytes before replacing the active save.
            if target.exists() and not backup.exists():
                shutil.copy2(target, backup)
            target.write_bytes(encoded)
            check=decode_compressed_json(target,"sav",self.char_folder,self.save_folder)
            if not check.checksum_valid:
                raise RuntimeError("El archivo se escribió, pero la verificación de checksum falló.")
            self.original_root=copy.deepcopy(self.current_root)
            self.dirty=False
            self.status.set(f"GUARDADO: {target} · checksum correcto")
            self.checksum_label.configure(text="CHECKSUM: VÁLIDO", foreground="#75d69a")
            self.log(f"DATA.SAV GUARDADO DIRECTAMENTE: {target} | backup: {backup if backup.exists() else 'no requerido'}")
            messagebox.showinfo("data.sav guardado", f"¡Guardado correctamente!\n\nArchivo:\n{target}\n\nRespaldo:\n{backup if backup.exists() else 'No fue necesario crear uno nuevo'}\n\nChecksum verificado.")
        except Exception as e:
            self.log(f"ERROR guardando data.sav: {e}\n{traceback.format_exc()}","exception")
            messagebox.showerror("Error al guardar data.sav", str(e))

    def export_zip(self):
        if not self.require_loaded():return
        # Commit visible form values before validating/serializing. Previously the
        # export path could serialize stale in-memory JSON if Apply was not clicked.
        if not self.apply_forms(silent=True): return
        issues,warnings=self.validate(show=False)
        if issues:
            if not messagebox.askyesno("Hay errores", "La validación detectó errores. ¿Exportar de todos modos para experimentación?"):return
        if not messagebox.askyesno("Confirmar exportación", "Se creará un ZIP con data.sav y metadatos editados, más los originales intactos. No se sobrescribirá el guardado del juego. ¿Continuar?"):return
        out=filedialog.asksaveasfilename(title="Guardar paquete experimental",defaultextension=".zip",initialfile=f"StoneshardLab_{self.char_folder}_{self.save_folder}.zip",filetypes=[("ZIP","*.zip")])
        if not out:return
        try:
            edited=self._encoded_current()
            with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
                z.writestr(f"EDITED/{self.char_folder}/{self.save_folder}/data.sav",edited)
                z.write(self.current_path,f"BACKUP/{self.char_folder}_{self.save_folder}_data.sav.original")
                c=self.current_root.get("characterDataMap",{})
                if self.save_map and isinstance(self.save_map.data,dict):
                    smap=copy.deepcopy(self.save_map.data)
                    smap["nameKey"]=c.get("nameKey",smap.get("nameKey","")); smap["avatar"]=c.get("avatar",smap.get("avatar",""))
                    if "valid" in smap: smap["valid"]=True
                    z.writestr(f"EDITED/{self.char_folder}/{self.save_folder}/save.map",encode_compressed_json(smap,"save_map",self.char_folder,self.save_folder))
                    if (self.current_path.parent/"save.map").exists(): z.write(self.current_path.parent/"save.map",f"BACKUP/{self.char_folder}_{self.save_folder}_save.map.original")
                if self.character_map and isinstance(self.character_map.data,dict):
                    cmap=copy.deepcopy(self.character_map.data); cmap["nameKey"]=c.get("nameKey",cmap.get("nameKey",""))
                    z.writestr(f"EDITED/{self.char_folder}/character.map",encode_compressed_json(cmap,"character_map",self.char_folder))
                    cmap_path=self.current_path.parent.parent/"character.map"
                    if cmap_path.exists(): z.write(cmap_path,f"BACKUP/{self.char_folder}_character.map.original")
                z.writestr("README.txt", "STONESHARD CHARACTER LAB - EXPERIMENTAL EXPORT\n\nClose Stoneshard before testing. Extract EDITED into the parent characters_v1 directory only after backing up your saves. The untouched original data.sav and save.map are in BACKUP. Keep the backup.\n")
                z.writestr("DIAGNOSTICS.txt",self.diagnostic_report())
            self.dirty=False;self.log(f"ZIP exportado: {out}");messagebox.showinfo("Exportación lista",f"Se creó:\n{out}\n\nEl original quedó incluido en BACKUP.")
        except Exception as e:self.log(f"ERROR exportando: {e}\n{traceback.format_exc()}","exception");messagebox.showerror("Error de exportación",str(e))

    def clone_character(self):
        if not self.require_loaded():return
        if not self.current_path or not self.save_folder:messagebox.showerror("No disponible","La clonación requiere un data.sav cargado desde una carpeta con ruta identificada.");return
        # Commit text fields and perks automatically; no separate Apply click required.
        if not self.apply_forms(silent=True): return
        if not messagebox.askyesno("Guardar personaje para el juego", "Se van a guardar TODOS los cambios actuales —identidad, apariencia, atributos, progresión, perks, habilidades y JSON avanzado— en una carpeta character_N nueva, lista para copiar/probar en Stoneshard. No se modifica el personaje original.\n\nEn el siguiente cuadro elegí la carpeta characters_v1, es decir, la carpeta que contiene character_1, character_4, etc. ¿Continuar?"):return
        suggested = self.folder_path.parent if self.folder_path else self.current_path.parent.parent
        parent=filedialog.askdirectory(title="ELEGÍ characters_v1 (contiene carpetas character_N)",initialdir=str(suggested),mustexist=True)
        if not parent:return
        target_parent=Path(parent).expanduser().resolve()
        # If the user selected an individual character_N by mistake, use its parent.
        if re.fullmatch(r"character_\d+", target_parent.name, re.I):
            messagebox.showinfo("Carpeta detectada", f"Seleccionaste {target_parent.name}. Voy a guardar el nuevo personaje en su carpeta contenedora:\n{target_parent.parent}")
            target_parent=target_parent.parent
        if not target_parent.is_dir():
            messagebox.showerror("Destino inválido", "La carpeta de destino no existe o no es accesible.")
            return
        used=[]
        for p in target_parent.glob("character_*"):
            m=re.fullmatch(r"character_(\d+)",p.name,re.I)
            if m:used.append(int(m.group(1)))
        new_name=f"character_{max(used+[0])+1}"
        dest=target_parent/new_name
        try:
            if dest.exists():raise FileExistsError(dest)
            dest.mkdir(parents=True)
            # Keep only the active slot to avoid carrying stale, mismatched snapshots.
            slot=dest/self.save_folder;slot.mkdir()
            c=copy.deepcopy(self.current_root.get("characterDataMap",{}))
            # Keep characterDataMap as edited by the user. The map metadata mirrors the identity.
            cmap_data=copy.deepcopy(self.character_map.data if self.character_map else {})
            cmap_data["nameKey"]=c.get("nameKey",cmap_data.get("nameKey","Wanderer"))
            (dest/"character.map").write_bytes(encode_compressed_json(cmap_data,"character_map",new_name))
            smap_data=copy.deepcopy(self.save_map.data if self.save_map else {})
            smap_data["nameKey"]=c.get("nameKey",smap_data.get("nameKey","Wanderer"))
            smap_data["avatar"]=c.get("avatar",smap_data.get("avatar",""))
            if "valid" in smap_data:smap_data["valid"]=True
            (slot/"save.map").write_bytes(encode_compressed_json(smap_data,"save_map",new_name,self.save_folder))
            (slot/"data.sav").write_bytes(encode_compressed_json(self.current_root,"sav",new_name,self.save_folder))
            preview=self.current_path.parent/"preview.png"
            if preview.exists():shutil.copy2(preview,slot/"preview.png")
            report=("EXPERIMENTAL CHARACTER CLONE\n" f"New folder: {new_name}\nSource: {self.char_folder}/{self.save_folder}\n" f"Name: {c.get('nameKey')}\nAvatar: {c.get('avatar')}\n\n" "This clone contains ONLY the selected save slot. Preview image is copied unchanged and may not reflect edited appearance.\n")
            (dest/"CLONE_INFO.txt").write_text(report,encoding="utf-8")
            # Immediately re-open and verify all generated signatures.
            checks=[decode_compressed_json(dest/"character.map","character_map",new_name),decode_compressed_json(slot/"save.map","save_map",new_name,self.save_folder),decode_compressed_json(slot/"data.sav","sav",new_name,self.save_folder)]
            if not all(x.checksum_valid for x in checks):raise RuntimeError("La verificación posterior a la escritura falló.")
            self.log(f"CLON CREADO Y VERIFICADO: {dest}");messagebox.showinfo("¡Personaje guardado para probar!",f"CARPETA CREADA:\n{dest}\n\nARCHIVOS LISTOS:\n• character.map\n• {self.save_folder}/save.map\n• {self.save_folder}/data.sav\n\nLos tres checksums fueron verificados.\n\nAhora abrí Stoneshard. Si guardaste fuera de la carpeta del juego, copiá la carpeta {new_name} completa dentro de characters_v1. El personaje original no fue modificado.")
        except Exception as e:
            self.log(f"ERROR creando clon: {e}\n{traceback.format_exc()}","exception");messagebox.showerror("Error al clonar",f"{e}\n\nSi se creó una carpeta parcial, revisala y eliminá solo esa carpeta nueva.")

    def diagnostic_report(self):
        if self.current_root is None:return "No save loaded."
        c=self.current_root.get("characterDataMap",{})
        skills=skill_records(self.current_root)
        learned=[x["id"] for x in skills if x["learned"]]
        return (f"{APP_TITLE}\nGenerated: {datetime.now().isoformat()}\nPath: {self.current_path}\nFolder salt: {self.char_folder}/{self.save_folder}\n"
                f"Character: {c.get('nameKey')}\nClass: {c.get('classKey')} / {c.get('playerClass')}\nAvatar: {c.get('avatar')}\nHead: {c.get('Head')}\nBody: {c.get('BodySprite')}\nCorpse: {c.get('CorpseSprite')}\n"
                f"Sex/race: {c.get('sexKey')} / {c.get('raceKey')}\nStats: { {k:c.get(k) for k in ['STR','AGL','PRC','Vitality','WIL','LVL','XP','AP','SP']} }\nPerks: {c.get('perksList')}\n"
                f"Skills records: {len(skills)}\nLearned count: {len(learned)}\nLearned IDs: {learned}\n\nRoot keys: {list(self.current_root.keys())}\n")

    def save_report(self):
        if not self.require_loaded():return
        out=filedialog.asksaveasfilename(title="Guardar diagnóstico",defaultextension=".txt",initialfile="stoneshard_diagnostic.txt",filetypes=[("Texto","*.txt")])
        if not out:return
        Path(out).write_text(self.diagnostic_report(),encoding="utf-8");self.log(f"Informe guardado: {out}")

    def open_log(self):
        try:
            if sys.platform.startswith("win"):os.startfile(self.log_path)
            elif sys.platform=="darwin":os.system(f'open "{self.log_path}"')
            else:os.system(f'xdg-open "{self.log_path}" >/dev/null 2>&1 &')
        except Exception:messagebox.showinfo("Log",f"Archivo de log:\n{self.log_path}")

if __name__ == "__main__":
    app=CharacterLab();app.mainloop()
