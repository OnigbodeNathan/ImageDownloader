import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any, Dict, List

from Github1 import download_images_for_query
from key_point_extractor import extract_key_points


class WorkflowApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Image Workflow")
        self.root.geometry("980x700")
        self.root.minsize(760, 560)
        self.key_points: List[str] = []
        self.search_results: Dict[str, Any] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        root = self.root
        root.columnconfigure(0, weight=3)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(1, weight=1)

        header = ttk.Frame(root, padding=(24, 20, 24, 12))
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Label(header, text="Image workflow", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Turn a brief into key points, web context, and a local image set.",
        ).pack(anchor="w", pady=(4, 0))

        source_frame = ttk.LabelFrame(root, text="1. Source brief", padding=14)
        source_frame.grid(row=1, column=0, sticky="nsew", padx=(24, 10), pady=(0, 24))
        source_frame.rowconfigure(0, weight=1)
        source_frame.columnconfigure(0, weight=1)
        self.source_text = ScrolledText(source_frame, wrap="word", height=12, font=("Segoe UI", 11))
        self.source_text.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.source_text.insert(
            "1.0",
            "Describe the images you need here. For example: warm editorial photos of a small team planning a sustainable product launch in a bright studio.",
        )
        self.search_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            source_frame,
            text="Also search each key point with Gemini",
            variable=self.search_enabled,
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Button(source_frame, text="Extract key points", command=self.extract).grid(
            row=1, column=1, sticky="e", pady=(12, 0)
        )

        right = ttk.Frame(root)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 24), pady=(0, 24))
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="2. Key points", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.points_list = tk.Listbox(right, height=7, activestyle="none", font=("Segoe UI", 10))
        self.points_list.grid(row=1, column=0, sticky="nsew", pady=(6, 16))

        ttk.Label(right, text="3. Run", font=("Segoe UI", 12, "bold")).grid(row=2, column=0, sticky="w")
        run_frame = ttk.Frame(right)
        run_frame.grid(row=3, column=0, sticky="nsew", pady=(6, 0))
        run_frame.columnconfigure(1, weight=1)
        ttk.Label(run_frame, text="Pexels API key").grid(row=0, column=0, sticky="w", pady=4)
        self.pexels_key = ttk.Entry(run_frame, show="*", width=28)
        self.pexels_key.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)
        ttk.Label(run_frame, text="Gemini API key").grid(row=1, column=0, sticky="w", pady=4)
        self.gemini_key = ttk.Entry(run_frame, show="*", width=28)
        self.gemini_key.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)
        self.download_button = ttk.Button(run_frame, text="Download images", command=self.start_workflow)
        self.download_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 4))
        ttk.Label(run_frame, text="Images are saved in pexels_images.", foreground="#666666").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(2, 0)
        )

        log_frame = ttk.LabelFrame(root, text="Activity", padding=10)
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=24, pady=(0, 20))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = ScrolledText(log_frame, height=8, state="disabled", wrap="word", font=("Consolas", 9))
        self.log.grid(row=0, column=0, sticky="nsew")
        self.status = ttk.Label(root, text="Ready", padding=(24, 0, 24, 12))
        self.status.grid(row=3, column=0, columnspan=2, sticky="ew")

    def write_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def extract(self) -> None:
        text = self.source_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Missing brief", "Enter a source brief first.")
            return
        self.key_points = extract_key_points(text)
        self.points_list.delete(0, "end")
        for point in self.key_points:
            self.points_list.insert("end", point)
        self.status.configure(text=f"Ready with {len(self.key_points)} key point(s).")
        self.write_log(f"Extracted {len(self.key_points)} key point(s).")

    def start_workflow(self) -> None:
        if not self.key_points:
            self.extract()
        pexels_key = self.pexels_key.get().strip() or os.getenv("PEXELS_API_KEY", "").strip()
        if not self.key_points:
            return
        if not pexels_key:
            messagebox.showwarning("Missing Pexels key", "Enter a Pexels API key or set PEXELS_API_KEY.")
            return
        source_text = self.source_text.get("1.0", "end").strip()
        run_search = self.search_enabled.get()
        if run_search:
            gemini_key = self.gemini_key.get().strip() or os.getenv("GEMINI_API_KEY", "").strip()
            if not gemini_key:
                messagebox.showwarning("Missing Gemini key", "Enter a Gemini API key or disable web search.")
                return
            os.environ["GEMINI_API_KEY"] = gemini_key
        os.environ["PEXELS_API_KEY"] = pexels_key
        self.download_button.configure(state="disabled")
        self.status.configure(text="Running workflow...")
        threading.Thread(target=self._run_workflow, args=(source_text, run_search), daemon=True).start()

    def _run_workflow(self, source_text: str, run_search: bool) -> None:
        try:
            if run_search:
                from key_point_search_tool import search_key_points

                self._ui_log("Searching key points with Gemini...")
                self.search_results = search_key_points(source_text, count=5)
                self._ui_log(f"Found context for {len(self.search_results.get('searches', []))} key point(s).")
            headers = {"Authorization": os.environ["PEXELS_API_KEY"]}
            total = 0
            for point in self.key_points:
                total += download_images_for_query(point, headers, on_progress=self._ui_log)
            self._ui_log(f"Workflow complete. Downloaded {total} image(s) to pexels_images.")
            self.root.after(0, lambda: self.status.configure(text=f"Complete: {total} image(s) downloaded."))
        except Exception as exc:
            self._ui_log(f"Workflow failed: {exc}")
            self.root.after(0, lambda: self.status.configure(text="Workflow failed. See activity log."))
        finally:
            self.root.after(0, lambda: self.download_button.configure(state="normal"))

    def _ui_log(self, message: str) -> None:
        self.root.after(0, lambda: self.write_log(message))


def main() -> None:
    root = tk.Tk()
    WorkflowApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()