import csv, ctypes, mmap, platform
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

VERSION = "0.1.0"
POLL_MS = 100

class Physics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId",ctypes.c_int32),("gas",ctypes.c_float),("brake",ctypes.c_float),
        ("fuel",ctypes.c_float),("gear",ctypes.c_int32),("rpms",ctypes.c_int32),
        ("steerAngle",ctypes.c_float),("speedKmh",ctypes.c_float),
        ("velocity",ctypes.c_float*3),("accG",ctypes.c_float*3),
        ("wheelSlip",ctypes.c_float*4),("wheelLoad",ctypes.c_float*4),
        ("wheelsPressure",ctypes.c_float*4),("wheelAngularSpeed",ctypes.c_float*4),
        ("tyreWear",ctypes.c_float*4),("tyreDirtyLevel",ctypes.c_float*4),
        ("tyreCoreTemperature",ctypes.c_float*4),("camberRAD",ctypes.c_float*4),
        ("suspensionTravel",ctypes.c_float*4),("drs",ctypes.c_float),("tc",ctypes.c_float),
        ("heading",ctypes.c_float),("pitch",ctypes.c_float),("roll",ctypes.c_float),
        ("cgHeight",ctypes.c_float),("carDamage",ctypes.c_float*5),
        ("numberOfTyresOut",ctypes.c_int32),("pitLimiterOn",ctypes.c_int32),
        ("abs",ctypes.c_float),("kersCharge",ctypes.c_float),("kersInput",ctypes.c_float),
        ("autoShifterOn",ctypes.c_int32),("rideHeight",ctypes.c_float*2)]
class Graphics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId",ctypes.c_int32),("status",ctypes.c_int32),("session",ctypes.c_int32),
        ("currentTime",ctypes.c_wchar*15),("lastTime",ctypes.c_wchar*15),
        ("bestTime",ctypes.c_wchar*15),("split",ctypes.c_wchar*15),
        ("completedLaps",ctypes.c_int32),("position",ctypes.c_int32),
        ("iCurrentTime",ctypes.c_int32),("iLastTime",ctypes.c_int32),
        ("iBestTime",ctypes.c_int32),("sessionTimeLeft",ctypes.c_float),
        ("distanceTraveled",ctypes.c_float),("isInPit",ctypes.c_int32),
        ("currentSectorIndex",ctypes.c_int32),("lastSectorTime",ctypes.c_int32),
        ("numberOfLaps",ctypes.c_int32),("tyreCompound",ctypes.c_wchar*33),
        ("replayTimeMultiplier",ctypes.c_float),("normalizedCarPosition",ctypes.c_float),
        ("carCoordinates",ctypes.c_float*3),("penaltyTime",ctypes.c_float),
        ("flag",ctypes.c_int32),("idealLineOn",ctypes.c_int32)]
class Static(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion",ctypes.c_wchar*15),("acVersion",ctypes.c_wchar*15),
        ("numberOfSessions",ctypes.c_int32),("numCars",ctypes.c_int32),
        ("carModel",ctypes.c_wchar*33),("track",ctypes.c_wchar*33),
        ("playerName",ctypes.c_wchar*33),("playerSurname",ctypes.c_wchar*33),
        ("playerNick",ctypes.c_wchar*33),("sectorCount",ctypes.c_int32),
        ("maxTorque",ctypes.c_float),("maxPower",ctypes.c_float),
        ("maxRpm",ctypes.c_int32),("maxFuel",ctypes.c_float),
        ("suspensionMaxTravel",ctypes.c_float*4),("tyreRadius",ctypes.c_float*4)]

class ACReader:
    def __init__(self): self.maps = {}
    def connect(self):
        if platform.system() != "Windows":
            raise RuntimeError("This build runs on Windows.")
        types = {"physics":Physics,"graphics":Graphics,"static":Static}
        opened = {}
        try:
            for key, struct in types.items():
                opened[key] = mmap.mmap(0,ctypes.sizeof(struct),"acpmf_"+key)
        except (OSError,ValueError) as e:
            for m in opened.values(): m.close()
            raise RuntimeError("Assetto Corsa shared memory was not found. Start the original Assetto Corsa, enter a driving session, and enable Shared Memory in Settings → General.") from e
        self.maps = opened
    def read(self):
        p = Physics.from_buffer_copy(self.maps["physics"][:ctypes.sizeof(Physics)])
        g = Graphics.from_buffer_copy(self.maps["graphics"][:ctypes.sizeof(Graphics)])
        s = Static.from_buffer_copy(self.maps["static"][:ctypes.sizeof(Static)])
        return p,g,s
    def close(self):
        for m in self.maps.values():
            try: m.close()
            except OSError: pass
        self.maps = {}

class App:
    def __init__(self, root):
        self.root=root; self.root.title("APEXLINE Link  ·  0.1.0")
        self.root.geometry("720x520"); self.root.minsize(620,470); self.root.configure(bg="#0b0e11")
        self.reader=ACReader(); self.connected=False; self.recording=False; self.file=None; self.writer=None
        self._ui(); self.root.protocol("WM_DELETE_WINDOW",self.close); self.root.after(250,self.tick)
    def _ui(self):
        head=tk.Frame(self.root,bg="#10161b",padx=24,pady=18); head.pack(fill="x")
        tk.Label(head,text="APEXLINE",bg="#10161b",fg="#c7ff3d",font=("Segoe UI",20,"bold")).pack(side="left")
        tk.Label(head,text="LINK  /  ASSETTO CORSA",bg="#10161b",fg="#9ba5ae",font=("Segoe UI",9,"bold")).pack(side="right",pady=8)
        body=tk.Frame(self.root,bg="#0b0e11",padx=24,pady=22); body.pack(fill="both",expand=True)
        self.status=tk.Label(body,text="●  NOT CONNECTED",bg="#0b0e11",fg="#ffbd70",font=("Segoe UI",10,"bold")); self.status.pack(anchor="w")
        self.session=tk.Label(body,text="Open Assetto Corsa and enter a driving session",bg="#0b0e11",fg="#aab3bb",font=("Segoe UI",10)); self.session.pack(anchor="w",pady=(5,15))
        grid=tk.Frame(body,bg="#0b0e11"); grid.pack(fill="x"); self.values={}
        for i,(name,unit) in enumerate([("SPEED","km/h"),("RPM","rpm"),("GEAR",""),("THROTTLE","%"),("BRAKE","%"),("FUEL","L")]):
            card=tk.Frame(grid,bg="#141b21",padx=15,pady=13,highlightbackground="#303a43",highlightthickness=1)
            card.grid(row=i//3,column=i%3,sticky="nsew",padx=5,pady=5)
            tk.Label(card,text=name,bg="#141b21",fg="#929da6",font=("Segoe UI",9,"bold")).pack(anchor="w")
            value=tk.Label(card,text="—",bg="#141b21",fg="#f4f6f8",font=("Segoe UI",24,"bold")); value.pack(anchor="w",pady=3)
            tk.Label(card,text=unit,bg="#141b21",fg="#87919b",font=("Segoe UI",8)).pack(anchor="w")
            self.values[name]=value
        for i in range(3): grid.columnconfigure(i,weight=1)
        info=tk.Frame(body,bg="#141b21",padx=15,pady=12); info.pack(fill="x",pady=(13,0))
        self.laps=tk.Label(info,text="LAP —    LAST —    BEST —",bg="#141b21",fg="#d4dbe0",font=("Segoe UI",10,"bold")); self.laps.pack(anchor="w")
        self.car=tk.Label(info,text="CAR —    TRACK —",bg="#141b21",fg="#929da6",font=("Segoe UI",9)); self.car.pack(anchor="w",pady=(6,0))
        buttons=tk.Frame(body,bg="#0b0e11"); buttons.pack(fill="x",pady=17)
        self.connect_btn=tk.Button(buttons,text="CONNECT TO ASSETTO CORSA",command=self.connect,bg="#c7ff3d",fg="#10140a",relief="flat",font=("Segoe UI",10,"bold"),padx=16,pady=11); self.connect_btn.pack(side="left")
        self.record_btn=tk.Button(buttons,text="●  START RECORDING",command=self.record,bg="#202830",fg="white",relief="flat",font=("Segoe UI",9,"bold"),padx=14,pady=11,state="disabled"); self.record_btn.pack(side="left",padx=10)
        self.note=tk.Label(body,text="LINK READY  ·  LIVE TELEMETRY READER",bg="#202b1b",fg="#d9e8c5",anchor="w",font=("Segoe UI",9),padx=13,pady=11); self.note.pack(fill="x")
        tk.Label(body,text="Original Assetto Corsa only  ·  CSV saved in Documents/APEXLINE/sessions",bg="#0b0e11",fg="#65717b",font=("Segoe UI",8)).pack(anchor="w",pady=(12,0))
    def connect(self):
        try:
            self.reader.connect(); self.connected=True
            self.status.config(text="●  CONNECTED",fg="#c7ff3d"); self.connect_btn.config(text="DISCONNECT",command=self.disconnect); self.record_btn.config(state="normal")
        except RuntimeError as e: messagebox.showwarning("Simulator not detected",str(e))
    def disconnect(self):
        self.stop(); self.reader.close(); self.connected=False
        self.status.config(text="●  NOT CONNECTED",fg="#ffbd70"); self.connect_btn.config(text="CONNECT TO ASSETTO CORSA",command=self.connect); self.record_btn.config(state="disabled")
    def record(self):
        if self.recording: self.stop(); return
        folder=Path.home()/"Documents"/"APEXLINE"/"sessions"; folder.mkdir(parents=True,exist_ok=True)
        path=folder/f"AC_{datetime.now():%Y%m%d_%H%M%S}.csv"; self.file=path.open("w",newline="",encoding="utf-8")
        self.writer=csv.writer(self.file); self.writer.writerow(["timestamp","speed_kmh","rpm","gear","throttle","brake","fuel_l","steering","completed_laps","lap_time","best_lap","car","track"])
        self.recording=True; self.record_btn.config(text="■  STOP RECORDING",bg="#56332d"); self.note.config(text=f"RECORDING  ·  {path}")
    def stop(self):
        if self.file: self.file.flush(); self.file.close()
        self.file=None; self.writer=None; self.recording=False
        if hasattr(self,"record_btn"): self.record_btn.config(text="●  START RECORDING",bg="#202830")
    def tick(self):
        if self.connected:
            try:
                p,g,s=self.reader.read()
                self.values["SPEED"].config(text=f"{p.speedKmh:.1f}"); self.values["RPM"].config(text=f"{p.rpms:,}")
                self.values["GEAR"].config(text="R" if p.gear==0 else ("N" if p.gear==1 else str(p.gear-1)))
                self.values["THROTTLE"].config(text=f"{p.gas*100:.0f}"); self.values["BRAKE"].config(text=f"{p.brake*100:.0f}"); self.values["FUEL"].config(text=f"{p.fuel:.1f}")
                self.session.config(text="LIVE SESSION" if g.status==2 else "Simulator detected · waiting for live session")
                self.laps.config(text=f"LAP {g.completedLaps+1}    LAST {g.lastTime or '—'}    BEST {g.bestTime or '—'}")
                self.car.config(text=f"CAR {s.carModel or '—'}    TRACK {s.track or '—'}")
                if self.recording and self.writer:
                    self.writer.writerow([datetime.now().isoformat(timespec="milliseconds"),round(p.speedKmh,2),p.rpms,p.gear,round(p.gas,4),round(p.brake,4),round(p.fuel,3),round(p.steerAngle,4),g.completedLaps,g.lastTime,g.bestTime,s.carModel,s.track])
                if p.speedKmh>40 and p.gas<.08 and p.brake<.08: cue="Coasting detected — review whether this phase is intentional."
                elif p.brake>.75 and p.speedKmh>100: cue="Heavy braking phase detected. Keep the initial input firm and controlled."
                elif p.gas>.9 and p.speedKmh>40: cue="Full throttle detected. Focus on a clean exit."
                else: cue="Telemetry flowing. Focus on smooth, repeatable inputs."
                self.note.config(text="DRIVING NOTE  ·  "+cue)
            except (OSError,ValueError,BufferError):
                self.disconnect(); self.status.config(text="●  CONNECTION LOST  ·  RECONNECT IN SESSION",fg="#ffbd70")
        self.root.after(POLL_MS,self.tick)
    def close(self):
        self.stop(); self.reader.close(); self.root.destroy()

def main():
    root=tk.Tk(); App(root); root.mainloop()
if __name__=="__main__": main()
