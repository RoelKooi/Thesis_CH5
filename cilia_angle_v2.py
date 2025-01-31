# -*- coding: utf-8 -*-
"""
Created on Mon Oct  4 10:26:15 2021

@author: RoelKooi
"""

import os
import cv2
import csv
import PIL.Image, PIL.ImageTk
import numpy as np
import matplotlib.pyplot as plt
import tkinter
import tkinter.filedialog as fd
import screeninfo

pixel_per_um_20x = 1.75

def main():
    session = MovementTracker()
    session.mainloop()
    # root = tkinter.Tk()
    # root.wm_withdraw()
    # location = r"C:\Users\20201634\OneDrive - TU Eindhoven\Microscopy\Olympus"
    
    
    # folder = fd.askdirectory()
    # for filename in os.listdir(folder):
    #     if filename.endswith(".jpg"):
    #         print(filename)
            
            # img = cv2.imread(folder + "/" + filename)
            # thres, binary = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
            # plt.imshow(binary)
            # img_copy, contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            # cv2.drawContours(img_copy, contours, -1, (255,0,0), thickness=2)
            # plt.imshow(img_copy)
    # thres, binary = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)
    # plt.imshow(binary)
    # img_copy, contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # cv2.drawContours(img_copy, contours, -1, (255,0,0), thickness=2)
    # plt.imshow(img_copy)
    return

class MovementTracker(tkinter.Tk):
    def __init__(self, **options):
        super().__init__(**options)
        
        
        # Some instance variables
        sinfo = screeninfo.get_monitors()[0]
        self.max_height = sinfo.height - 150 # Maximum height of the video frame
        self.max_width = sinfo.width - 100   # Maximum width of the video frame
        self.count_return = 0
        self.image_off = None
        self.image_on = None
        self.tracing = 0
        self.x_start = None
        self.y_start = None
        self.x_end = None
        self.y_end = None
        self.trace_line = None
        self.trace_line_dupe = None
        self.crosshare = None
        self.cursor_dupe = None
        self.img_h = 0
        self.img_w = 0
        self.k = None
        self.var_add_results = tkinter.IntVar()
        self.var_add_results.set(0)
        self.lines = [] # Elements should be structure as tuplets (x1, y1, x2, y2)
        self.last_10 = [] # List of actions that can be erased
        self.line_ids = [] # The line object IDs referenced by tkinter
        self.var_cur_img = tkinter.StringVar()
        self.var_cur_img.set("")
        self.var_n_results = tkinter.StringVar()
        self.var_n_results.set(str(len(self.lines)))
        self.initialdir = r"C:\Users\20201634\OneDrive - TU Eindhoven"
        
        # Establish hotkey commands
        self.bind("<Return>", self._returnCallback)
        self.bind("<Control-z>", self._undo)
        self.bind("<Control-e>", self._exportData)
        
        # Create widget layout
        self.createWidgets()
        
        return
        
    def createWidgets(self):
        # Two images on a Canvas
        self.image_canvas = tkinter.Canvas(self, background='black')
                                           # height=1000, width=1500)
        self.image_canvas.grid(row=0, column=0, sticky='nsew', columnspan=2)
        
        # Control buttons
        frame_btns = tkinter.Frame(self)
        
        btn_start = tkinter.Button(frame_btns,
                                   text="Start",
                                   command=self._startTrackInput
                                   )
        
        btn_stop = tkinter.Button(frame_btns,
                                  text="Stop",
                                  command=self._stopTrackInput
                                  )
        
        btn_clear = tkinter.Button(frame_btns,
                                   text="Clear selections",
                                   command=self._clearSelections)
        
        btn_export = tkinter.Button(frame_btns,
                                    text="Export",
                                    command=self._exportData
                                    )
        
        btn_load_images = tkinter.Button(frame_btns,
                                         text="Load Images",
                                         command=self._loadImages
                                         )
        
        checkbox_addresult = tkinter.Checkbutton(frame_btns,
                                                 text="Add results",
                                                 var=self.var_add_results)
        
        frame_btns.grid(row=1, column=0, sticky='nsew')
        btn_start.grid(row=0, column=0, sticky='nsew')
        btn_stop.grid(row=0, column=1, sticky='nsew')
        btn_clear.grid(row=0, column=2, sticky='nsew')
        btn_load_images.grid(row=1, column=0, sticky='nsew')
        btn_export.grid(row=1, column=1, sticky='nsew')
        checkbox_addresult.grid(row=1, column=2, sticky='w')
        
        # Metrics feedback
        frame_metrics = tkinter.Frame(self)
        lbl_n_lines = tkinter.Label(frame_metrics,
                                    text="Nr. of current lines:")
        txt_n_lines = tkinter.Label(frame_metrics,
                                    textvariable=self.var_n_results)
        lbl_cur_img = tkinter.Label(frame_metrics,
                                   text="Current image:")
        txt_cur_img = tkinter.Label(frame_metrics,
                                    textvariable=self.var_cur_img)
        
        frame_metrics.grid(row=1, column=1, sticky='nsew')
        lbl_n_lines.grid(row=0, column=0, sticky='nw')
        txt_n_lines.grid(row=0, column=1, sticky='nw')
        lbl_cur_img.grid(row=1, column=0, sticky='nw')
        txt_cur_img.grid(row=1, column=1, sticky='nw')
        
        return
    
    def _returnCallback(self, event):
        if self.count_return == 0:
            self.count_return = 1
            self._startTrackInput()
        else:
            self.count_return = 0
            self._stopTrackInput()
            
        return
    
    def _undo(self, event):
        # self.last_10 have entries of (line, line) structure
        if len(self.last_10) > 0:            
            print("Undo")
            entry = self.last_10.pop(-1)
            self.line_ids.remove(entry)
            self.image_canvas.delete(entry[0])
            self.image_canvas.delete(entry[1])
            self.lines.pop(-1)
            self.var_n_results.set(str(len(self.lines)))
        else:
            print("Nothing left")
        return
    
    def _startTrackInput(self):
        print("Started tracking input")
        self.image_canvas.bind("<Button-1>", self._toggleMotionTrace)
        self.image_canvas.bind("<Motion>", self._dupe_cursor)
        return
    
    def _toggleMotionTrace(self, event):
        if self.tracing:
            self.tracing = 0
            self.unbind("<Motion>")
            self.bind("<Motion>", self._dupe_cursor)
            if not None in (self.x_start, self.y_start, self.x_end, self.y_end):
                # Add the coordinates of the line to the list
                self.lines.append((int(self.x_start / self.k),
                                   int(self.y_start / self.k),
                                   int(self.x_end / self.k),
                                   int(self.y_end / self.k),
                                   self.var_cur_img.get()
                                   ))
                self.var_n_results.set(str(len(self.lines)))
                # Erase the temp traced line and create a permanent one
                self.image_canvas.delete(self.trace_line)
                self.image_canvas.delete(self.trace_line_dupe)
                self.image_canvas.delete(self.crosshare)
                self.trace_line = None
                self.trace_line_dupe = None
                self.crosshare = None
                if self.x_end == self.x_start and self.y_end == self.y_start:
                    self.y_end += 1
                left = self.image_canvas.create_line(self.x_start, self.y_start,
                                                     self.x_end, self.y_end,
                                                     fill='light blue',
                                                     width=2)
                right = self.image_canvas.create_line(self.x_start + self.img_w, self.y_start,
                                                      self.x_end + self.img_w, self.y_end,
                                                      fill='light blue',
                                                      width=2)
                # Store action in undo list
                self.last_10.append((left, right))
                self.line_ids.append((left, right))
                # Clean the list if too long
                if len(self.last_10) > 10:
                    self.last_10.pop(0)
            
            self.x_start = None
            self.y_start = None
            self.x_end = None
            self.y_end = None
            # print("Stopped tracing")
        else:
            self.tracing = 1
            self.x_start = event.x
            self.y_start = event.y
            self.x_end = event.x
            self.y_end = event.y
            self.crosshare = drawCrosshare(self.image_canvas,
                                           event.x + self.img_w, event.y)
            self.unbind("<Motion>")
            self.bind("<Motion>", self._drawMotionTrace)
            
            # print("Started tracing")
        return
    
    def _drawMotionTrace(self, event):
        self.image_canvas.delete(self.crosshare)
        if self.trace_line:
            self.image_canvas.delete(self.trace_line)
            self.image_canvas.delete(self.trace_line_dupe)            
        
        self.trace_line = self.image_canvas.create_line(self.x_start, self.y_start, event.x, event.y, fill='red')
        self.trace_line_dupe = self.image_canvas.create_line(
            self.x_start + self.img_w, self.y_start, event.x + self.img_w, event.y, fill='red')
        self.crosshare = drawCrosshare(self.image_canvas, event.x + self.img_w, event.y)
        
        self.x_end = event.x
        self.y_end = event.y
        return
    
    def _dupe_cursor(self, event):
        if self.cursor_dupe:
            self.image_canvas.delete(self.cursor_dupe)
        self.cursor_dupe = drawDotCursor(self.image_canvas, event.x + self.img_w, event.y)
        return
    
    def _stopTrackInput(self):
        print("Stopped tracking input")
        self.image_canvas.unbind("<Button-1>")
        self.image_canvas.unbind("<Motion>")
        self.image_canvas.delete(self.trace_line)
        self.image_canvas.delete(self.trace_line_dupe)
        self.image_canvas.delete(self.crosshare)
        self.trace_line = None
        self.trace_line_dupe = None
        self.crosshare = None
        self.tracing = 0
        return
    
    def _clearSelections(self):
        if self.tracing:
            self._stopTrackInput()
        self.last_10 = []
        for line in self.line_ids:
            self.image_canvas.delete(line[0])
            self.image_canvas.delete(line[1])
        self.lines = []
        self.var_n_results.set("0")
        print("Cleared all selections")
        return
    
    def _loadImages(self):
        print("Loading images")
        # Open file selection dialog
        file_1 = fd.askopenfilename(title="Choose either the 'on' or 'off' image",
                                    initialdir=self.initialdir,
                                    filetypes=(("jpeg", "*.jpg"), ("tiff", "*.tiff"))
                                    )
        
        if not file_1:
            return
        
        file_name, ext = file_1.split(".")
        folder = os.path.dirname(file_1)
        print("Setting default directory:" + folder)
        self.initialdir = folder
        self.var_cur_img.set(os.path.split(file_name)[1].split(" -")[0])
        
        # Find the corresponding on/off image
        if file_name.lower().endswith("on"):
            print("Found 'on' file")
            
            check = file_name[:-2] + "off." + ext
            if os.path.isfile(check):
                print("Found 'off' file")
                img_on = cv2.imread(file_1)
                img_off = cv2.imread(check)
            else:
                tkinter.messagebox.showerror(title="Error",
                                             message="No corresponding 'off' file found"
                                             )
                        
        elif file_name.lower().endswith("off"):
            print("Found 'off' file")
            check = file_name[:-3] + "on." + ext
            if os.path.isfile(check):
                print("Found 'on' file")
                img_on = cv2.imread(check)
                img_off = cv2.imread(file_1)
            else:
                
                tkinter.messagebox.showerror(title="Error",
                                             message="No corresponding 'on' file found"
                                             )
        else:
            tkinter.messagebox.showerror(title="Error",
                                         message="Invalid file name! Should end with 'on' or 'off'"
                                         )
        
        # Put the images on the canvas
        # Clear possible previous images
        self.image_canvas.delete("all")
        if not self.var_add_results.get():
            self.lines = []
            self.line_ids = []
            self.last_10 = []
            self.var_n_results.set("0")
            print("Cleared results")
        # Get the image dimensions to fit them side by side
        img_off_h, img_off_w, img_off_channels = img_off.shape
        img_on_h, img_on_w, img_on_channels = img_on.shape
        kw = 0.5 * self.max_width / img_off_w
        kh = self.max_height / img_off_h
        self.k = min(kw, kh)
        self.img_w = int(self.k*img_off_w)
        self.img_h = int(self.k*img_off_h)
        
        self.image_off = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img_off).resize((
            self.img_w, self.img_h)))
        self.image_on = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img_on).resize((
            self.img_w, self.img_h)))
        
        
        self.image_canvas.config(width=2*self.img_w, height=self.img_h)
        
        self.image_canvas.create_image(0, 0, image=self.image_off, anchor=tkinter.NW)
        self.image_canvas.create_image(self.img_w, 0, image=self.image_on, anchor=tkinter.NW)
        
        
        self.image_canvas.update()
        return
    
    def _exportData(self, *event):
        print("Exporting data")
        popup = SaveWindow(self, folder=self.initialdir, data=self.lines)
        self.wait_window(popup)
        return
    
    def _drawTempLine(self, event):
        return


class SaveWindow(tkinter.Toplevel):
    def __init__(self, parent, folder=None, data=[]):
        super().__init__(parent, takefocus=True)
        self.title("Save Data")
        
        # Instance variables
        self.data = data
        self.w_pady = 5
        self.outfile = None
        self.var_folder = tkinter.StringVar()
        self.var_folder.set(folder)
        self.var_len = tkinter.StringVar()
        self.var_dia = tkinter.StringVar()
        self.var_pitch = tkinter.StringVar()
        self.var_medium = tkinter.StringVar()
        self.var_scale = tkinter.StringVar()
        self.var_scale.set(pixel_per_um_20x)
        
        self.createWidgets()
        
    def createWidgets(self):
        # Choosing a folder
        frame_folder = tkinter.Frame(self)
        
        lbl_folder = tkinter.Label(frame_folder,
                                   text="Location:")
        
        txt_cur_sel = tkinter.Label(frame_folder,
                                    wraplength=300,
                                    textvariable=self.var_folder)
        
        btn_browse = tkinter.Button(frame_folder,
                                    text="Browse",
                                    command=self._browse)
        
        btn_save = tkinter.Button(frame_folder,
                                  text="Save",
                                  command=self._save
                                  )
        
        frame_folder.grid(row=0, column=0, sticky='nsew',
                          columnspan=2, rowspan=1)
        lbl_folder.grid(row=0, column=0, sticky='nsew')
        txt_cur_sel.grid(row=0, column=1, sticky='nsew')
        btn_browse.grid(row=0, column=2, sticky='ew')
        btn_save.grid(row=1, column=0, sticky='nsew', pady=self.w_pady)
        
        # Setting cilia parameters
        frame_settings = tkinter.LabelFrame(self, text="Experiment Parameters")
        
        lbl_len = tkinter.Label(frame_settings,
                                text=u"Cilia length (\u03bcm):",
                                anchor='w')
        
        ntr_len = tkinter.Entry(frame_settings,
                                textvariable=self.var_len)
        
        lbl_dia = tkinter.Label(frame_settings,
                                text=u"Cilia diameter (\u03bcm):",
                                anchor='w')
        
        ntr_dia = tkinter.Entry(frame_settings,
                                textvariable=self.var_dia)
        
        lbl_pitch = tkinter.Label(frame_settings,
                                  text=u"Density (cm\u207B\u00b2):",
                                  anchor='w')
        
        ntr_pitch = tkinter.Entry(frame_settings,
                                  textvariable=self.var_pitch)
        
        lbl_medium = tkinter.Label(frame_settings,
                                   text="Medium:",
                                   anchor='w')
        
        ntr_medium = tkinter.Entry(frame_settings,
                                   textvariable=self.var_medium)
        
        lbl_scale = tkinter.Label(frame_settings,
                                  text="Scale [pxl/um]",
                                  anchor='w')
        
        ntr_scale = tkinter.Label(frame_settings,
                                  textvariable=self.var_scale)
        
        frame_settings.grid(row=1, column=0, sticky='nsew', pady=10)
        
        lbl_len.grid(row=0, column=0, sticky='nsew', pady=self.w_pady)
        ntr_len.grid(row=0, column=1, sticky='nsew', pady=self.w_pady)
        lbl_dia.grid(row=1, column=0, sticky='nsew', pady=self.w_pady)
        ntr_dia.grid(row=1, column=1, sticky='nsew', pady=self.w_pady)
        lbl_pitch.grid(row=2, column=0, sticky='nsew', pady=self.w_pady)
        ntr_pitch.grid(row=2, column=1, sticky='nsew', pady=self.w_pady)
        lbl_medium.grid(row=3, column=0, sticky='nsew', pady=self.w_pady)
        ntr_medium.grid(row=3, column=1, sticky='nsew', pady=self.w_pady)
        lbl_scale.grid(row=4, column=0, sticky='nsew', pady=self.w_pady)
        ntr_scale.grid(row=4, column=1, sticky='nsew', pady=self.w_pady)
        
        return
    
    def _browse(self):
        # Create default file name from cilia parameters
        temp = "Analysis_L{length}um_dia{dia}um_density{pitch}_{medium}.csv"
        # initfilename = temp.format(
        #     length=self.var_len.get(),
        #     dia=self.var_dia.get(),
        #     pitch=self.var_pitch.get(),
        #     medium=self.var_medium.get()
        #     )
        
        # Show save as dialog
        outfile_name = fd.asksaveasfilename(initialfile="Analysis.csv")
        self.var_folder.set(
            outfile_name
            )
        self.focus()
        return
    
    def _save(self):
        f = open(self.var_folder.get(), 'w', newline='')
        self.outfile = csv.writer(
            f,
            delimiter=','
            )
        self.outfile.writerow([
            "Id",
            "Img name",
            "Length [um]",
            "Diameter [um]",
            "Density [um]",
            "x1", "y1", "x2", "y2",
            "Tip displacement [um]",
            "Bending angle [rad]",
            "Orientation [deg]"
            ]     
            )
        
        row = 1
        for line in self.data:
            x1, y1, x2, y2, img_name = line
            displace = np.sqrt((x2-x1)**2 + (y2-y1)**2) / float(self.var_scale.get())
            bend = np.arcsin(displace / int(self.var_len.get())) * 180 / np.pi
            dy = y2-y1
            dx = x2-x1
            if dx == 0:
                if dy < 0:
                    direction = -90.0
                else:
                    direction = 90.0
            else:
                direction = np.degrees(np.arctan(dy/dx))
            
            self.outfile.writerow([
                row,
                img_name,
                int(self.var_len.get()),
                int(self.var_dia.get()),
                int(float(self.var_pitch.get())),
                x1, y1, x2, y2,
                round(displace, 2),
                round(bend, 2),
                round(direction,2)
                ])
            row += 1
        
        f.close()
        self.outfile = None
        self.destroy()
        return


def drawCrosshare(canv, x, y):
    size = 10
    # Points are just the extremities of the crosshare including the center point to prevent connection of corners to each other
    points = [
        (x-size, y),
        (x+size, y), # Draw horizontal line
        (x, y), # Return to center
        (x, y-size),
        (x, y+size), # Draw vertical line
        (x, y) # Return to center
        ]
    return canv.create_polygon(points, outline = 'light blue', width=1)

def drawDotCursor(canv, x, y):
    size = 2
    return canv.create_oval(x, y, x+size, y+size, outline="red", fill="red")
    

if __name__ == "__main__":
    main()
