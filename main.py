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
import time
import sys


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x1400")
        self.root.title("字典json生成")

        # 初始化数据结构
        self.current_data = {
            "image": "",
            "annotator": "",
            "page_info": {
                "page_num": "",
                "word_num": ""
            },
            "simplified_Chinese_character":"",
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
        self.current_pronunciation_index = 0  # 当前读音索引
        self.current_entry_index = 0  # 当前词性条目索引
        self.current_example_index = 0
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    last_index = config.get("last_index", 0)#get（）使用方法，如果键不存在，返回默认值
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
        self.img_canvas.create_text(250, 250, text="找不到图片,请在目录中创建image文件夹", fill="red")
        self.title_label.config(text="错误状态")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        #怎么调整主窗口大小 a:pack()函数是tkinter中的一个函数，用于在窗口中放置组件。它用于在窗口中放置组件，并设置组件的位置、大小、边框、背景色等属性。

        # 左侧图片区域
        self.create_image_panel()
        # 右侧表单区域
        self.create_form_panel()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_image_panel(self):
        left_frame = tk.Frame(self.main_frame)
        left_frame.pack(side=tk.TOP, fill=tk.Y)

        self.title_label = tk.Label(left_frame, text="", font=("微软雅黑", 12))
        self.title_label.pack(pady=5)

        self.img_canvas = tk.Canvas(left_frame, width=100, height=100, bg='#e0e0e0')
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
            btn.pack(side=tk.LEFT, padx=2)#pack是什么意思 a:pack()函数是tkinter中的一个函数，用于在窗口中放置组件。它用于在窗口中放置组件，并设置组件的位置、大小、边框、背景色等属性。

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
        """更新缩略图显示（显示当前读音的截图）"""
        # 清空现有缩略图
        for label in self.thumbnail_labels:
            label.destroy()
        self.thumbnail_labels.clear()
        self.thumbnail_images.clear()

        # 获取当前读音数据
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]

        # 优先级：临时图片 > 已提交图片
        temp_path = pron.get("imported_source_path", "")
        if temp_path and os.path.exists(temp_path):
            try:
                img = Image.open(temp_path)
                img.thumbnail((50, 50))
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(self.thumbnail_frame, image=photo,
                                 borderwidth=2, relief="solid",
                                 highlightbackground="red")
                label.bind("<Button-1>", lambda e, path=temp_path: self.show_enlarged_image(path))
                label.image = photo
                label.pack(side=tk.LEFT, padx=2)
                self.thumbnail_labels.append(label)
                self.thumbnail_images.append(photo)
                return
            except Exception as e:
                print(f"临时缩略图加载失败: {str(e)}")

        # 显示已提交的图片（只显示最新一张）
        input_dir = "output_image"
        if pron.get("imported_image"):
            latest_image = pron["imported_image"][-1]
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
                    label.bind("<Button-1>", lambda e, path=img_path: self.show_enlarged_image(path))
                    self.thumbnail_labels.append(label)
                    self.thumbnail_images.append(photo)
                except Exception as e:
                    print(f"缩略图加载失败: {str(e)}")

    def capture_screen(self):
        try:
            # 确保临时目录存在
            self.temp_dir = os.path.abspath("temp")
            os.makedirs(self.temp_dir, exist_ok=True)

            # 阶段1：截取全屏 -------------------------------------------------
            self.root.withdraw()  # 隐藏主窗口
            time.sleep(0.3)  # 等待窗口完全隐藏


            # 生成唯一文件名
            os.makedirs('temp', exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            fullscreen_temp_path = os.path.join(self.temp_dir, f"fullscreen_{timestamp}.png")

            # 截取并保存全屏
            screenshot = ImageGrab.grab()
            screenshot.save(fullscreen_temp_path, "PNG")

            # 阶段2：在全屏截图上选区 -------------------------------------------
            selector_window = tk.Toplevel(self.root)
            selector_window.attributes('-fullscreen', True)
            selector_window.attributes('-topmost', True)
            selector_window.configure(cursor="crosshair")

            # 加载并显示全屏截图
            img = Image.open(fullscreen_temp_path)
            img_width, img_height = img.size

            # 计算适合屏幕的缩放比例
            screen_width = selector_window.winfo_screenwidth()
            screen_height = selector_window.winfo_screenheight()
            scale = min(screen_width / img_width, screen_height / img_height)

            # 高质量缩放
            scaled_width = int(img_width * scale)
            scaled_height = int(img_height * scale)
            scaled_img = img.resize((scaled_width, scaled_height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(scaled_img)

            # 创建画布
            canvas = tk.Canvas(selector_window, highlightthickness=0)
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.pack(fill=tk.BOTH, expand=True)

            # 初始化变量
            rect_id = None
            start_x = start_y = end_x = end_y = 0
            scale_factor = img_width / scaled_width  # 实际像素与显示像素的比例

            # 鼠标事件处理
            def on_press(event):
                nonlocal start_x, start_y, rect_id
                start_x, start_y = event.x, event.y
                rect_id = canvas.create_rectangle(
                    start_x, start_y, start_x, start_y,
                    outline='red', width=2, tags="selection"
                )

            def on_drag(event):
                nonlocal end_x, end_y
                end_x, end_y = event.x, event.y
                canvas.coords(rect_id, start_x, start_y, end_x, end_y)


            def on_release(event):
                # 计算原始坐标
                raw_left = int(min(start_x, end_x) * scale_factor)
                raw_top = int(min(start_y, end_y) * scale_factor)
                raw_right = int(max(start_x, end_x) * scale_factor)
                raw_bottom = int(max(start_y, end_y) * scale_factor)

                # 验证选区有效性
                if (raw_right - raw_left < 10) or (raw_bottom - raw_top < 10):
                    messagebox.showwarning("无效选区", "选区尺寸过小")
                    selector_window.destroy()
                    return
                selector_window.withdraw()
                # 保存最终截图
                try:
                    cropped = img.crop((raw_left, raw_top, raw_right, raw_bottom))
                    final_filename = f"cropped_{timestamp}.png"
                    final_path = os.path.join(self.temp_dir, final_filename)
                    cropped.save(final_path)

                    # 更新数据
                    pron = self.current_data["pronunciations"][self.current_pronunciation_index]
                    pron["imported_source_path"] = final_path
                    self.update_thumbnail_panel()

                    # 显示相对路径
                    rel_path = os.path.relpath(final_path, start=os.getcwd())
                    messagebox.showinfo("截图成功", f"截图已保存到：\n{rel_path}")
                except Exception as save_error:
                    messagebox.showerror("保存失败", f"无法保存文件：{str(save_error)}")
                finally:
                    selector_window.destroy()
                    try:
                        os.remove(fullscreen_temp_path)  # 清理全屏临时文件
                    except Exception as clean_error:
                        print(f"清理临时文件失败：{str(clean_error)}")

            # 事件绑定
            canvas.bind("<ButtonPress-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
            selector_window.bind("<Escape>", lambda e: selector_window.destroy())

            # 维持图片引用
            canvas.image = photo
            selector_window.wait_window()

        except Exception as main_error:
            messagebox.showerror("严重错误", f"截图过程失败：{str(main_error)}")
        finally:
            self.root.deiconify()
            if 'fullscreen_temp_path' in locals():
                try:
                    if os.path.exists(fullscreen_temp_path):
                        os.remove(fullscreen_temp_path)
                except Exception as e:
                    print(f"最终清理失败：{str(e)}")

    def save_captured_area(self, start_point, end_point):

        screenshot = ImageGrab.grab(bbox=(*start_point, *end_point))
        if screenshot.mode in ('RGBA', 'LA'):
            screenshot = screenshot.convert('RGB')

        os.makedirs('temp', exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False,
            dir='temp'  # 新增目录指定参数
        )
        screenshot.save(temp_file, format="JPEG")
        temp_file.close()#close()方法用于关闭文件。关闭后文件不能再进行读写操作。为什么要关闭文件 a:关闭文件是为了释放资源，避免资源泄漏

        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        pron["imported_source_path"] = temp_file.name
        self.update_thumbnail_panel()  # 立即更新缩略图
        messagebox.showinfo(
            "截图成功",
            f"已捕获区域：{start_point} - {end_point}\n"
            f"临时文件：{temp_file.name}"
        )

    def create_form_panel(self):
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=20)

        # 创建画布和滚动条
        canvas = tk.Canvas(right_frame)
        scrollbar_y = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        scrollable_frame = tk.Frame(canvas)

        # 配置滚动区域
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 创建视口并配置滚动
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # 布局滚动条
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建表单内容
        self.create_annotation_info_section(scrollable_frame)
        self.create_pronunciation_section(scrollable_frame)
        self.create_pos_section(scrollable_frame)

        # 绑定滚轮滚动事件（跨平台支持）
        def on_mouse_wheel(event):
            # Windows/Linux
            if event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")

        # 绑定到画布和所有子部件
        def bind_wheel(widget):
            widget.bind("<MouseWheel>", on_mouse_wheel)  # Windows
            widget.bind("<Button-4>", on_mouse_wheel)  # Linux向上
            widget.bind("<Button-5>", on_mouse_wheel)  # Linux向下
            for child in widget.winfo_children():
                bind_wheel(child)

        # 应用绑定到整个滚动区域
        bind_wheel(canvas)
        bind_wheel(scrollable_frame)

        # 添加触摸板滚动支持（可选）
        canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta)), "units"))

    def create_annotation_info_section(self, parent):
        frame = tk.LabelFrame(parent, text="标注信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # 标注作者标签和输入框
        tk.Label(frame, text="标注作者:").grid(row=0, column=0, padx=10, pady=5, sticky="e")  # 右对齐，增加适当的内边距
        self.annotator_entry = tk.Entry(frame, width=5)  # 增加宽度以适应文本输入
        self.annotator_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")  # 左对齐，增加适当的内边距

        # 页码标签、输入框和“页”字
        tk.Label(frame, text="页码-第").grid(row=1, column=0, padx=10, pady=5, sticky="e")  # 右对齐
        self.page_num_entry = tk.Entry(frame, width=5)
        self.page_num_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')  # 左对齐
        tk.Label(frame, text="页").grid(row=1, column=2, padx=10, pady=5, sticky='w')

        # 字位置标签、输入框和“个字”字
        tk.Label(frame, text="字位置-第").grid(row=2, column=0, padx=10, pady=5, sticky="e")  # 右对齐
        self.word_num_entry = tk.Entry(frame, width=5)
        self.word_num_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")  # 左对齐
        tk.Label(frame, text="个字").grid(row=2, column=2, padx=10, pady=5, sticky="w")

    def create_pos_section(self, parent):
        frame = tk.LabelFrame(parent, text="词性信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        fields = [
            ("词性(中文):", "part_of_speech", 25),
            ("意思:", "meaning", 25),
            ("例句（壮文）:", "example_zhuang", 25),
            ("例句（中文）:", "example_chinese", 25)
        ]

        self.pos_entries = {}
        for i, (label, field, width) in enumerate(fields):
            tk.Label(frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            entry = tk.Entry(frame, width=width)
            entry.grid(row=i, column=1, columnspan=3, sticky='w', pady=2)
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
        tk.Button(example_ctrl_frame, text="添加新例句", command=self.add_new_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="上一条", command=self.previous_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="下一条", command=self.next_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="删除例句", command=self.delete_example).pack(side=tk.LEFT, padx=2)
        self.example_page = tk.Label(example_ctrl_frame, text="0/0")
        self.example_page.pack(side=tk.LEFT, padx=5)

    def create_pronunciation_section(self, parent):
        frame = tk.LabelFrame(parent, text="读音信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        row = 0
        tk.Label(frame, text="对应汉字:").grid(row=row, column=0, sticky='e', padx=5)
        self.chinese_char_entry = tk.Entry(frame, width=5)
        self.chinese_char_entry.grid(row=row, column=1, pady=2)#sticky是什么 a:

        row += 1
        tk.Label(frame, text="壮文音:").grid(row=row, column=0, sticky='e', padx=5)
        self.zh_wen_entry = tk.Entry(frame, width=5)
        self.zh_wen_entry.grid(row=row, column=1, pady=2)

        row += 1
        tk.Label(frame, text="国际音标:").grid(row=row, column=0, sticky='e', padx=5)
        self.ipa_entry = tk.Entry(frame, width=5)
        self.ipa_entry.grid(row=row, column=1, pady=2)

        row += 1
        self.dialect_var = tk.IntVar()
        dialect = tk.Checkbutton(frame, text="方言", onvalue=1, offvalue=0,variable=self.dialect_var,)
        dialect.grid(row=row, column=1)

        row += 1
        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=row, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新读音", command=self.add_new_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个", command=self.previous_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个", command=self.next_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="删除读音", command=self.delete_pronunciation).pack(side=tk.LEFT, padx=2)
        self.pronunciation_page = tk.Label(ctrl_frame, text="0/0")
        self.pronunciation_page.pack(side=tk.LEFT, padx=5)


    def load_current_image(self):
        try:
            if not self.image_files:
                return

            image_path = self.image_files[self.current_image_index]
            current_image_filename = os.path.basename(image_path)#basename() 方法返回文件名
            json_path = os.path.join("output", os.path.splitext(current_image_filename)[0] + ".json")

            new_data_template = {
                "image": current_image_filename,
                "annotator": self.current_data.get("annotator", ""),
                "page_info": self.current_data.get("page_info", {"page_num": "", "word_num": ""}),
                "simplified_Chinese_character": "",
                "pronunciations": [{
                    "zhuang_spelling": "",
                    "ipa": "",
                    "imported_source_path": "",  # 新增
                    "imported_image": [],  # 新增
                    "entries": [{
                        "part_of_speech": "",
                        "meaning": "",
                        "examples": [{"壮文": "", "中文": ""}]
                    }]
                }]
            }

            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)#load（）方法将json数据转换为python对象
                    if isinstance(data, list) and len(data) > 0:#isinstance()用法    a:isinstance() 函数来判断一个对象是否是一个已知的类型，类似 type()。
                        self.current_data = data[0]
                        if not self.current_data["pronunciations"]:
                            self.current_data["pronunciations"] = new_data_template["pronunciations"].copy()
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
            img = Image.open(image_path)#image.open()方法用于打开一个图片
            img.thumbnail((1000, 1000))#thumbnail()方法用于将图像调整为给定的尺寸。
            photo = ImageTk.PhotoImage(img)#ImageTk.PhotoImage()方法用于将图片转换为Tkinter的PhotoImage。

            self.img_canvas.image = photo
            self.img_canvas.delete("all")
            self.img_canvas.create_image(50, 50, image=photo)
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
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]#pron是什么意思 a:pron是pronunciation的缩写，意思是发音

        self.chinese_char_entry.delete(0, tk.END)
        self.chinese_char_entry.insert(0, self.current_data.get("simplified_Chinese_character", ""))

        self.zh_wen_entry.delete(0, tk.END)
        self.zh_wen_entry.insert(0, pron.get("zhuang_spelling", ""))
        self.ipa_entry.delete(0, tk.END)
        self.ipa_entry.insert(0, pron.get("ipa", ""))
        dialect_type = pron.get("dialect_type", 0)

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
            text=f"{self.current_example_index + 1}/{len(entry['examples'])}")

    def save_current_form(self):#保存当前表单
        self.current_data["annotator"] = self.annotator_entry.get()
        self.current_data["page_info"]["page_num"] = self.page_num_entry.get()
        self.current_data["page_info"]["word_num"] = self.word_num_entry.get()
        self.current_data["simplified_Chinese_character"] = self.chinese_char_entry.get()

        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        pron["zhuang_spelling"] = self.zh_wen_entry.get()
        pron["ipa"] = self.ipa_entry.get()
        pron["dialect_type"] = int(self.dialect_var.get())

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
        """
        提交数据函数，负责保存当前表单数据，清理旧图片，并将新图片移动到指定目录，
        更新数据记录，并将当前数据保存为JSON格式文件。
        """
        # 保存当前表单数据
        self.save_current_form()
        # 清理旧图片
        #self.cleanup_old_images()
        #self.current_data["imported_image"] = []  # 清空历史记录
        # 获取已导入的图片列表
        imported_images = []
        # 获取导入的源文件路径
        for pron in self.current_data["pronunciations"]:
            temp_source = pron.get("imported_source_path", "")
            if not temp_source:
                continue  # 没有需要处理的文件

            try:
                # 保存旧文件信息
                old_imported_images = pron.get("imported_image", [])
                old_source_path = pron.get("imported_source_path", "")

                # 创建输入目录
                input_dir = "output_image"
                os.makedirs(input_dir, exist_ok=True)

                # 生成时间戳（每个文件独立）
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

                # 获取读音名称并清理非法字符
                pron_name = pron.get("zhuang_spelling", "unnamed")
                pron_name_clean = re.sub(r'[\\/*?:"<>|]', "", pron_name)

                # 处理文件扩展名
                _, ext = os.path.splitext(temp_source)
                ext = ext if ext else ".jpg"

                # 生成新文件名和路径
                new_filename = f"{pron_name_clean}_{timestamp}{ext}"
                dest_path = os.path.join(input_dir, new_filename)

                # 移动或复制文件
                if temp_source.startswith(tempfile.gettempdir()):
                    shutil.move(temp_source, dest_path)
                else:
                    shutil.copyfile(temp_source, dest_path)

                # 更新数据
                pron["imported_source_path"] = dest_path
                pron["imported_image"] = [new_filename]

                # 删除旧文件（仅在output_image目录中的文件）
                # 1. 删除历史记录文件
                for old_file in old_imported_images:
                    old_path = os.path.join(input_dir, old_file)
                    if os.path.exists(old_path) and old_path != dest_path:
                        os.remove(old_path)
                        print(f"已删除历史文件: {old_path}")

                # 2. 删除旧的source文件（如果与新文件不同且在input目录）
                if (old_source_path.startswith(input_dir)
                        and old_source_path != dest_path
                        and os.path.exists(old_source_path)):
                    os.remove(old_source_path)
                    print(f"已删除旧源文件: {old_source_path}")

            except Exception as e:
                messagebox.showerror("错误",
                                     f"文件处理失败: {str(e)}\n"
                                     f"读音：{pron.get('zhuang_spelling', '未知')}\n"
                                     f"原路径：{temp_source}"
                                     )
                return

        # 确保输出目录存在
        os.makedirs("output", exist_ok=True)#os.makedirs() 方法用于递归创建目录。像 mkdir() 一样，但创建的所有中间级目录都将创建。
        # 构造JSON文件名
        filename = f"{os.path.splitext(self.current_data['image'])[0]}.json"
        full_path = os.path.join("output", filename)

        # 将当前数据保存为JSON格式文件
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump([self.current_data], f, ensure_ascii=False, indent=2)

        # 显示成功消息
        messagebox.showinfo("成功", f"数据已保存到\n{full_path}")
        """# 显示下一张图片
        self.show_next_image()"""

    def on_close(self):
        with open("config.json", "w") as f:
            json.dump({"last_index": self.current_image_index}, f)
        self.root.destroy()

    def delete_pronunciation(self):
        """
        删除当前读音及其所有词性信息。

        此函数首先通过messagebox确认用户是否确实希望删除当前读音及其所有关联的词性信息。
        如果用户确认删除，函数将保存当前表单数据，然后从数据中移除当前读音。

        在删除读音后，如果当前数据中的读音列表变为空，函数将自动创建一个新的空读音条目，
        以方便用户继续编辑。随后，函数重置当前读音、词条和示例的索引，并更新表单以反映
        数据的变更。
        """
        if messagebox.askyesno("确认", "确定要删除当前读音及其所有词性信息吗？"):
            original_index = self.current_pronunciation_index
            pron = self.current_data["pronunciations"][self.current_pronunciation_index]
            self.save_current_form()

            input_dir="output_image"
            old_path=pron.get("imported_source_path","")
            if os.path.exists(old_path):
                os.remove(old_path)
                print(f"已删除历史文件: {old_path}")
            del self.current_data["pronunciations"][original_index]    #del是什么意思 a:del是delete的缩写，意思是删除

            if not self.current_data["pronunciations"]:
                self.current_data["pronunciations"].append({
            "zhuang_spelling": "",
            "ipa": "",
            "imported_source_path": "",  # 新增
            "imported_image": [],  # 新增
            "dialect_type": 0,
            "entries": [{
                "part_of_speech": "",
                "meaning": "",
                "examples": [{"壮文": "", "中文": ""}]
            }]
        })

            self.current_pronunciation_index = min(original_index, len(self.current_data["pronunciations"]) - 1)
            self.current_entry_index = 0 #为什么要置0 a:因为删除了当前读音，所以要重新从0开始q:从1开始会怎么样 a:会报错，因为删除了当前读音，所以当前读音的索引就是0
            self.current_example_index = 0
            self.update_form()
            self.update_thumbnail_panel()

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
            "imported_source_path": "",  # 新增
            "imported_image": [],  # 新增
            "dialect_type": 0,
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
        self.update_thumbnail_panel()

    def previous_pronunciation(self):
        if self.current_pronunciation_index > 0:
            self.save_current_form()
            self.current_pronunciation_index -= 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()
            self.update_thumbnail_panel()

    def next_pronunciation(self):
        if self.current_pronunciation_index < len(self.current_data["pronunciations"]) - 1:
            self.save_current_form()
            self.current_pronunciation_index += 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()
            self.update_thumbnail_panel()

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
            pron = self.current_data["pronunciations"][self.current_pronunciation_index]
            pron["imported_source_path"] = file_path
            self.update_thumbnail_panel()  # 立即更新缩略图
            messagebox.showinfo("导入成功", f"已选择图片: {os.path.basename(file_path)}")

    """
    清理旧文件
    def cleanup_old_images(self):
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if not pron.get("imported_image"):
            return

        input_dir = "output_image"
        for old_file in pron["imported_image"]:
            old_path = os.path.join(input_dir, old_file)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
                    print(f"已删除旧图片: {old_path}")
            except Exception as e:
                print(f"删除旧图片失败: {str(e)}")"""

    def show_enlarged_image(self, image_path):
        """显示放大后的图片"""
        try:
            win = tk.Toplevel(self.root)
            win.title("放大预览")

            img = Image.open(image_path)
            # 根据屏幕尺寸调整图片大小
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            img.thumbnail((screen_width - 100, screen_height - 100))

            photo = ImageTk.PhotoImage(img)
            label = tk.Label(win, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)

            # 双击关闭窗口
            label.bind("<Double-Button-1>", lambda e: win.destroy())
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片：{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()