import os
import io 
import tkinter as tk
from graphviz import Digraph
from PIL import Image, ImageTk, ImageDraw, ImageOps
from tkinter import scrolledtext, ttk, messagebox, Menu, filedialog

from scanner import tokenize
from parser import TokenStream, parse_program, SyntaxTreeNode 
from visualizer import TreeVisualizer

class CodeEditorApp:
    def __init__(self, root):
        """Initialize the VS Code-like code editor application."""
        self.root = root
        self.root.title("TINY Language Editor")
        self.root.geometry("1000x700")
        self.current_theme = "light"
        self.current_dot_object = None 
        self.original_pil_image = None
        self.tree_image_photo = None 

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.app_container = ttk.Frame(root)
        self.app_container.grid(row=0, column=0, sticky="nsew")
        self.app_container.columnconfigure(0, weight=1)
        self.app_container.rowconfigure(0, weight=1)

        self.editor_view_frame = ttk.Frame(self.app_container)
        self.editor_view_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.editor_view_frame.columnconfigure(0, weight=1)
        self.editor_view_frame.rowconfigure(0, weight=1)  
        self.editor_view_frame.rowconfigure(1, weight=0)  
        self.editor_view_frame.rowconfigure(2, weight=1)  

        self.tree_view_frame = ttk.Frame(self.app_container)
        self.tree_view_frame.columnconfigure(0, weight=1)
        self.tree_view_frame.rowconfigure(1, weight=1) 

        self.create_menu()
        self.setup_editor_view_widgets()
        self.setup_tree_view_widgets()
        self.create_editor_context_menu()

        self.apply_theme() 
        
        self.show_editor_view() 
        self.root.protocol("WM_DELETE_WINDOW", self.on_close) 

    def setup_editor_view_widgets(self):
        """Create widgets for the editor view."""
        self.create_code_editor(self.editor_view_frame)
        self.create_bottom_panel(self.editor_view_frame)
        self.create_output_area(self.editor_view_frame)

    def setup_tree_view_widgets(self):
        """Create widgets for the tree view."""
        tree_view_buttons_panel = ttk.Frame(self.tree_view_frame)
        tree_view_buttons_panel.grid(row=0, column=0, sticky="ew", pady=(10,5))

        self.return_to_editor_btn = ttk.Button(
            tree_view_buttons_panel,
            text="Return to Editor",
            command=self.show_editor_view
        )
        self.return_to_editor_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.export_menu_btn = ttk.Menubutton(tree_view_buttons_panel, text="Export Tree")
        export_menu = Menu(self.export_menu_btn, tearoff=0)
        export_menu.add_command(label="Export as PNG", command=self.export_tree_as_png)
        export_menu.add_command(label="Export as PDF", command=self.export_tree_as_pdf)
        self.export_menu_btn.config(menu=export_menu)
        self.export_menu_btn.pack(side=tk.LEFT, padx=(0,10))

        self.tree_image_container_frame = ttk.Frame(self.tree_view_frame, relief=tk.SUNKEN, borderwidth=1)
        self.tree_image_container_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.tree_image_container_frame.columnconfigure(0, weight=1)
        self.tree_image_container_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.tree_image_container_frame, highlightthickness=0) 
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
    def show_editor_view(self):
        """Show the editor view and hide the tree view."""
        self.tree_view_frame.grid_remove()
        self.editor_view_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.root.title("TINY Language Editor - Editor")

        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.delete("all")
        self.tree_image_photo = None
        self.original_pil_image = None


    def show_tree_view(self):
        """Show the tree view and hide the editor view."""
        if not self.current_dot_object:
            messagebox.showinfo("No Tree", "No parse tree has been generated yet.")
            return

        try:
            png_data = self.current_dot_object.pipe(format='png') 
            if not png_data:
                messagebox.showerror("Tree Display Error", "Graphviz returned empty PNG data.")
                self.update_output("Error: Graphviz returned empty PNG data.", clear=False)
                return

            self.editor_view_frame.grid_remove()
            self.tree_view_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            self.root.title("TINY Language Editor - Parse Tree View")
            
            self.original_pil_image = Image.open(io.BytesIO(png_data))
            self.original_pil_image = ImageOps.expand(self.original_pil_image, border=10, fill='white') # Added line
            
            self.root.update_idletasks() 
            self._resize_and_display_tree_image()

        except Exception as e:
            messagebox.showerror("Tree Display Error", f"Could not generate or display parse tree image: {e}")
            self.update_output(f"Error generating/displaying tree: {e}", clear=False)
            self.original_pil_image = None 
            self.show_editor_view()

    def _on_canvas_configure(self, event):
        """Handle canvas resize events by rescaling and redrawing the image."""
        if self.original_pil_image and self.tree_view_frame.winfo_ismapped():
            if event.width > 1 and event.height > 1:
                 self._resize_and_display_tree_image()

    def _resize_and_display_tree_image(self):
        """Resizes the stored original PIL image to fit the canvas, preserving aspect ratio, and displays it."""
        if not self.original_pil_image:
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.delete("all")
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        img_width, img_height = self.original_pil_image.size

        if img_width == 0 or img_height == 0: 
            return

        width_scale = canvas_width / img_width
        height_scale = canvas_height / img_height
        scale = min(width_scale, height_scale)

        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        if new_width < 1 or new_height < 1: 
            return 

        try:
            resized_image = self.original_pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except AttributeError:
             resized_image = self.original_pil_image.resize((new_width, new_height), Image.LANCZOS)

        self.tree_image_photo = ImageTk.PhotoImage(resized_image)
        
        self.canvas.delete("all")

        x_pos = (canvas_width - new_width) // 2
        y_pos = (canvas_height - new_height) // 2
        
        self.canvas.create_image(x_pos, y_pos, anchor=tk.NW, image=self.tree_image_photo)


    def on_close(self):
        """Handle application closing, ensuring memory is freed."""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.delete("all")
        self.tree_image_photo = None
        self.original_pil_image = None 
        self.current_dot_object = None
        self.root.destroy()

    def create_menu(self):
        """Create the application menu with a theme toggle."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        theme_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=theme_menu)
        theme_menu.add_command(label="Toggle Light/Dark Mode", command=self.toggle_theme)

    def apply_theme(self):
        """Apply the current theme (light or dark) to the UI elements."""
        style = ttk.Style()
        if self.current_theme == "light":
            bg_color = "#ffffff"
            text_color = "#000000"
            editor_bg = "#ffffff" 
            editor_fg = "#000000"
            button_bg = "#f0f0f0"
            button_fg = "#000000"
            button_active_bg = "#e0e0e0"
            output_bg = "#f8f8f8"
            output_fg = "#333333"
            insert_bg = "black"
            select_bg = "#add6ff" 
            tree_frame_bg = "#eeeeee" 

            self.root.configure(bg=bg_color)
            style.configure("TFrame", background=bg_color)
            style.configure("TreeContainer.TFrame", background=tree_frame_bg)
            style.configure("TButton", background=button_bg, foreground=button_fg, font=("Consolas", 10), borderwidth=1, focusthickness=0, focuscolor=button_bg)
            style.map("TButton", background=[("active", button_active_bg), ("pressed", button_active_bg)], foreground=[("active", button_fg), ("pressed", button_fg)]) 
            style.configure("TLabel", background=bg_color, foreground=text_color)
            style.configure("TMenubutton", background=button_bg, foreground=button_fg, font=("Consolas", 10), arrowcolor=text_color, borderwidth=1)
            style.map("TMenubutton", background=[("active", button_active_bg)], foreground=[("active", button_fg)])

        else: 
            bg_color = "#1e1e1e"
            text_color = "#d4d4d4"
            editor_bg = "#1e1e1e" 
            editor_fg = text_color 
            button_bg = "#3c3c3c"
            button_fg = "#000000"
            button_active_bg = "#505050"
            output_bg = "#2d2d2d"
            output_fg = "#cccccc"
            insert_bg = "white"
            select_bg = "#264f78"
            tree_frame_bg = "#2a2a2a"

            self.root.configure(bg=bg_color)
            style.configure("TFrame", background=bg_color)
            style.configure("TreeContainer.TFrame", background=tree_frame_bg)
            style.configure("TButton", background=button_bg, foreground=button_fg, font=("Consolas", 10), borderwidth=1, focusthickness=0, focuscolor=button_bg)
            style.map("TButton", background=[("active", button_active_bg), ("pressed", button_active_bg)], foreground=[("active", button_fg), ("pressed", button_fg), ("disabled", "#7f7f7f")])
            style.configure("TLabel", background=bg_color, foreground=text_color)
            style.configure("TMenubutton", background="#ffffff", foreground="#000000", font=("Consolas", 10), arrowcolor="#000000", borderwidth=1)
            style.map("TMenubutton", background=[("active", "#cccccc")], foreground=[("active", "#000000")])

        self.app_container.configure(style="TFrame") 

        if hasattr(self, 'code_editor'):
            self.code_editor.config(bg=editor_bg, fg=editor_fg, insertbackground=insert_bg, selectbackground=select_bg)
        if hasattr(self, 'output_area'):
            self.output_area.config(bg=output_bg, fg=output_fg)
        if hasattr(self, 'output_label'): 
            self.output_label.config(background=bg_color, foreground=text_color)
        
        if hasattr(self, 'tree_image_container_frame'):
            self.tree_image_container_frame.config(style="TreeContainer.TFrame") 
        
        if hasattr(self, 'canvas'): 
            canvas_actual_bg = editor_bg 
            self.canvas.config(bg=canvas_actual_bg)

        if hasattr(self, 'return_to_editor_btn'):
            self.return_to_editor_btn.config(style="TButton")
        if hasattr(self, 'export_menu_btn'):
            self.export_menu_btn.config(style="TMenubutton")


    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.apply_theme()

    def create_editor_context_menu(self):
        """Create a context menu for the code editor."""
        self.editor_context_menu = Menu(self.root, tearoff=0)
        self.editor_context_menu.add_command(label="Cut", command=lambda: self.code_editor.event_generate("<<Cut>>"))
        self.editor_context_menu.add_command(label="Copy", command=lambda: self.code_editor.event_generate("<<Copy>>"))
        self.editor_context_menu.add_command(label="Paste", command=lambda: self.code_editor.event_generate("<<Paste>>"))

    def show_editor_context_menu(self, event):
        """Display the editor context menu at the cursor position."""
        try:
            self.editor_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.editor_context_menu.grab_release()

    def create_code_editor(self, parent_frame):
        """Create the main code editing area within the given parent frame."""
        editor_frame = ttk.Frame(parent_frame) 
        editor_frame.grid(row=0, column=0, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)

        self.code_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            width=80,
            height=20, 
            padx=10,
            pady=10,
            font=("Consolas", 12), 
            relief=tk.SOLID,
            borderwidth=1
        )

        self.code_editor.grid(row=0, column=0, sticky="nsew")
        self.code_editor.bind("<Button-3>", self.show_editor_context_menu) # Add this line

    def create_bottom_panel(self, parent_frame):
        """Create the bottom panel with action buttons within the given parent frame."""
        bottom_panel = ttk.Frame(parent_frame) 
        bottom_panel.grid(row=1, column=0, sticky="ew", pady=(10, 10))

        self.erase_btn = ttk.Button(
            bottom_panel,
            text="Erase",
            command=self.erase_content
        )
        self.erase_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.parse_btn = ttk.Button(
            bottom_panel,
            text="Parse",
            command=self.parse_code
        )
        self.parse_btn.pack(side=tk.LEFT)


    def create_output_area(self, parent_frame):
        """Create an output area to show parsing results within the given parent frame."""
        output_frame = ttk.Frame(parent_frame) 
        output_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1) 

        self.output_label = ttk.Label(output_frame, text="Output:") 
        self.output_label.grid(row=0, column=0, sticky="w", pady=(0,5))

        self.output_area = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            width=80,
            height=10, 
            padx=10,
            pady=10,
            font=("Consolas", 11),
            relief=tk.SOLID,
            borderwidth=1
        )
        self.output_area.grid(row=1, column=0, sticky="nsew")
        self.output_area.config(state=tk.DISABLED)

    def erase_content(self):
        """Clear the content of the code editor."""
        self.code_editor.delete(1.0, tk.END)
        self.update_output("Editor content cleared.")

    def update_output(self, text, clear=True):
        """Update the output area with the given text."""
        self.output_area.config(state=tk.NORMAL)
        if clear:
            self.output_area.delete(1.0, tk.END)
        self.output_area.insert(tk.END, str(text) + "\n")
        self.output_area.config(state=tk.DISABLED)
        self.output_area.see(tk.END) 

    def parse_code(self):
        """Run the scanner and parser on the code in the editor."""
        code = self.code_editor.get(1.0, tk.END).strip()
        if not code:
            messagebox.showwarning("Empty Code", "Please enter some code to parse.")
            return

        self.update_output("Starting scanning and parsing process...") 
        self.root.update_idletasks()

        try:
            self.update_output("\nScanning code...", clear=False)
            self.root.update_idletasks() 
            tokens = tokenize(code)
            if not tokens:
                self.update_output("No tokens found or scanner error.", clear=False)
                self.root.update_idletasks() 
                return
            
            self.update_output(f"Scanning complete. Found {len(tokens)} tokens.", clear=False)
            self.root.update_idletasks() 
            self.update_output("List of tokens:", clear=False)
            for value, token_type in tokens:
                self.update_output(f"  {value} : {token_type}", clear=False)
            self.root.update_idletasks() 

            self.update_output("\nParsing tokens...", clear=False)
            self.root.update_idletasks() 
            token_stream = TokenStream(tokens)
            parse_tree_root = parse_program(token_stream)
            self.update_output("Parsing complete.", clear=False)
            self.root.update_idletasks() 
            
            visualizer = TreeVisualizer() 
            self.current_dot_object = visualizer.render_tree(parse_tree_root) 
            
            if self.current_dot_object:
                self.update_output("\\nParse tree generated. Switching to tree view...", clear=False)
                self.root.update_idletasks() 
                
                self.code_editor.delete(1.0, tk.END)
                self.output_area.config(state=tk.NORMAL)
                self.output_area.delete(1.0, tk.END)
                self.output_area.config(state=tk.DISABLED)
                
                self.show_tree_view()
            else:
                self.update_output("\nCould not generate parse tree graph.", clear=False)
                self.root.update_idletasks() 
                messagebox.showerror("Parse Tree Error", "Failed to generate the parse tree graph.")

        except RuntimeError as e:
            self.update_output(f"\nScanner Error: {e}", clear=False)
            self.root.update_idletasks() 
            messagebox.showerror("Scanner Error", str(e))
            self.current_dot_object = None
        except SyntaxError as e:
            self.update_output(f"\nParser Error: {e}", clear=False)
            self.root.update_idletasks() 
            messagebox.showerror("Parser Error", str(e))
            self.current_dot_object = None 
        except Exception as e:
            self.update_output(f"\nAn unexpected error occurred: {e}", clear=False)
            self.root.update_idletasks() 
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.current_dot_object = None

    def export_tree_as_png(self):
        """Export the current parse tree as a PNG file."""
        if not self.current_dot_object:
            messagebox.showinfo("Export Error", "No parse tree available to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Parse Tree as PNG"
        )
        if not filepath:
            return
            
        try:
            self.current_dot_object.render(filepath[:-4], format="png", cleanup=True) 
            messagebox.showinfo("Export Successful", f"Parse tree saved as {filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export as PNG: {e}")

    def export_tree_as_pdf(self):
        """Export the current parse tree as a PDF file."""
        if not self.current_dot_object:
            messagebox.showinfo("Export Error", "No parse tree available to export.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Parse Tree as PDF"
        )
        if not filepath:
            return 
            
        try:
            self.current_dot_object.render(filepath[:-4], format="pdf", cleanup=True) 
            messagebox.showinfo("Export Successful", f"Parse tree saved as {filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export as PDF: {e}")

def main():
    """Main function to start the application."""
    root = tk.Tk()
    app = CodeEditorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()