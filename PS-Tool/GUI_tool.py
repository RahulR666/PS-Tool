import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, PanedWindow, Toplevel, Label, Button
from PIL import Image, ImageTk
import csv
import json
import traceback


class FolderNavigator:
    def __init__(self, parent, on_folder_change):
        self.parent = parent
        self.on_folder_change = on_folder_change
        self.current_path = ""
        self.all_folders = []

        self.frame = tk.Frame(parent, width=250)
        self.frame.grid(row=0, column=0, sticky="nsew")


        # Label
        self.label = tk.Label(self.frame, text="📁 Folders", font=("Arial", 12, "bold"))
        self.label.pack(pady=(10, 5))

        # 🔍 Search Bar
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_filter)
        self.search_entry = tk.Entry(self.frame, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Listbox for folders
        self.listbox = tk.Listbox(self.frame)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10)
        self.listbox.bind("<<ListboxSelect>>", self.handle_selection)

        # Select button
        #self.select_button = tk.Button(self.frame, text="Select Folder", command=self.select_folder)
        #self.select_button.pack(pady=10)


    # def select_folder(self):
    #     folder_path = filedialog.askdirectory(title="🗂️ Choose Folder to Load Images")
    #     if folder_path:
    #         self.load(folder_path)
    #         self.on_folder_change(folder_path)

    def load(self, path):
        self.current_path = path
        try:
            self.all_folders = sorted([
                d for d in os.listdir(path)
                if os.path.isdir(os.path.join(path, d))
            ])
            self.update_filter()
        except Exception as e:
            self.on_folder_change.log_error(f"Error loading folders: {e}")

    def update_filter(self, *args):
        filter_text = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, ".. (Go Up)")

        for folder in self.all_folders:
            if filter_text in folder.lower():
                self.listbox.insert(tk.END, folder)


    def handle_selection(self, event):
        index = self.listbox.curselection()
        if not index:
            return

        selection = self.listbox.get(index[0])
        if selection.startswith(".."):
            new_path = os.path.dirname(self.current_path)
        else:
            new_path = os.path.join(self.current_path, selection)

        if os.path.exists(new_path) and os.path.isdir(new_path):
            # 👇 Call the main app's folder load method
            self.on_folder_change(new_path)

            # 👇 Update sidebar list to reflect new folder
            self.load(new_path)




class ImageSelectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Deep Terrain AI PS-Tool")
        # self.sidebar_default_width = 490
        # self.attribute_default_width = 700  # or whatever width feels good

        self.root.tk.call('tk', 'scaling', 1.5)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.sidebar_default_width = min(int(self.screen_width * 0.20),500)     # 20% of screen width
        self.attribute_default_width = min(int(self.screen_width * 0.25),700)   # 25% of screen width

        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.zoom_level = 1.0
        self.original_image = None  # Store full-res image
        self.image_offset = (0, 0)
        self.pan_start = None

        self.human_attributes_frames = {}
        self.human_attributes = {}

        # Initialize defaults
        self.input_dir = ""
        self.output_dir = ""
        self.csv_file = ""
        self.image_paths = []
        self.current_index = 0
        self.selected_images = set()
        self.tk_image = None
        self.current_folder = ""
        self.current_image_path = ""
        self.last_logged_image = ""

        self.folder_visible = True
        self.log_visible = True
        self.dark_mode = False

        # First: setup UI
        self.setup_ui()

        # Then: ask folder (AFTER sidebar exists)
        start_dir = filedialog.askdirectory(title="📂 Choose base folder to explore")
        if start_dir:
            self.sidebar.load(start_dir)
            self.current_folder = start_dir
        else:
            messagebox.showinfo("No Folder", "No base folder selected. Exiting.")
            self.root.destroy()

    def bind_mousewheel_scroll(self, widget, canvas):
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")  # For Windows/macOS
        widget.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/macOS
        widget.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
        widget.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down

    def unbind_mousewheel_scroll(self, widget):
        widget.unbind_all("<MouseWheel>")
        widget.unbind_all("<Button-4>")
        widget.unbind_all("<Button-5>")


    def zoom_image(self, factor):
        self.zoom_level *= factor
        self.show_image()

    def zoom_in(self):
        self.zoom_level *= 1.1
        self.show_image()

    def zoom_out(self):
        self.zoom_level /= 1.1
        self.show_image()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.image_offset = (0, 0)
        self.show_image()



    def handle_mouse_zoom(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def start_pan(self, event):
        self.pan_start = (event.x, event.y)

    def do_pan(self, event):
        if self.pan_start:
            dx = event.x - self.pan_start[0]
            dy = event.y - self.pan_start[1]
            self.image_offset = (self.image_offset[0] + dx, self.image_offset[1] + dy)
            self.pan_start = (event.x, event.y)
            self.show_image()

    def end_pan(self, event):
        self.pan_start = None

    def show_error_popup(self, message):
        popup = Toplevel(self.root)
        popup.title("❌ Error")
        width, height = 600, 300
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")

        Label(popup, text=message, font=("Arial", 12), fg="red", padx=20, pady=10).pack(expand=True)
        Button(popup, text="OK", command=popup.destroy, width=10).pack(pady=10)

    def setup_file_paths(self):
        self.output_dir = filedialog.askdirectory(title="📤 Choose Output Folder")
        if not self.output_dir:
            self.show_error_popup("No output folder selected.")
            return False

        self.csv_file = filedialog.asksaveasfilename(
            title="📝 Save CSV File",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not self.csv_file:
            self.show_error_popup("No CSV file selected.")
            return False

        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    self.selected_images.add(row[0])

        return True
    
    

    def setup_ui(self):
        print("👀 setup_ui is running...")

        # Layout config
        self.root.rowconfigure(1, weight=1)  # Folder / Image / Attributes row
        self.root.rowconfigure(2, weight=0)  # Controls
        self.root.rowconfigure(3, weight=0)  # Terminal

        self.root.columnconfigure(0, minsize=self.sidebar_default_width)
        self.root.columnconfigure(1, weight=1)  # Image viewer stretches
        self.root.columnconfigure(2, minsize=self.attribute_default_width, weight=0)

        self.accessory_btn_normal_color = "#f0f0f0"
        self.accessory_btn_selected_color = "#555555"
        self.selected_accessories = set()
        self.accessory_buttons = {}

        # --- Toggle Buttons ---
        toggle_frame = tk.Frame(self.root)
        toggle_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=3)

        self.theme_toggle_btn = tk.Button(toggle_frame, text="🌙 Dark Mode", command=self.toggle_theme)
        self.theme_toggle_btn.pack(side=tk.RIGHT, padx=5)

    

        # --- Folder Panel ---
        self.sidebar = FolderNavigator(self.root, self.on_folder_selected)
        self.sidebar_frame = self.sidebar.frame
        self.sidebar_frame.grid(row=1, column=0, rowspan=3, sticky="nsew")
        # self.sidebar_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self.sidebar_frame.grid_propagate(False)

        # --- Image Viewer ---
        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.grid(row=1, column=1, sticky="nsew")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<ButtonRelease-1>", self.end_pan)

        # Mouse scroll for zoom (Linux: Button-4/5 | Windows/Mac: MouseWheel)
        self.canvas.bind("<MouseWheel>", self.handle_mouse_zoom)  # Windows/Mac
        self.canvas.bind("<Button-4>", lambda e: self.zoom_in())  # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self.zoom_out())  # Linux scroll down
        # Linux scroll down


        # --- Scrollable Attribute Panel ---
        self.attribute_frame = tk.LabelFrame(self.root, text="🧬 Attributes", font=("Arial", 12, "bold"))
        self.attribute_frame.grid(row=1, column=2, rowspan=3, sticky="nsew")
        self.attribute_frame.grid_propagate(False)

        # Create canvas and scrollbar inside attribute_frame
        self.attribute_canvas = tk.Canvas(self.attribute_frame, highlightthickness=0)
        self.attribute_scrollbar = tk.Scrollbar(self.attribute_frame, orient="vertical", command=self.attribute_canvas.yview)
        self.attribute_canvas.configure(yscrollcommand=self.attribute_scrollbar.set)

        self.attribute_canvas.pack(side="left", fill="both", expand=True)
        self.attribute_scrollbar.pack(side="right", fill="y")

        # Inner frame where actual attribute widgets go
        self.scrollable_attribute_frame = tk.Frame(self.attribute_canvas)
        self.scrollable_attribute_frame.bind("<Configure>", lambda e: self.attribute_canvas.configure(scrollregion=self.attribute_canvas.bbox("all")))
        self.attribute_canvas.create_window((0, 0), window=self.scrollable_attribute_frame, anchor="nw")

        # Optional: Scroll on mousewheel when pointer is inside the attribute frame
            # Scroll on mouse wheel when pointer is inside the attribute frame
        self.scrollable_attribute_frame.bind(
            "<Enter>", lambda e: self.bind_mousewheel_scroll(self.scrollable_attribute_frame, self.attribute_canvas)
        )
        self.scrollable_attribute_frame.bind(
            "<Leave>", lambda e: self.unbind_mousewheel_scroll(self.scrollable_attribute_frame)
        )

        # Now build the actual attributes inside scrollable area
        self.build_attribute_panel(self.scrollable_attribute_frame)


        # --- Controls (Below Image Viewer only) ---
        control_frame = tk.Frame(self.root)
        control_frame.grid(row=2, column=1, sticky="ew", padx=10, pady=(0, 5))

        self.scene_entry = tk.Entry(control_frame)
        self.scene_entry.pack(fill=tk.X, pady=5)
        self.scene_entry.insert(0, "Enter scene ID or leave blank")

        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(fill=tk.X)

        self.zoom_in_btn = tk.Button(btn_frame, text="🔍➕", command=lambda: self.zoom_image(1.1))
        self.zoom_in_btn.pack(side=tk.LEFT, padx=5)

        self.zoom_out_btn = tk.Button(btn_frame, text="🔍➖", command=lambda: self.zoom_image(0.9))
        self.zoom_out_btn.pack(side=tk.LEFT, padx=5)


        self.select_btn = tk.Button(btn_frame, text="✅ Select", command=self.select_image)
        self.select_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.next_btn = tk.Button(btn_frame, text="➡️ Next", command=self.next_image)
        self.next_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.quit_btn = tk.Button(btn_frame, text="❌ Quit", command=self.quit_app)
        self.quit_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.undo_btn = tk.Button(btn_frame, text="⏪ Undo", command=self.undo_last_selection)
        self.undo_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # --- Terminal / Log (Below Image Viewer only) ---
        self.log_frame = tk.Frame(self.root)
        self.log_frame.grid(row=3, column=1, sticky="nsew")

        self.log_output = tk.Text(self.log_frame, height=12, state='disabled', bg='black', fg='white')
        self.log_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(5, 10))

        scrollbar = tk.Scrollbar(self.log_frame, command=self.log_output.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(5, 10))
        self.log_output['yscrollcommand'] = scrollbar.set

        self.apply_theme()
        print("✅ setup_ui completed!")


    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _unbind_mousewheel(self, widget):
        widget.unbind_all("<MouseWheel>")


    def on_mouse_scroll_zoom(self, event):
        if event.num == 4 or event.delta > 0:   # Scroll up
            self.zoom_image(1.1)
        elif event.num == 5 or event.delta < 0: # Scroll down
            self.zoom_image(0.9)

    
    def build_attribute_panel(self, parent):
        for i in range(3):
            parent.columnconfigure(i, weight=1)  # ✅ use `parent`, not `self.attribute_frame`

        row = 0

        # Class Dropdown
        tk.Label(parent, text="Class:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        self.class_var = tk.StringVar(value="Select")
        class_menu = tk.OptionMenu(parent, self.class_var, "Intruder (Human)", "Empty Frame", "Select")  # ✅ was self.attribute_frame
        class_menu.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)
        self.class_var.trace_add("write", lambda *args: self.update_attribute_states())

        row += 1

        # Time of Day
        tk.Label(parent, text="Time of Day:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        self.time_var = tk.StringVar(value="Select")
        self.time_menu = tk.OptionMenu(parent, self.time_var, "Morning", "Noon", "Evening", "Night", "Select")  # ✅ fixed parent
        self.time_menu.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)

        row += 1

        # Human Count
        tk.Label(parent, text="Humans:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w", pady=2)
        self.num_humans_var = tk.StringVar(value="Select")
        self.human_menu = tk.OptionMenu(parent, self.num_humans_var, *["Select"] + list(map(str, range(0, 7))), command=self.render_human_frames)
        self.human_menu.grid(row=row, column=1, columnspan=2, sticky="ew", pady=2)

        row += 1

        # Dynamic container for human attribute frames
        self.human_attributes_container = tk.Frame(parent)
        self.human_attributes_container.grid(row=row, column=0, columnspan=3, sticky="nsew")

    def render_human_frames(self, count_str):
        # Remove existing dynamic frames
        for frame in self.human_attributes_frames.values():
            frame.destroy()
        self.human_attributes_frames.clear()
        self.human_attributes.clear()

        if count_str == "Select":
            return

        try:
            count = int(count_str)
        except ValueError:
            return

        for i in range(count):
            frame = self.build_human_subframe(self.human_attributes_container, i)
            frame.pack(fill="x", pady=5)
            self.human_attributes_frames[i] = frame


    def update_human_attribute_frames(self, *args):
        # Remove old frames if any
        for frame in self.human_attributes_frames.values():
            frame.destroy()

        self.human_attributes_frames.clear()
        self.human_attributes.clear()

        try:
            num = int(self.num_humans_var.get())
        except ValueError:
            return

        row = 4  # Starting row in the attribute panel (after Class, Time, Human Count)

        for i in range(num):
            # Frame for this human's attributes
            human_frame = tk.LabelFrame(self.attribute_frame, text=f"👤 Human {i+1}", font=("Arial", 10, "bold"))
            human_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=5)
            row += 1

            self.human_attributes_frames[i] = human_frame
            self.human_attributes[i] = self.build_human_subframe(human_frame)

    def build_human_subframe(self, parent, index):
        frame = tk.LabelFrame(parent, text=f"Human {index + 1}", padx=5, pady=5, font=("Arial", 10, "bold"))
        self.human_attributes[index] = {}

        # Row counter within this frame
        row = 0

        # Action
        tk.Label(frame, text="Action:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        action_var = tk.StringVar(value="Select")
        action_menu = tk.OptionMenu(frame, action_var, "Walking", "Running", "Crawling", "Crouch-walking",
                                    "Sitting", "Standing", "Lying", "Climbing", "Select")
        action_menu.grid(row=row, column=1, sticky="ew", pady=2)
        self.human_attributes[index]['action_var'] = action_var

        # Gender
        row += 1
        tk.Label(frame, text="Gender:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        gender_var = tk.StringVar(value="Select")
        gender_menu = tk.OptionMenu(frame, gender_var, "Male", "Female", "Unknown", "Select")
        gender_menu.grid(row=row, column=1, sticky="ew", pady=2)
        self.human_attributes[index]['gender_var'] = gender_var

        # Age
        row += 1
        tk.Label(frame, text="Age Group:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        age_var = tk.StringVar(value="Select")
        age_menu = tk.OptionMenu(frame, age_var, "Child", "Adult", "Old", "Unknown", "Select")
        age_menu.grid(row=row, column=1, sticky="ew", pady=2)
        self.human_attributes[index]['age_var'] = age_var

        # Distance
        row += 1
        tk.Label(frame, text="Distance:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        distance_var = tk.StringVar(value="Select")
        distance_menu = tk.OptionMenu(frame, distance_var,
                                    "0-10m", "10-20m", "20-50m", "50-75m", "75-100m", "100m+", "Select")
        distance_menu.grid(row=row, column=1, sticky="ew", pady=2)
        self.human_attributes[index]['distance_var'] = distance_var

        # Occlusion
        row += 1
        tk.Label(frame, text="Occlusion:", font=("Arial", 9)).grid(row=row, column=0, sticky="w", pady=2)
        occlusion_var = tk.StringVar(value="Select")
        occlusion_menu = tk.OptionMenu(frame, occlusion_var, "Select", ">25%", ">50%", ">75%", "100%", "None")
        occlusion_menu.grid(row=row, column=1, sticky="ew", pady=2)
        self.human_attributes[index]['occlusion_var'] = occlusion_var

        # Accessories
        row += 1
        tk.Label(frame, text="Accessories:", font=("Arial", 9)).grid(row=row, column=0, sticky="nw", pady=2)

        accessory_options = ["Bag", "Mask", "Cap", "Hoodie", "Scarf", "Unidentified", "None"]
        accessory_buttons = {}

        acc_frame = tk.Frame(frame)
        acc_frame.grid(row=row, column=1, sticky="ew", pady=2)
        acc_frame.columnconfigure(0, weight=1)
        acc_frame.columnconfigure(1, weight=1)

        def toggle(acc, btn):
            if btn.cget("relief") == tk.SUNKEN:
                btn.config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")
            else:
                if acc in ["Unidentified", "None"]:
                    for other_acc, b in accessory_buttons.items():
                        b.config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")
                else:
                    for exclusive in ["Unidentified", "None"]:
                        accessory_buttons[exclusive].config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")
                btn.config(relief="sunken", bg=self.accessory_btn_selected_color, fg="white")

        for i, acc in enumerate(accessory_options):
            col = i % 2
            row_idx = i // 2
            btn = tk.Button(
                acc_frame, text=acc, relief="raised", width=10,
                bg=self.accessory_btn_normal_color,
                command=lambda acc=acc, btn=None: None  # Placeholder
            )
            btn.grid(row=row_idx, column=col, sticky="ew", padx=2, pady=2)
            accessory_buttons[acc] = btn

        # Now update command using correct button reference
        for acc, btn in accessory_buttons.items():
            btn.config(command=lambda acc=acc, btn=btn: toggle(acc, btn))

        self.human_attributes[index]['accessory_buttons'] = accessory_buttons

        return frame


    def handle_human_count_change(self, *args):
        # Clear existing human frames
        for frame in self.human_attributes_frames.values():
            frame.destroy()
        self.human_attributes_frames.clear()
        self.human_attributes.clear()

        try:
            count = int(self.num_humans_var.get())
        except ValueError:
            return  # If it's "Select" or invalid input

        for i in range(count):
            self.build_human_subframe(i)

            

    def on_class_change(self):
        class_selected = self.class_var.get()
        is_intruder = class_selected == "Intruder (Human)"

        # Enable/Disable human count and time dropdown
        self.num_humans_menu.configure(state=tk.NORMAL if is_intruder else tk.DISABLED)
        self.time_menu.configure(state=tk.NORMAL if is_intruder else tk.DISABLED)

        # Clear all human attribute sections if not intruder
        if not is_intruder:
            for frame in self.human_attributes_frames.values():
                frame.destroy()
            self.human_attributes.clear()
            self.human_attributes_frames.clear()
 
    def reset_attribute_fields(self):
        self.class_var.set("Select")
        self.time_var.set("Select")
        self.num_humans_var.set("Select")

        # Clear human-specific frames and data
        for frame in self.human_attributes_frames.values():
            frame.destroy()

        self.human_attributes_frames.clear()
        self.human_attributes.clear()

        # Recalculate panel scrollregion
        self.scrollable_attribute_frame.update_idletasks()
        self.attribute_canvas.configure(scrollregion=self.attribute_canvas.bbox("all"))


    def on_canvas_resize(self, event):
            self.show_image()

    def log_error(self, message):
        print(message)
        self.log_output.configure(state='normal')
        self.log_output.insert(tk.END, message + '\n')
        self.log_output.configure(state='disabled')
        self.log_output.yview(tk.END)

    def log_info(self, message):
        print(message)
        self.log_output.configure(state='normal')
        self.log_output.insert(tk.END, message + '\n')
        self.log_output.configure(state='disabled')
        self.log_output.yview(tk.END)

    def on_folder_selected(self, folder_path):
        self.current_folder = folder_path
        self.current_index = 0
        self.sidebar.load(folder_path)
        self.load_images()

        if not self.output_dir or not self.csv_file:
            if not self.setup_file_paths():
                return

        self.show_image()
        self.log_info(f"📂 Opened folder: {folder_path}")

    def load_images(self):
        supported = ['.jpg', '.jpeg', '.png', '.bmp']
        self.image_paths = [
            os.path.join(self.current_folder, f)
            for f in sorted(os.listdir(self.current_folder))
            if any(f.lower().endswith(ext) for ext in supported)
        ]
        if not self.image_paths:
            self.canvas.delete("all")
            self.canvas.create_text(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, text="No images in this folder", fill="white", font=("Arial", 16))
            self.log_info("No images found in this folder.")

    def show_image(self):
        if self.current_index >= len(self.image_paths):
            return

        img_path = self.image_paths[self.current_index]

        if img_path != self.current_image_path:
            try:
                self.original_image = Image.open(img_path).convert("RGB")
                self.current_image_path = img_path
            except Exception as e:
                self.log_error(f"❌ Failed to open image: {img_path} - {e}")
                self.next_image()
                return

        if self.original_image is None:
            return

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        img = self.original_image

        # Calculate scale to fit image to canvas
        scale_w = canvas_width / img.width
        scale_h = canvas_height / img.height
        base_scale = min(scale_w, scale_h)

        # Final scale = base fit * user zoom level
        final_scale = base_scale * self.zoom_level
        new_width = int(img.width * final_scale)
        new_height = int(img.height * final_scale)

        try:
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_img)
        except Exception as e:
            self.log_error(f"🔥 Error resizing image: {e}\n{traceback.format_exc()}")
            self.next_image()
            return

        self.canvas.delete("all")

        x_offset, y_offset = self.image_offset
        self.canvas.create_image(
            canvas_width // 2 + x_offset,
            canvas_height // 2 + y_offset,
            image=self.tk_image
        )

    def ask_overwrite_popup(self, filename):
        popup = tk.Toplevel(self.root)
        popup.title("Already Selected")
        popup.geometry("500x300")  # Adjust width x height as needed
        popup.grab_set()  # Make it modal

        tk.Label(
                popup,
                text=f"The file '{filename}' is already selected.\nDo you want to overwrite it?",
                font=("Arial", 12),
                wraplength=380,
                justify="center",
                padx=20,
                pady=20
            ).pack()

        button_frame = tk.Frame(popup)
        button_frame.pack(pady=10)

        result = {"choice": False}

        def confirm():
            result["choice"] = True
            popup.destroy()

        def cancel():
            popup.destroy()

        tk.Button(button_frame, text="✅ Yes", width=12, command=confirm).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="❌ No", width=12, command=cancel).pack(side=tk.LEFT, padx=10)

        popup.wait_window()
        return result["choice"]


    def select_image(self):
        if not self.image_paths:
            return

        img_path = self.image_paths[self.current_index]
        filename = os.path.basename(img_path)

        if filename in self.selected_images:
            self.log_info(f"⚠️ Skipped (already selected): {filename}")
            if not self.ask_overwrite_popup(filename):
                self.next_image()
                return

        scene_id = self.scene_entry.get().strip()
        if not scene_id or scene_id == "Enter scene ID or leave blank":
            scene_id = os.path.basename(os.path.dirname(img_path))

        try:
            os.makedirs(self.output_dir, exist_ok=True)
            dst_path = os.path.join(self.output_dir, filename)

            if os.path.abspath(img_path) != os.path.abspath(dst_path):
                shutil.copy2(img_path, dst_path)
                self.log_info(f"✅ Saved image: {filename} to {dst_path}")
            else:
                self.log_info(f"⚠️ Skipped copying (same file): {filename}")

            # === Class & Common Fields ===
            class_label = self.class_var.get()
            time = self.time_var.get()

            if class_label == "Empty Frame":
                num_humans = "0"
                human_json_str = "[]"
            else:
                num_humans = self.num_humans_var.get()
                if num_humans == "Select" or not num_humans.isdigit():
                    messagebox.showwarning("Missing Human Count", "⚠️ Please select number of humans.")
                    return

                count = int(num_humans)
                human_list = []

                for i in range(count):
                    attrs = self.human_attributes.get(i)
                    if not attrs:
                        continue

                    action = attrs['action_var'].get()
                    gender = attrs['gender_var'].get()
                    age = attrs['age_var'].get()
                    distance = attrs['distance_var'].get()
                    occlusion = attrs['occlusion_var'].get()
                    accessories = [acc for acc, btn in attrs['accessory_buttons'].items() if btn.cget('relief') == tk.SUNKEN]  # ✅ Add this here

                    # 🧠 Validation
                    if any(val == "Select" for val in [action, gender, age, distance, occlusion]):
                        messagebox.showwarning("Missing Fields", f"⚠️ Fill all attributes for Human {i + 1}")
                        return
                    if not accessories:
                        messagebox.showwarning("Missing Accessories", f"⚠️ Select at least one accessory for Human {i + 1}")
                        return

                    human_data = {
                        "human_id": f"Human {i + 1}",
                        "action": action,
                        "gender": gender,
                        "age": age,
                        "distance": distance,
                        "occlusion": occlusion,
                        "accessories": accessories
                    }
                    human_list.append(human_data)


                # Convert to JSON string
                human_json_str = json.dumps(human_list)

            # === Write to CSV ===
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if os.stat(self.csv_file).st_size == 0:
                    writer.writerow([
                        'filename', 'scene_id', 'class',
                        'num_humans', 'time_of_day',
                        'human_attributes', 'source_path'
                    ])

                writer.writerow([
                    filename, scene_id, class_label,
                    num_humans, time, human_json_str, img_path
                ])

            self.last_selected = {
                "filename": filename,
                "path": dst_path,
                "csv_line": [
                    filename, scene_id, class_label,
                    num_humans, time, human_json_str, img_path
                ]
            }

            self.selected_images.add(filename)
            self.log_info(f"✅ Saved image: {filename} to {dst_path}")
            self.log_info(f"📃 Logged to CSV: {filename}, scene: {scene_id}, humans: {num_humans}")
            self.reset_attribute_fields()
            self.next_image()

        except Exception as e:
            self.log_error(f"Error saving image: {filename} - {e}\n{traceback.format_exc()}")

    def update_attribute_states(self, *args):
        is_empty = self.class_var.get() == "Empty Frame"

        if is_empty:
            # Disable and reset time and human count
            self.time_var.set("Select")
            self.num_humans_var.set("Select")

            self.time_menu.configure(state=tk.DISABLED)
            self.human_menu.configure(state=tk.DISABLED)

            # Remove all dynamic human attribute widgets
            for frame in self.human_attributes_frames.values():
                frame.destroy()
            self.human_attributes_frames.clear()
            self.human_attributes.clear()

            # Update scroll region
            self.scrollable_attribute_frame.update_idletasks()
            self.attribute_canvas.configure(scrollregion=self.attribute_canvas.bbox("all"))

            self.log_info("👤 Class is 'Empty Frame' — cleared all human attributes.")
        else:
            # Enable time and human selection
            self.time_menu.configure(state=tk.NORMAL)
            self.human_menu.configure(state=tk.NORMAL)


    def next_image(self):
        self.zoom_level = 1.0
        self.image_offset = (0, 0)  # <- Correct pan reset
        self.current_index += 1
        if self.current_index < len(self.image_paths):
            self.last_logged_image = ""
            self.reset_attribute_fields()
            self.show_image()
        else:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.canvas.winfo_width() // 2,
                self.canvas.winfo_height() // 2,
                text="All images in this folder reviewed",
                fill="white", font=("Arial", 16)
            )
            self.log_info("🔹 Finished folder. No more images to show.")

    def quit_app(self):
        self.root.quit()

    def toggle_individual_accessory(self, human_data, accessory):
        btn = human_data["buttons"][accessory]
        acc_set = human_data["accessories"]

        if accessory in acc_set:
            acc_set.remove(accessory)
            btn.config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")
        else:
            # Exclusive handling for 'None' and 'Unidentified'
            if accessory in ["None", "Unidentified"]:
                for other in acc_set.copy():
                    acc_set.remove(other)
                    human_data["buttons"][other].config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")
                acc_set.add(accessory)
                btn.config(relief="sunken", bg=self.accessory_btn_selected_color, fg="white")
            else:
                # Deselect exclusive options
                for exclusive in ["None", "Unidentified"]:
                    if exclusive in acc_set:
                        acc_set.remove(exclusive)
                        human_data["buttons"][exclusive].config(relief="raised", bg=self.accessory_btn_normal_color, fg="black")

                acc_set.add(accessory)
                btn.config(relief="sunken", bg=self.accessory_btn_selected_color, fg="white")

            
    def undo_last_selection(self):
        if not hasattr(self, 'last_selected') or not self.last_selected:
            self.log_info("⚠️ Nothing to undo.")
            return

        filename = self.last_selected["filename"]
        path = self.last_selected["path"]
        line_to_remove = self.last_selected["csv_line"]

        # Remove from CSV
        if os.path.exists(self.csv_file):
            with open(self.csv_file, 'r') as f:
                rows = list(csv.reader(f))
            rows = [r for r in rows if r != line_to_remove]
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(rows)

        # Remove image file
        if os.path.exists(path):
            os.remove(path)

        # Update internal state
        if filename in self.selected_images:
            self.selected_images.remove(filename)

        self.last_selected = None
        self.log_info(f"⏪ Undid selection: {filename}")
        self.reset_attribute_fields()



    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.theme_toggle_btn.config(text="☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")


    def apply_theme(self):
        if not hasattr(self, 'canvas') or not self.canvas:
            return

        if self.dark_mode:
            bg = "#2d3e30"           # Olive green dark base
            fg = "white"
            btn_bg = "#3f513e"
            entry_bg = "#384d3b"
            highlight = "#6d8f6c"
            canvas_color = "#1f2b20"
            log_color = "#1f2b20"
            sidebar_bg = bg
            entry_fg = "white"
            log_fg = "white"
            listbox_fg = "white"
        else:
            bg = "white"
            fg = "black"
            btn_bg = "#f0f0f0"
            entry_bg = "white"
            highlight = "#cccccc"
            canvas_color = "#000000"
            log_color = "#1e1e1e"
            sidebar_bg = "#f2f2f2"
            entry_fg = "black"
            log_fg = "white"
            listbox_fg = "black"

        # Root + Sidebar
        self.root.configure(bg=bg)
        self.sidebar.frame.configure(bg=sidebar_bg)
        self.sidebar.listbox.configure(
            bg=entry_bg, fg=listbox_fg,
            highlightbackground=highlight, selectbackground=highlight
        )

        # Top bar + buttons
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=bg)
                for sub in widget.winfo_children():
                    if isinstance(sub, tk.Button):
                        sub.configure(bg=btn_bg, fg=fg, activebackground=highlight)

        # Canvas background
        self.canvas.configure(bg=canvas_color)

        # ✨ Attribute panel itself
        self.attribute_frame.configure(
            bg=bg,
            fg=fg,
            highlightbackground=highlight,
            highlightcolor=highlight,
            bd=2,
            relief=tk.GROOVE
        )

        # ✨ Theme all children inside the attribute panel
        for child in self.attribute_frame.winfo_children():
            if isinstance(child, (tk.Label, tk.Checkbutton)):
                child.configure(bg=bg, fg=fg)
            elif isinstance(child, tk.OptionMenu):
                child.configure(bg=btn_bg, fg=fg, highlightbackground=highlight)
                child["menu"].configure(bg=btn_bg, fg=fg)
            elif isinstance(child, tk.Listbox):
                child.configure(
                    bg=entry_bg,
                    fg=fg,
                    highlightbackground=highlight,
                    selectbackground=highlight,
                    selectforeground=fg
                )


        # Entry and buttons
        self.scene_entry.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
        self.select_btn.configure(bg=btn_bg, fg=fg)
        self.next_btn.configure(bg=btn_bg, fg=fg)
        self.quit_btn.configure(bg=btn_bg, fg=fg)
        self.undo_btn.configure(bg=btn_bg, fg=fg)

        # Log panel
        self.log_frame.configure(bg=bg)
        self.log_output.configure(bg=log_color, fg=log_fg, insertbackground=log_fg)

        # Control panel
        if hasattr(self, 'control_frame'):
            self.control_frame.configure(bg=bg)

        # Hover effects
        hover_btn_bg = "#2c3b2c" if self.dark_mode else "#d9d9d9"
        for btn in [
            self.select_btn, self.next_btn, self.quit_btn, self.undo_btn, self.theme_toggle_btn
        ]:
            self.apply_hover_effects(btn, btn_bg, hover_btn_bg)

        if self.dark_mode:
            self.accessory_btn_normal_color = "#3f513e"   # dark olive for normal
            self.accessory_btn_selected_color = "#888888" # even darker for selected
        else:
            self.accessory_btn_normal_color = "#f0f0f0"   # light gray for normal
            self.accessory_btn_selected_color = "#555555"

        for btn in self.accessory_buttons.values():
            is_selected = btn.cget("relief") == tk.SUNKEN
            btn.configure(
                bg=self.accessory_btn_selected_color if is_selected else self.accessory_btn_normal_color,
                fg="white" if self.dark_mode or is_selected else "black"
            )

    def apply_hover_effects(self, widget, normal_bg, hover_bg):
        widget.configure(bg=normal_bg)
        widget.bind("<Enter>", lambda e: widget.configure(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.configure(bg=normal_bg))


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSelectorGUI(root)
    root.mainloop()
