import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab
import os
import glob
import json
import shutil
from datetime import datetime
import re
import tempfile


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字典json生成")

        # 初始化数据结构
        self.current_data = {
            "image": "",
            "annotator": "",
            "page_info": {
                "page_num": "",
                "word_num": ""
            },
            "imported_source_path": "",
            "imported_image": [],
            "pronunciations": []
        }

        # 加载图片文件
        image_dir = "image"
        output_dir = "output"
        image_extensions = ["*.png", "*.jpg", "*.jpeg"]
        self.image_files = sorted(
            [f for ext in image_extensions for f in glob.glob(os.path.join(image_dir, ext))]
        )

        # 加载配置文件
        config_path = "config.json"
        self.current_image_index = 0
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    last_index = config.get("last_index", 0)
                    if 0 <= last_index < len(self.image_files):
                        self.current_image_index = last_index
            except:
                pass

        # 创建界面
        self.create_widgets()

        # 加载当前图片
        if self.image_files:
            self.load_current_image()
        else:
            self.show_empty_message()

    def show_empty_message(self):
        self.img_canvas.delete("all")
        self.img_canvas.create_text(250, 250, text="没有找到任何图片", fill="red")
        self.title_label.config(text="错误状态")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 左侧图片区域
        self.create_image_panel()
        # 右侧表单区域
        self.create_form_panel()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_image_panel(self):
        left_frame = tk.Frame(self.main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.title_label = tk.Label(left_frame, text="", font=("微软雅黑", 12))
        self.title_label.pack(pady=5)

        self.img_canvas = tk.Canvas(left_frame, width=200, height=200, bg='#e0e0e0')
        self.img_canvas.pack()

        # 缩略图容器
        self.thumbnail_frame = tk.Frame(left_frame, height=80)
        self.thumbnail_frame.pack(pady=5, fill=tk.X)
        self.thumbnail_labels = []
        self.thumbnail_images = []

        nav_frame1 = tk.Frame(left_frame)
        nav_frame1.pack(pady=5)

        first_row_btns = [
            ("上一页", self.show_previous_image),
            ("下一页", self.show_next_image),
            ("提交", self.submit_data)
        ]

        for text, cmd in first_row_btns:
            btn = tk.Button(nav_frame1, text=text, width=6, command=cmd)
            if text == "提交":
                btn.config(width=8, bg='#4CAF50')
            btn.pack(side=tk.LEFT, padx=2)

        self.page_entry = tk.Entry(nav_frame1, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame1, text="跳转", width=6, command=self.jump_to_page).pack(side=tk.LEFT, padx=2)

        nav_frame2 = tk.Frame(left_frame)
        nav_frame2.pack(pady=5)

        second_row_btns = [
            ("导入图片", self.import_image),
            ("实时截图", self.capture_screen)
        ]

        for text, cmd in second_row_btns:
            tk.Button(nav_frame2, text=text, width=8, command=cmd).pack(side=tk.LEFT, padx=2)

    def update_thumbnail_panel(self):
        """更新缩略图显示（只显示最新图片）"""
        # 清空现有缩略图
        for label in self.thumbnail_labels:
            label.destroy()
        self.thumbnail_labels.clear()
        self.thumbnail_images.clear()

        # 优先级：临时图片 > 已提交图片
        temp_path = self.current_data.get("imported_source_path", "")
        if temp_path and os.path.exists(temp_path):
            try:
                img = Image.open(temp_path)
                img.thumbnail((50, 50))
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(self.thumbnail_frame, image=photo,
                                 borderwidth=2, relief="solid",
                                 highlightbackground="red")
                label.image = photo
                label.pack(side=tk.LEFT, padx=2)
                self.thumbnail_labels.append(label)
                self.thumbnail_images.append(photo)
                return  # 有临时图片时只显示临时图片
            except Exception as e:
                print(f"临时缩略图加载失败: {str(e)}")

        # 显示已提交的图片（只显示最新一张）
        input_dir = "input_image"
        latest_image = None
        if self.current_data.get("imported_image"):
            latest_image = self.current_data["imported_image"][-1]
            img_path = os.path.join(input_dir, latest_image)
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((50, 50))
                    photo = ImageTk.PhotoImage(img)
                    label = tk.Label(self.thumbnail_frame, image=photo,
                                     borderwidth=1, relief="solid")
                    label.image = photo
                    label.pack(side=tk.LEFT, padx=2)
                    self.thumbnail_labels.append(label)
                    self.thumbnail_images.append(photo)
                except Exception as e:
                    print(f"缩略图加载失败: {str(e)}")

    def capture_screen(self):
        self.root.withdraw()
        screen_win = tk.Toplevel()
        screen_win.attributes('-fullscreen', True)
        screen_win.attributes('-alpha', 0.3)
        screen_win.configure(cursor="crosshair")

        start_x = start_y = end_x = end_y = 0
        rect_id = None

        def on_mouse_down(event):
            nonlocal start_x, start_y
            start_x, start_y = event.x, event.y

        def on_mouse_move(event):
            nonlocal rect_id
            if rect_id:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                start_x, start_y, event.x, event.y,
                outline='red', width=3
            )

        def on_mouse_up(event):
            nonlocal end_x, end_y
            end_x, end_y = event.x, event.y
            screen_win.destroy()
            self.root.deiconify()
            self.save_captured_area(
                (min(start_x, end_x), min(start_y, end_y)),
                (max(start_x, end_x), max(start_y, end_y))
            )

        canvas = tk.Canvas(screen_win, cursor="crosshair")
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.bind("<ButtonPress-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)

    def save_captured_area(self, start_point, end_point):
        screenshot = ImageGrab.grab(bbox=(*start_point, *end_point))
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        screenshot.save(temp_file, format="PNG")
        temp_file.close()

        self.current_data["imported_source_path"] = temp_file.name
        self.update_thumbnail_panel()  # 立即更新缩略图
        messagebox.showinfo(
            "截图成功",
            f"已捕获区域：{start_point} - {end_point}\n"
            f"临时文件：{temp_file.name}"
        )

    def create_form_panel(self):
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        self.create_annotation_info_section(right_frame)
        self.create_pronunciation_section(right_frame)
        self.create_pos_section(right_frame)

    def create_annotation_info_section(self, parent):
        frame = tk.LabelFrame(parent, text="标注信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="标注作者:").grid(row=0, column=0, sticky='e', padx=5)
        self.annotator_entry = tk.Entry(frame, width=25)
        self.annotator_entry.grid(row=0, column=1, pady=2, sticky='w')

        tk.Label(frame, text="页码-第").grid(row=1, column=0, sticky='e', padx=5)
        self.page_num_entry = tk.Entry(frame, width=6)
        self.page_num_entry.grid(row=1, column=1, pady=2, sticky='w')
        tk.Label(frame, text="页").grid(row=1, column=2, sticky='w')

        tk.Label(frame, text="字位置-第").grid(row=1, column=3, sticky='e', padx=5)
        self.word_num_entry = tk.Entry(frame, width=6)
        self.word_num_entry.grid(row=1, column=4, pady=2, sticky='w')
        tk.Label(frame, text="个字").grid(row=1, column=5, sticky='w')

    def create_pronunciation_section(self, parent):
        frame = tk.LabelFrame(parent, text="读音信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="壮文音:").grid(row=0, column=0, sticky='e', padx=5)
        self.zh_wen_entry = tk.Entry(frame, width=25)
        self.zh_wen_entry.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="国际音标:").grid(row=0, column=2, sticky='e', padx=5)
        self.ipa_entry = tk.Entry(frame, width=25)
        self.ipa_entry.grid(row=0, column=3, pady=2)

        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=1, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新读音", command=self.add_new_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个", command=self.previous_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个", command=self.next_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="删除读音", command=self.delete_pronunciation).pack(side=tk.LEFT, padx=2)
        self.pronunciation_page = tk.Label(ctrl_frame, text="0/0")
        self.pronunciation_page.pack(side=tk.LEFT, padx=5)

    def create_pos_section(self, parent):
        frame = tk.LabelFrame(parent, text="词性信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        fields = [
            ("词性(中文):", "part_of_speech", 25),
            ("意思:", "meaning", 60),
            ("例句（壮文）:", "example_zhuang", 60),
            ("例句（中文）:", "example_chinese", 60)
        ]

        self.pos_entries = {}
        for i, (label, field, width) in enumerate(fields):
            tk.Label(frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(frame, width=width)
            entry.grid(row=i, column=1, columnspan=3, sticky='ew', pady=2)
            self.pos_entries[field] = entry

        pos_ctrl_frame = tk.Frame(frame)
        pos_ctrl_frame.grid(row=4, column=0, columnspan=4, pady=5)
        tk.Button(pos_ctrl_frame, text="添加新词性", command=self.add_new_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="上一个", command=self.previous_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="下一个", command=self.next_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="删除词性", command=self.delete_entry).pack(side=tk.LEFT, padx=2)
        self.pos_page = tk.Label(pos_ctrl_frame, text="0/0")
        self.pos_page.pack(side=tk.LEFT, padx=5)

        example_ctrl_frame = tk.Frame(frame)
        example_ctrl_frame.grid(row=5, column=0, columnspan=4, pady=5)
        tk.Button(example_ctrl_frame, text="新建例句", command=self.add_new_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="上一条", command=self.previous_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="下一条", command=self.next_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="删除例句", command=self.delete_example).pack(side=tk.LEFT, padx=2)
        self.example_page = tk.Label(example_ctrl_frame, text="例句 0/0")
        self.example_page.pack(side=tk.LEFT, padx=5)

    def create_pronunciation_section(self, parent):
        frame = tk.LabelFrame(parent, text="读音信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="壮文音:").grid(row=0, column=0, sticky='e', padx=5)
        self.zh_wen_entry = tk.Entry(frame, width=25)
        self.zh_wen_entry.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="国际音标:").grid(row=0, column=2, sticky='e', padx=5)
        self.ipa_entry = tk.Entry(frame, width=25)
        self.ipa_entry.grid(row=0, column=3, pady=2)

        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=1, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新读音", command=self.add_new_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个", command=self.previous_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个", command=self.next_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="删除读音", command=self.delete_pronunciation).pack(side=tk.LEFT, padx=2)
        self.pronunciation_page = tk.Label(ctrl_frame, text="0/0")
        self.pronunciation_page.pack(side=tk.LEFT, padx=5)

    def create_pos_section(self, parent):
        frame = tk.LabelFrame(parent, text="词性信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        fields = [
            ("词性(中文):", "part_of_speech", 25),
            ("意思:", "meaning", 60),
            ("例句（壮文）:", "example_zhuang", 60),
            ("例句（中文）:", "example_chinese", 60)
        ]

        self.pos_entries = {}
        for i, (label, field, width) in enumerate(fields):
            tk.Label(frame, text=label).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            entry = tk.Entry(frame, width=width)
            entry.grid(row=i, column=1, columnspan=3, sticky='ew', pady=2)
            self.pos_entries[field] = entry

        pos_ctrl_frame = tk.Frame(frame)
        pos_ctrl_frame.grid(row=4, column=0, columnspan=4, pady=5)
        tk.Button(pos_ctrl_frame, text="添加新词性", command=self.add_new_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="上一个", command=self.previous_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="下一个", command=self.next_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="删除词性", command=self.delete_entry).pack(side=tk.LEFT, padx=2)
        self.pos_page = tk.Label(pos_ctrl_frame, text="0/0")
        self.pos_page.pack(side=tk.LEFT, padx=5)

        example_ctrl_frame = tk.Frame(frame)
        example_ctrl_frame.grid(row=5, column=0, columnspan=4, pady=5)
        tk.Button(example_ctrl_frame, text="新建例句", command=self.add_new_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="上一条", command=self.previous_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="下一条", command=self.next_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="删除例句", command=self.delete_example).pack(side=tk.LEFT, padx=2)
        self.example_page = tk.Label(example_ctrl_frame, text="例句 0/0")
        self.example_page.pack(side=tk.LEFT, padx=5)

    def load_current_image(self):
        try:
            if not self.image_files:
                return

            image_path = self.image_files[self.current_image_index]
            current_image_filename = os.path.basename(image_path)
            json_path = os.path.join("output", os.path.splitext(current_image_filename)[0] + ".json")

            # 清除旧图片（在加载新图片前）
            self.cleanup_old_images()

            new_data_template = {
                "image": current_image_filename,
                "annotator": self.current_data.get("annotator", ""),  # 保留标注者信息
                "page_info": self.current_data.get("page_info", {"page_num": "", "word_num": ""}),  # 保留页码信息
                "imported_source_path": "",
                "imported_image": [],  # 重置导入图片记录
                "pronunciations": [{
                    "zhuang_spelling": "",
                    "ipa": "",
                    "entries": [{
                        "part_of_speech": "",
                        "meaning": "",
                        "examples": [{"壮文": "", "中文": ""}]
                    }]
                }]
            }

            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.current_data = data[0]
                        self.current_data["annotator"] = new_data_template["annotator"]
                        self.current_data["page_info"] = new_data_template["page_info"]
            else:
                self.current_data = new_data_template

            # 更新表单字段
            self.annotator_entry.delete(0, tk.END)
            self.annotator_entry.insert(0, self.current_data.get("annotator", ""))

            self.page_num_entry.delete(0, tk.END)
            self.page_num_entry.insert(0, self.current_data["page_info"].get("page_num", ""))

            self.word_num_entry.delete(0, tk.END)
            self.word_num_entry.insert(0, self.current_data["page_info"].get("word_num", ""))

            # 加载主图片
            img = Image.open(image_path)
            img.thumbnail((1000, 1000))
            photo = ImageTk.PhotoImage(img)

            self.img_canvas.image = photo
            self.img_canvas.delete("all")
            self.img_canvas.create_image(100, 100, image=photo)
            self.title_label.config(
                text=f"{self.current_data['image']} (第{self.current_image_index + 1}页/共{len(self.image_files)}页)")

            # 更新缩略图
            self.update_thumbnail_panel()

            # 重置导航索引
            self.current_pronunciation_index = 0
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()
        except Exception as e:
            self.img_canvas.delete("all")
            self.img_canvas.create_text(250, 250, text="图片加载失败", fill="red")
            print(f"错误: {str(e)}")

    def update_form(self):
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]

        self.zh_wen_entry.delete(0, tk.END)
        self.zh_wen_entry.insert(0, pron.get("zhuang_spelling", ""))
        self.ipa_entry.delete(0, tk.END)
        self.ipa_entry.insert(0, pron.get("ipa", ""))

        entry = pron["entries"][self.current_entry_index]
        self.pos_entries["part_of_speech"].delete(0, tk.END)
        self.pos_entries["part_of_speech"].insert(0, entry.get("part_of_speech", ""))
        self.pos_entries["meaning"].delete(0, tk.END)
        self.pos_entries["meaning"].insert(0, entry.get("meaning", ""))

        example = entry["examples"][self.current_example_index]
        self.pos_entries["example_zhuang"].delete(0, tk.END)
        self.pos_entries["example_zhuang"].insert(0, example.get("壮文", ""))
        self.pos_entries["example_chinese"].delete(0, tk.END)
        self.pos_entries["example_chinese"].insert(0, example.get("中文", ""))

        self.pronunciation_page.config(
            text=f"{self.current_pronunciation_index + 1}/{len(self.current_data['pronunciations'])}")
        self.pos_page.config(
            text=f"{self.current_entry_index + 1}/{len(pron['entries'])}")
        self.example_page.config(
            text=f"例句 {self.current_example_index + 1}/{len(entry['examples'])}")

    def save_current_form(self):
        self.current_data["annotator"] = self.annotator_entry.get()
        self.current_data["page_info"]["page_num"] = self.page_num_entry.get()
        self.current_data["page_info"]["word_num"] = self.word_num_entry.get()

        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        pron["zhuang_spelling"] = self.zh_wen_entry.get()
        pron["ipa"] = self.ipa_entry.get()

        entry = pron["entries"][self.current_entry_index]
        entry["part_of_speech"] = self.pos_entries["part_of_speech"].get()
        entry["meaning"] = self.pos_entries["meaning"].get()

        example = entry["examples"][self.current_example_index]
        example["壮文"] = self.pos_entries["example_zhuang"].get()
        example["中文"] = self.pos_entries["example_chinese"].get()

    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()

    def show_next_image(self):
        if self.current_image_index < len(self.image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()

    def jump_to_page(self):
        page = self.page_entry.get()
        try:
            page_num = int(page)
            if 1 <= page_num <= len(self.image_files):
                self.current_image_index = page_num - 1
                self.load_current_image()
            else:
                messagebox.showerror("错误", f"页码范围应为1-{len(self.image_files)}")
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字")

    def submit_data(self):
        self.save_current_form()
        self.cleanup_old_images()

        imported_images = list(self.current_data.get("imported_image", []))
        temp_source = self.current_data.get("imported_source_path", "")

        if temp_source:
            input_dir = "input_image"
            os.makedirs(input_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            try:
                # 只保留最新图片（删除旧记录）
                pron_names = list(set(
                    [p.get("zhuang_spelling", "unnamed")
                     for p in self.current_data["pronunciations"]]
                ))

                # 生成唯一文件名
                for pron_name in pron_names:
                    pron_name_clean = re.sub(r'[\\/*?:"<>|]', "", pron_name)
                    _, ext = os.path.splitext(temp_source)
                    ext = ext if ext else ".png"
                    filename = f"{pron_name_clean}_{timestamp}{ext}"
                    dest_path = os.path.join(input_dir, filename)

                    # 移动文件代替复制（提升性能）
                    if temp_source.startswith(tempfile.gettempdir()):
                        shutil.move(temp_source, dest_path)
                    else:
                        shutil.copyfile(temp_source, dest_path)

                    imported_images.append(filename)

                self.current_data["imported_image"] = imported_images
                self.current_data["imported_source_path"] = ""
            except Exception as e:
                messagebox.showerror("错误", f"文件处理失败: {str(e)}")
                return

        os.makedirs("output", exist_ok=True)
        filename = f"{os.path.splitext(self.current_data['image'])[0]}.json"
        full_path = os.path.join("output", filename)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump([self.current_data], f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"数据已保存到\n{full_path}")
        self.show_next_image()

    def on_close(self):
        with open("config.json", "w") as f:
            json.dump({"last_index": self.current_image_index}, f)
        self.root.destroy()

    def delete_pronunciation(self):
        if messagebox.askyesno("确认", "确定要删除当前读音及其所有词性信息吗？"):
            original_index = self.current_pronunciation_index
            self.save_current_form()
            del self.current_data["pronunciations"][original_index]

            if not self.current_data["pronunciations"]:
                self.current_data["pronunciations"].append({
                    "zhuang_spelling": "",
                    "ipa": "",
                    "entries": [{"part_of_speech": "", "meaning": "", "examples": [{"壮文": "", "中文": ""}]}]
                })

            self.current_pronunciation_index = min(original_index, len(self.current_data["pronunciations"]) - 1)
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()

    def delete_entry(self):
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if len(pron["entries"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前词性及其所有例句吗？"):
                self.save_current_form()
                del pron["entries"][self.current_entry_index]
                self.current_entry_index = max(0, self.current_entry_index - 1)
                self.update_form()

    def delete_example(self):
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][
            self.current_entry_index]
        if len(entry["examples"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前例句吗？"):
                self.save_current_form()
                del entry["examples"][self.current_example_index]
                self.current_example_index = max(0, self.current_example_index - 1)
                self.update_form()

    def add_new_pronunciation(self):
        self.save_current_form()
        new_pron = {
            "zhuang_spelling": "",
            "ipa": "",
            "entries": [{
                "part_of_speech": "",
                "meaning": "",
                "examples": [{"壮文": "", "中文": ""}]
            }]
        }
        self.current_data["pronunciations"].append(new_pron)
        self.current_pronunciation_index = len(self.current_data["pronunciations"]) - 1
        self.current_entry_index = 0
        self.current_example_index = 0
        self.update_form()

    def previous_pronunciation(self):
        if self.current_pronunciation_index > 0:
            self.save_current_form()
            self.current_pronunciation_index -= 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()

    def next_pronunciation(self):
        if self.current_pronunciation_index < len(self.current_data["pronunciations"]) - 1:
            self.save_current_form()
            self.current_pronunciation_index += 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()

    def add_new_entry(self):
        self.save_current_form()
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        pron["entries"].append({
            "part_of_speech": "",
            "meaning": "",
            "examples": [{"壮文": "", "中文": ""}]
        })
        self.current_entry_index = len(pron["entries"]) - 1
        self.current_example_index = 0
        self.update_form()

    def previous_entry(self):
        if self.current_entry_index > 0:
            self.save_current_form()
            self.current_entry_index -= 1
            self.current_example_index = 0
            self.update_form()

    def next_entry(self):
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if self.current_entry_index < len(pron["entries"]) - 1:
            self.save_current_form()
            self.current_entry_index += 1
            self.current_example_index = 0
            self.update_form()

    def add_new_example(self):
        self.save_current_form()
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][
            self.current_entry_index]
        entry["examples"].append({"壮文": "", "中文": ""})
        self.current_example_index = len(entry["examples"]) - 1
        self.update_form()

    def previous_example(self):
        if self.current_example_index > 0:
            self.save_current_form()
            self.current_example_index -= 1
            self.update_form()

    def next_example(self):
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][
            self.current_entry_index]
        if self.current_example_index < len(entry["examples"]) - 1:
            self.save_current_form()
            self.current_example_index += 1
            self.update_form()

    def import_image(self):
        file_path = filedialog.askopenfilename(
            title="选择要导入的图片",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.current_data["imported_source_path"] = file_path
            self.update_thumbnail_panel()  # 立即更新缩略图
            messagebox.showinfo("导入成功", f"已选择图片: {os.path.basename(file_path)}")

    def cleanup_old_images(self):
        """清理旧图片（当切换到新图片时）"""
        if not self.current_data.get("imported_image"):
            return

        input_dir = "input_image"
        for old_file in self.current_data["imported_image"]:
            old_path = os.path.join(input_dir, old_file)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
                    print(f"已删除旧图片: {old_path}")
            except Exception as e:
                print(f"删除旧图片失败: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()