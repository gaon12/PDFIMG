# 설치 목록
# pip install tkinterdnd2 pymupdf pillow pillow-avif-plugin customtkinter

import os
import threading
import tkinter as tk
from tkinter import messagebox, Toplevel, ttk, filedialog, simpledialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import fitz  # pymupdf
from PIL import Image, ImageTk
import pillow_avif
import customtkinter as ctk
import json
import locale
import shutil
from concurrent.futures import ThreadPoolExecutor

FONT = ("Arial", 12)

# OS 언어 감지
sys_locale = locale.getdefaultlocale()[0]
if sys_locale.startswith('ko'):
	DEFAULT_LANG = "ko"
elif sys_locale.startswith('ja'):
	DEFAULT_LANG = "ja"
else:
	DEFAULT_LANG = "en"

CURRENT_LANG = DEFAULT_LANG

def load_language(lang):
	"""
	Load the language file based on the given language code.
	언어 코드를 기반으로 언어 파일을 로드합니다.
	"""
	# lang_file = os.path.join("./langs", f"{lang}.json")
	lang_file = os.path.join(os.environ.get('RESOURCE_PATH', '.'), 'langs', f"{lang}.json")
	if not os.path.exists(lang_file):
		lang_file = os.path.join("./langs", "en.json")
	with open(lang_file, "r", encoding="utf-8") as f:
		return json.load(f)

messages = load_language(CURRENT_LANG)

def create_non_closable_popup(title, message):
	"""
	Create a non-closable popup window.
	닫을 수 없는 팝업 창을 생성합니다.
	"""
	popup = Toplevel(root)
	popup.title(title)
	popup.geometry("400x100")
	popup.resizable(False, False)
	popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button

	label = tk.Label(popup, text=message, font=FONT, wraplength=350)
	label.pack(pady=20)

	return popup

def request_password(file_name):
	"""
	Request the user to input the password for a protected PDF file.
	보호된 PDF 파일의 비밀번호를 사용자에게 입력받습니다.
	"""
	while True:
		password = simpledialog.askstring(
			title=messages["password_required_title"],
			prompt=messages["password_required_msg"].format(file=file_name),
			show="*"
		)
		if password is None:  # "Cancel" option
			skip = messagebox.askyesno(messages["skip_title"], messages["skip_msg"].format(file=file_name))
			if skip:
				return None  # Skip this file
			continue
		return password

def open_pdf_with_password(file_path):
	"""
	Try to open a password-protected PDF. Prompt the user for the password if needed.
	비밀번호로 보호된 PDF를 여는 작업을 시도합니다. 비밀번호가 필요하면 사용자에게 요청합니다.
	"""
	while True:
		try:
			doc = fitz.open(file_path)
			if doc.needs_pass:  # Check if the PDF requires a password
				password = request_password(os.path.basename(file_path))
				if password is None:  # Skip this file
					return None
				if not doc.authenticate(password):  # Incorrect password
					messagebox.showerror(messages["error"], messages["incorrect_password"])
					continue
			return doc
		except Exception as e:
			messagebox.showerror(messages["error"], f"{messages['file_processing_error']}: {e}")
			return None

def show_loading_popup():
	"""
	Display a non-closable loading popup while processing files.
	파일 처리 중 닫을 수 없는 로딩 팝업을 표시합니다.
	"""
	return create_non_closable_popup(messages["converting"], messages["checking_file"])

def show_progress_popup(total_pages):
	"""
	Display a progress popup for tracking the conversion of PDF pages.
	PDF 페이지 변환 과정을 추적하기 위한 진행 팝업을 표시합니다.
	"""
	popup = Toplevel(root)
	popup.title(messages["converting"])
	popup.geometry("400x150")
	popup.resizable(False, False)
	popup.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button

	label = tk.Label(popup, text=messages["converting_images"], font=FONT)
	label.pack(pady=10)

	progress_bar = ttk.Progressbar(popup, orient="horizontal", mode="determinate", length=350)
	progress_bar.pack(pady=10)
	progress_bar["maximum"] = total_pages

	progress_label = tk.Label(popup, text=messages["page_progress"].format(idx=0, total=total_pages, percent=0), font=FONT)
	progress_label.pack(pady=5)

	return popup, progress_bar, progress_label

def convert_page(page, output_format, output_folder, idx, pad_filenames):
	"""
	Convert a single PDF page to an image.
	단일 PDF 페이지를 이미지로 변환합니다.
	"""
	pix = page.get_pixmap()
	file_number = f"{idx:03}" if pad_filenames else str(idx)
	output_path = os.path.join(output_folder, f"{file_number}.{output_format}")

	# Check if the file already exists
	if os.path.exists(output_path):
		proceed = messagebox.askyesno(
			messages["error"],
			messages["file_already_exists"].format(file=output_path)
		)
		if not proceed:
			return None

	# Convert Pixmap to PIL Image
	image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

	# Check size limitations for specific formats
	max_size = {
		"webp": 16383,  # WebP max dimensions
		"avif": 65535   # AVIF max dimensions (adjust if necessary)
	}
	if output_format in max_size:
		if pix.width > max_size[output_format] or pix.height > max_size[output_format]:
			# Notify user and ask for resolution
			proceed = messagebox.askyesno(
				messages["error"],
				messages["size_limit_exceeded"].format(
					format=output_format.upper(),
					width=pix.width,
					height=pix.height,
					max_size=max_size[output_format]
				)
			)
			if not proceed:
				return None
			# Fallback to PNG format
			output_format = "png"
			output_path = os.path.join(output_folder, f"{file_number}.{output_format}")

	# Save with Pillow
	if output_format in ["webp", "bmp", "avif"]:
		image.save(output_path, format=output_format.upper())
	else:
		pix.save(output_path)  # fitz 지원 포맷 (e.g., png, jpg)

def convert_pdf_to_images(file_path, output_format, pad_filenames, update_progress=None):
	"""
	Convert a PDF file to images using pymupdf (fitz).
	pymupdf(fitz)를 사용하여 PDF 파일을 이미지로 변환합니다.
	"""
	output_folder = os.path.join(os.path.dirname(file_path), os.path.splitext(os.path.basename(file_path))[0])
	os.makedirs(output_folder, exist_ok=True)

	try:
		doc = open_pdf_with_password(file_path)
		if doc is None:  # Skip file if password failed or user chose to skip
			return None, 0

		total_pages = len(doc)

		with ThreadPoolExecutor() as executor:
			futures = []
			for i in range(total_pages):
				futures.append(
					executor.submit(
						convert_page, doc[i], output_format, output_folder, i + 1, pad_filenames
					)
				)
				if update_progress:
					update_progress(i + 1, total_pages)

		return output_folder, total_pages
	finally:
		if doc:
			doc.close()

def process_pdf(file_paths):
	"""
	Process selected PDF files for conversion.
	선택된 PDF 파일들을 변환합니다.
	"""
	output_format = image_format_var.get()
	pad_filenames = pad_var.get()

	def start_conversion():
		loading_popup = show_loading_popup()
		try:
			valid_pdfs = [f for f in file_paths if f.lower().endswith(".pdf")]
			if not valid_pdfs:
				messagebox.showerror(messages["error"], messages["not_pdf_error"])
				return

			for file_path in valid_pdfs:
				file_path = os.path.abspath(file_path)

				# 페이지 수 체크
				try:
					doc = open_pdf_with_password(file_path)
					if doc is None:
						continue
					total_pages = len(doc)
				except Exception as e:
					messagebox.showerror(messages["error"], f"{messages['file_processing_error']}: {e}")
					continue

				# 페이지 수 많을 경우 확인
				if total_pages > 50:
					proceed = messagebox.askyesno(
						messages["many_pages_title"],
						messages["many_pages_msg"].format(total_pages=total_pages)
					)
					if not proceed:
						continue

				if loading_popup.winfo_exists():
					loading_popup.destroy()

				popup, progress_bar, progress_label = show_progress_popup(total_pages)

				def update_progress(idx, total):
					progress_bar["value"] = idx
					percent = int((idx / total) * 100)
					progress_label.config(text=messages["page_progress"].format(idx=idx, total=total, percent=percent))
					popup.update_idletasks()

				try:
					output_folder, _ = convert_pdf_to_images(file_path, output_format, pad_filenames, update_progress)
					if output_folder:
						messagebox.showinfo(messages["done"], messages["conversion_complete"].format(folder=output_folder))
				except Exception as e:
					messagebox.showerror(messages["error"], f"{messages['file_processing_error']}: {e}")
				finally:
					if popup and popup.winfo_exists():
						popup.destroy()
		finally:
			if loading_popup and loading_popup.winfo_exists():
				loading_popup.destroy()

	threading.Thread(target=start_conversion).start()

def on_drop(event):
	file_paths = root.tk.splitlist(event.data)
	if not any([f.lower().endswith(".pdf") for f in file_paths]):
		messagebox.showerror(messages["error"], messages["not_pdf_error"])
		return
	process_pdf(file_paths)

def select_file():
	file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
	if file_path:
		process_pdf([file_path])

def show_info():
	messagebox.showinfo(messages["info_title"], messages["info_msg"])

def close_app():
	root.destroy()

def set_language(lang):
	global CURRENT_LANG, messages
	CURRENT_LANG = lang
	messages = load_language(CURRENT_LANG)
	update_texts()

def rebuild_menus():
	# 기존 메뉴들 제거 후 다시 생성
	menubar.delete(0, 'end')

	# file_menu 재생성
	new_file_menu = tk.Menu(menubar, tearoff=0)
	new_file_menu.add_command(label=messages["select_file"], command=select_file)
	new_file_menu.add_command(label=messages["info"], command=show_info)
	new_file_menu.add_separator()
	new_file_menu.add_command(label=messages["close"], command=close_app)

	# lang_menu 재생성
	new_lang_menu = tk.Menu(menubar, tearoff=0)
	new_lang_menu.add_radiobutton(label="한국어", variable=lang_var, value="ko", command=set_lang_ko)
	new_lang_menu.add_radiobutton(label="English", variable=lang_var, value="en", command=set_lang_en)
	new_lang_menu.add_radiobutton(label="日本語", variable=lang_var, value="ja", command=set_lang_ja)

	menubar.add_cascade(label=messages["file_menu"], menu=new_file_menu)
	menubar.add_cascade(label=messages["language_menu"], menu=new_lang_menu)
	root.config(menu=menubar)

def update_texts():
	try:
		rebuild_image_format_menu()
		rebuild_menus()

		format_label.configure(text=messages["img_format"])
		pad_label.configure(text=messages["pad_filenames"])
		pad_checkbox.configure(text=messages["pad_option"])
	except Exception as e:
		# 디버그용 출력
		print("Error in update_texts:", e)

def set_lang_ko():
	set_language("ko")

def set_lang_en():
	set_language("en")

def set_lang_ja():
	set_language("ja")

def rebuild_image_format_menu():
	"""
	Remove and recreate existing menus
	이미지 형식 메뉴를 재구성합니다.
	"""
	image_format_menu.delete(0, 'end')
	formats = ["jpg", "png", "webp", "bmp", "avif"]
	for f in formats:
		image_format_menu.add_radiobutton(label=f.upper(), variable=image_format_var, value=f)

def show_image_format_menu():
	x = image_format_button.winfo_rootx()
	y = image_format_button.winfo_rooty() + image_format_button.winfo_height()
	image_format_menu.post(x, y)

def check_poppler():
	poppler_path = shutil.which("pdftoppm")
	if poppler_path is None:
		messagebox.showwarning(messages["info_title"], messages["poppler_not_found"])

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = TkinterDnD.Tk()

# 아이콘 경로 설정
icon_path = os.path.join(os.environ.get('RESOURCE_PATH', '.'), 'imgs', 'icon.png')
if os.path.exists(icon_path):
	try:
		icon_image = Image.open(icon_path)
		icon_photo = ImageTk.PhotoImage(icon_image)
		root.iconphoto(False, icon_photo)
	except Exception as e:
		print(f"Error loading icon: {e}")
else:
	print("Icon file not found.")

root.title("PDF to Image Converter")
root.geometry("570x350")
root.resizable(False, False)

check_poppler()

menubar = tk.Menu(root)

file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label=messages["select_file"], command=select_file)
file_menu.add_command(label=messages["info"], command=show_info)
file_menu.add_separator()
file_menu.add_command(label=messages["close"], command=close_app)

lang_menu = tk.Menu(menubar, tearoff=0)
lang_var = tk.StringVar(value=CURRENT_LANG)

lang_menu.add_radiobutton(label="한국어", variable=lang_var, value="ko", command=set_lang_ko)
lang_menu.add_radiobutton(label="English", variable=lang_var, value="en", command=set_lang_en)
lang_menu.add_radiobutton(label="日本語", variable=lang_var, value="ja", command=set_lang_ja)

menubar.add_cascade(label=messages["file_menu"], menu=file_menu)
menubar.add_cascade(label=messages["language_menu"], menu=lang_menu)
root.config(menu=menubar)

# bg_path = os.path.abspath("./imgs/bg.png")
bg_path = os.path.join(os.environ.get('RESOURCE_PATH', '.'), 'imgs', 'bg.png')
if os.path.exists(bg_path):
	bg_image = Image.open(bg_path)
	bg_photo = ImageTk.PhotoImage(bg_image)
	bg_label = tk.Label(root, image=bg_photo)
	bg_label.place(relwidth=1, relheight=1)
else:
	bg_label = tk.Label(root, text=messages["no_bg_img"], font=FONT, bg="lightgray")
	bg_label.place(relwidth=1, relheight=1)

settings_frame = ctk.CTkFrame(root, width=510, height=100, corner_radius=10)
settings_frame.place(x=10, y=240)

pad_var = tk.BooleanVar(value=False)

pad_label = ctk.CTkLabel(settings_frame, text=messages["pad_filenames"], font=FONT)
pad_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)
pad_checkbox = ctk.CTkCheckBox(settings_frame, text=messages["pad_option"], variable=pad_var)
pad_checkbox.grid(row=1, column=1, padx=10, pady=10)

image_format_var = tk.StringVar(value="png")
image_format_menu = tk.Menu(menubar, tearoff=0)
rebuild_image_format_menu()

format_label = ctk.CTkLabel(settings_frame, text=messages["img_format"], font=FONT)
format_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)

image_format_button = ctk.CTkButton(settings_frame, textvariable=image_format_var, command=show_image_format_menu)
image_format_button.grid(row=0, column=1, padx=10, pady=10)

root.drop_target_register(DND_FILES)
root.dnd_bind("<<Drop>>", on_drop)

root.mainloop()
