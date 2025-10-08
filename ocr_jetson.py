import tkinter as tk
from PIL import Image, ImageTk
import cv2
import threading
import time
from datetime import datetime
import os
import gc
import numpy as np
import socket
import argparse
import xml.etree.ElementTree as ET
import logging

ocr_instance = None
camera = None
root = None
canvas = None
img_on_canvas = None
running_live_view = False
current_frame = None
paused = False 
recognition_text = ""


def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=960,  
    display_height=540,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def load_ocr_model():
    global ocr_instance
    print("Loading OCR model...")
    os.environ['FLAGS_log_severity_level'] = '1'
    os.environ['FLAGS_log_dir'] = './tmp_paddle_logs'
    logging.getLogger('paddle').setLevel(logging.ERROR)
    logging.getLogger('ppocr').setLevel(logging.ERROR)
    from paddleocr import PaddleOCR
    ocr_instance = PaddleOCR(use_angle_cls=False)
    print("✅ OCR model loading completed.")

def prepare_camera(flip_method=0):
    global camera
    if camera and camera.isOpened():
        return
    
    pipeline = gstreamer_pipeline(
        capture_width=1920,
        capture_height=1080,
        display_width=960,
        display_height=540,
        flip_method=flip_method
    )
    
    print(f"Using GStreamer Pipeline: {pipeline}")
    camera = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    
    if not camera.isOpened():
        print("❌ Error: Unable to open CSI camera via GStreamer.")
        camera = None
        return
        
    print("✅ CSI Camera setup completed.")
        

def release_camera():
    global camera
    if camera:
        print("Clean up camera resources...")
        try:
            if camera.isOpened():
                camera.release()
        except Exception as e:
            print(f"⚠️ Error closing camera: {e}")
        camera = None

def get_frame(orientation=0):
    global current_frame
    if camera is None or not camera.isOpened():
        return None
        
    ret, frame = camera.read()
    if not ret:
        print("❌ Error reading frame from camera.")
        return None

    current_frame = frame
    return frame
    

    
def update_live_view(canvas, canvas_w, canvas_h, orientation):
    global running_live_view, img_on_canvas, current_frame, paused
    if not running_live_view or paused:
        return
    
    frame = get_frame(orientation) 
    if frame is not None:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        h, w = frame_rgb.shape[:2]
        ratio = min(canvas_w / w, canvas_h / h)
        resized_w, resized_h = int(w * ratio), int(h * ratio)
        img = Image.fromarray(frame_rgb)
        img = img.resize((resized_w, resized_h), Image.LANCZOS)
        
        imgtk = ImageTk.PhotoImage(image=img)
        
        canvas.delete("all")
        canvas.create_image((canvas_w - resized_w) // 2, (canvas_h - resized_h) // 2, anchor=tk.NW, image=imgtk)
        canvas.image = imgtk
        
    if recognition_text:
        draw_recognition_text(canvas, canvas_w, canvas_h, recognition_text)    
    root.after(100, lambda: update_live_view(canvas, canvas_w, canvas_h, orientation))
    

def create_xml_output(detection_results, output_path):
    root_elem = ET.Element("Rectangles")
    
    for i, box in enumerate(detection_results):
        pts = np.array(box).astype(np.int32)
        x1, y1 = np.min(pts[:, 0]), np.min(pts[:, 1])
        x2, y2 = np.max(pts[:, 0]), np.max(pts[:, 1])
        
        rect_elem = ET.SubElement(root_elem, "Rectangle")
        rect_elem.set("id", f"r{i+1}")
        rect_elem.set("x", str(x1))
        rect_elem.set("y", str(y1))
        rect_elem.set("width", str(x2 - x1))
        rect_elem.set("height", str(y2 - y1))
        
    tree = ET.ElementTree(root_elem)
    ET.indent(tree, space="\t", level=0)
    
    with open(output_path, "wb") as f:
        f.write(ET.tostring(root_elem, encoding="utf-8"))
    
    print(f"✅ The detection results are saved to XML file：{output_path}")

def draw_rectangles(canvas, canvas_w, canvas_h, original_w, original_h, detection_results, color='red'):
    ratio = min(canvas_w / original_w, canvas_h / original_h)
    
    for box in detection_results:
        pts = np.array(box).astype(np.int32)
        x1, y1 = np.min(pts[:, 0]), np.min(pts[:, 1])
        x2, y2 = np.max(pts[:, 0]), np.max(pts[:, 1])
        
        draw_x1 = (x1 * ratio) + (canvas_w - original_w * ratio) / 2
        draw_y1 = (y1 * ratio) + (canvas_h - original_h * ratio) / 2
        draw_x2 = (x2 * ratio) + (canvas_w - original_w * ratio) / 2
        draw_y2 = (y2 * ratio) + (canvas_h - original_h * ratio) / 2
        
        canvas.create_rectangle(draw_x1, draw_y1, draw_x2, draw_y2, outline=color, width=2)

    
def get_output_path(output_arg, default_prefix, extension):
    if output_arg:
        return output_arg
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{default_prefix}_{timestamp}.{extension}"

def handle_capture(args):
    print("Capturing...")
    prepare_camera(args.orientation) 
    frame = get_frame(args.orientation)
    if frame is None:
        return
    
    output_path = get_output_path(args.output, "capture_image", "jpg")
    cv2.imwrite(output_path, frame)
    print(f"✅ The image has been saved to：{output_path}")

def handle_detect(args, canvas=None, canvas_w=None, canvas_h=None):
    global running_live_view, paused
    load_ocr_model()
    
    is_live_view = (canvas is not None)

    if args.input:
        img = cv2.imread(args.input)
        if img is None:
            print(f"❌ Unable to load image：{args.input}")
            return
    else:
        prepare_camera(args.orientation)
        img = get_frame(args.orientation)
        if img is None:
            return
        
    print("🔍Executing text detection...")
    result = ocr_instance.ocr(img, det=True, cls=False)
    
    if not result or not result[0]:
        print("❌ No text detected.")
        
        if is_live_view:
            paused = True
            print("❗ Please enter another command, or type 'quit' to exit.")
        return
    
    detection_boxes = [line[0] for line in result[0]]
    original_h, original_w = img.shape[:2]

    if is_live_view:
        # 1. Freeze Live View 
        paused = True
        
        # 2. Clear old canvas contents
        canvas.delete("all")
        
        # 3. Redraw the static detection screen on the canvas (img)
        frame_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Make sure the screen shows a static image during detection.
        ratio = min(canvas_w / original_w, canvas_h / original_h)
        resized_w, resized_h = int(original_w * ratio), int(original_h * ratio)
        
        img_pil = Image.fromarray(frame_rgb)
        img_pil = img_pil.resize((resized_w, resized_h), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img_pil)
        
        canvas.create_image((canvas_w - resized_w) // 2, (canvas_h - resized_h) // 2, anchor=tk.NW, image=imgtk)
        canvas.image = imgtk
        
        draw_rectangles(canvas, canvas_w, canvas_h, original_w, original_h, detection_boxes, color='red')
        
        print("❗Please type 'view'、'quit' ")
        
    output_path = get_output_path(args.output, "detection_result", "xml")
    create_xml_output(detection_boxes, output_path)


def handle_recognize(args, canvas=None, canvas_w=None, canvas_h=None):
    global recognition_text 
    
    load_ocr_model()
    
    is_live_view = (canvas is not None)

    if args.input:
        img = cv2.imread(args.input)
        if img is None:
            print(f"❌ Unable to load image：{args.input}")
            return
    else:
        prepare_camera(args.orientation)
        img = get_frame(args.orientation)
        if img is None:
            return
    
    print("🔍 Executing OCR...")
    result = ocr_instance.ocr(img, det=True, cls=False)
    
    if not result or not result[0]:
        print("❌ No text was recognized")
        recognition_text = "No text was recognized"
        return
        
    lines = [line[1][0] for line in result[0]]
    text_result = "\n".join(lines) 

    recognition_text = text_result
    print("✅ Results：")
    print(text_result)

def draw_recognition_text(canvas, canvas_w, canvas_h, text, color='yellow'):
    padding = 20
    x_pos = canvas_w - padding
    y_pos = canvas_h - padding
    
    canvas.delete("ocr_result_text")
  
    canvas.create_text(
        x_pos, 
        y_pos, 
        text=text, 
        fill=color,
        font=("Helvetica", 16, "bold"),
        anchor=tk.SE,
        justify=tk.RIGHT,
        tags="ocr_result_text",
    )
    
def command_listener(initial_args, canvas=None, canvas_w=None, canvas_h=None):
    global paused
    base_args = argparse.Namespace(
        orientation=initial_args.orientation,
        xml_output=getattr(initial_args, 'xml_output', None), 
        output=None,
        input=None
    )

    while True:
        cmd_line = input("👉 Input command (capture/view_recognize/view_detect/view/quit): ").strip()
        cmd_parts = cmd_line.lower().split()
        cmd = cmd_parts[0] if cmd_parts else ""

        current_args = base_args
        
        if cmd == "quit":
            print("🛑 End")
            os._exit(0) 
        
        elif cmd == "capture":
            cap_args = argparse.Namespace(**vars(base_args))
            cap_args.output = cmd_parts[1] if len(cmd_parts) > 1 else None
            handle_capture(cap_args)
            
        elif cmd == "view_detect":
            det_args = argparse.Namespace(**vars(base_args))
            det_args.input = None 
            det_args.output = cmd_parts[1] if len(cmd_parts) > 1 else None 
            if canvas is None:
                print("⚠️ Live View is not enabled yet, please use 'view' mode first.")
                
            else:
                handle_detect(det_args, canvas=canvas, canvas_w=canvas_w, canvas_h=canvas_h)
            
        elif cmd == "view_recognize":
            rec_args = argparse.Namespace(**vars(base_args))
            rec_args.input = None
            
            rec_args.output = cmd_parts[1] if len(cmd_parts) > 1 else None 

            if canvas is None:
                print("⚠️ Live View is not enabled yet, please use 'view' mode first.")
            else:
                handle_recognize(rec_args, canvas=canvas, canvas_w=canvas_w, canvas_h=canvas_h)
        elif cmd == "view":
           if canvas:
             if paused:
               paused = False
               print("▶️ Live View Recovery")
               if canvas and canvas_w and canvas_h:
                        root.after(10, lambda: update_live_view(canvas, canvas_w, canvas_h, base_args.orientation))
             else:
               print("⚠️ Live View is already in progress.")    
        else:
            print("❌ Unknown command, please type capture/detect/view_recognize/view_detect/quit")
    
def run_live_view(args):
    global root, canvas, running_live_view, paused, current_frame, canvas_w, canvas_h
    prepare_camera(args.orientation) 
    
    root = tk.Tk()
    root.title("Transcend OCR Demo Tool")
    
    canvas_w, canvas_h = 800, 600
    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="black")
    canvas.pack(padx=10, pady=10)
    
    info_label = tk.Label(root, text="Please type in the terminal: capture, view_detect, view_recognize, view, quit", font=("Helvetica", 12))
    info_label.pack(pady=5)
    
    running_live_view = True
    paused = False
    update_live_view(canvas, canvas_w, canvas_h, args.orientation)

    threading.Thread(target=command_listener, args=(args, canvas, canvas_w, canvas_h), daemon=True).start()

    root.mainloop()

def main():
    parser = argparse.ArgumentParser(description="Transcend OCR Demo Tool")
    subparsers = parser.add_subparsers(dest="command", help="Select a command")
    
    # view 
    view_parser = subparsers.add_parser("view", help="Show live view")
    view_parser.add_argument("-o", "--orientation", type=int, default=0, choices=[0, 1, 2, 3], 
                             help="Rotate the image (0=no rotation, 1=90°, 2=180°, 3=270°). Note: Relies on GStreamer flip_method for actual rotation/flip.")
    
    # image_detect
    detect_parser = subparsers.add_parser("image_detect", help="Detect text in images and output XML")
    detect_group = detect_parser.add_mutually_exclusive_group(required=True)
    detect_group.add_argument("-i", "--input", type=str, help="Specify the input image path")
    detect_parser.add_argument("-x", "--output", type=str, default=None, help="Specify the XML report storage path")
    
    # image_recognize
    recognize_parser = subparsers.add_parser("image_recognize", help="Perform OCR and output the results")
    recognize_group = recognize_parser.add_mutually_exclusive_group(required=True)
    recognize_group.add_argument("-i", "--input", type=str, help="Specify the input image path")
    
    args = parser.parse_args()
    
    if args.command == "view":
        load_ocr_model()
        run_live_view(args)
    elif args.command == "image_detect":
        load_ocr_model()
        handle_detect(args) 
    elif args.command == "image_recognize":
        load_ocr_model()
        handle_recognize(args)
    else:
        parser.print_help()
    
    release_camera()
    
if __name__ == "__main__":
    main()
