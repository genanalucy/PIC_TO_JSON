"""
界面组件模块
包含所有UI界面的创建和布局功能
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os


class UIComponents:
    def __init__(self, app_instance):
        self.app = app_instance
        
    def create_main_widgets(self):
        """创建主要界面组件"""
        self.app.main_frame = tk.Frame(self.app.root)
        self.app.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 左侧图片区域
        self.create_image_panel()
        # 右侧表单区域
        self.create_form_panel()

    def create_image_panel(self):
        """创建左侧图片显示面板"""
        left_frame = tk.Frame(self.app.main_frame)
        left_frame.pack(side=tk.TOP, fill=tk.Y)

        self.app.title_label = tk.Label(left_frame, text="", font=("微软雅黑", 12))
        self.app.title_label.pack(pady=5)

        self.app.img_canvas = tk.Canvas(left_frame, width=100, height=100, bg='#e0e0e0')
        self.app.img_canvas.pack()

        # 缩略图容器
        self.app.thumbnail_frame = tk.Frame(left_frame, height=80)
        self.app.thumbnail_frame.pack(pady=5, fill=tk.X)
        self.app.thumbnail_labels = []
        self.app.thumbnail_images = []

        nav_frame1 = tk.Frame(left_frame)
        nav_frame1.pack(pady=5)

        first_row_btns = [
            ("上一页", self.app.show_previous_image),
            ("下一页", self.app.show_next_image),
            ("提交", self.app.submit_data)
        ]

        for text, cmd in first_row_btns:
            btn = tk.Button(nav_frame1, text=text, width=6, command=cmd)
            if text == "提交":
                btn.config(width=8, bg='#4CAF50')
            btn.pack(side=tk.LEFT, padx=2)

        self.app.page_entry = tk.Entry(nav_frame1, width=6)
        self.app.page_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame1, text="跳转", width=6, command=self.app.jump_to_page).pack(side=tk.LEFT, padx=2)

        # 第二行按钮
        nav_frame2 = tk.Frame(left_frame)
        nav_frame2.pack(pady=5)

        second_row_btns = [
            ("导入图片", self.import_image),
            ("实时截图", self.app.image_processor.capture_screen)
        ]

        for text, cmd in second_row_btns:
            tk.Button(nav_frame2, text=text, width=8, command=cmd).pack(side=tk.LEFT, padx=2)

    def create_form_panel(self):
        """创建右侧表单面板"""
        right_frame = tk.Frame(self.app.main_frame)
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

        # 绑定滚轮滚动事件
        self._bind_scroll_events(canvas, scrollable_frame)

    def _bind_scroll_events(self, canvas, scrollable_frame):
        """绑定滚轮滚动事件"""
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

        # 添加触摸板滚动支持
        canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta)), "units"))

    def create_annotation_info_section(self, parent):
        """创建标注信息区域"""
        frame = tk.LabelFrame(parent, text="标注信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # 标注作者标签和输入框
        tk.Label(frame, text="标注作者:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.app.annotator_entry = tk.Entry(frame, width=20)
        self.app.annotator_entry.grid(row=0, column=1, padx=10, pady=5, sticky="we", columnspan=2)

        # 页码标签、输入框和"页"字
        tk.Label(frame, text="页码-第").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.app.page_num_entry = tk.Entry(frame, width=20)
        self.app.page_num_entry.grid(row=1, column=1, padx=10, pady=5, sticky='w')
        tk.Label(frame, text="页").grid(row=1, column=2, padx=10, pady=5, sticky='w')

        # 字位置标签、输入框和"个字"字
        tk.Label(frame, text="字位置-第").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.app.word_num_entry = tk.Entry(frame, width=20)
        self.app.word_num_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        tk.Label(frame, text="个字").grid(row=2, column=2, padx=10, pady=5, sticky="w")

    def create_pronunciation_section(self, parent):
        """创建读音信息区域"""
        frame = tk.LabelFrame(parent, text="读音信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        row = 0
        tk.Label(frame, text="对应汉字:").grid(row=row, column=0, sticky='e', padx=5)
        self.app.chinese_char_entry = tk.Entry(frame, width=10)
        self.app.chinese_char_entry.grid(row=row, column=1, pady=2)

        row += 1
        tk.Label(frame, text="壮文音:").grid(row=row, column=0, sticky='e', padx=5)
        self.app.zh_wen_entry = tk.Entry(frame, width=20)
        self.app.zh_wen_entry.grid(row=row, column=1, pady=2)

        row += 1
        tk.Label(frame, text="国际音标:").grid(row=row, column=0, sticky='e', padx=5)
        self.app.ipa_entry = tk.Entry(frame, width=20)
        self.app.ipa_entry.grid(row=row, column=1, pady=2)

        row += 1
        self.app.dialect_var = tk.IntVar()
        dialect = tk.Checkbutton(frame, text="方言", onvalue=1, offvalue=0, variable=self.app.dialect_var)
        dialect.grid(row=row, column=1)

        row += 1
        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=row, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新读音", command=self.app.add_new_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个", command=self.app.previous_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个", command=self.app.next_pronunciation).pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="删除读音", command=self.app.delete_pronunciation).pack(side=tk.LEFT, padx=2)
        self.app.pronunciation_page = tk.Label(ctrl_frame, text="0/0")
        self.app.pronunciation_page.pack(side=tk.LEFT, padx=5)

    def create_pos_section(self, parent):
        """创建词性信息区域"""
        frame = tk.LabelFrame(parent, text="词性信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 词性和意思仍用Entry，例句用Text
        fields = [
            ("词性(中文):", "part_of_speech", 25, "entry"),
            ("意思:", "meaning", 25, "entry"),
            ("例句（壮文）:", "example_zhuang", 40, "text"),
            ("例句（中文）:", "example_chinese", 40, "text")
        ]

        self.app.pos_entries = {}
        for i, (label, field, width, widget_type) in enumerate(fields):
            tk.Label(frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            if widget_type == "entry":
                entry = tk.Entry(frame, width=width)
                entry.grid(row=i, column=1, columnspan=3, sticky='w', pady=2)
                self.app.pos_entries[field] = entry
            else:
                text = tk.Text(frame, width=width, height=3, wrap=tk.WORD)
                text.grid(row=i, column=1, columnspan=3, sticky='w', pady=2)
                self.app.pos_entries[field] = text

        # 词性控制按钮
        pos_ctrl_frame = tk.Frame(frame)
        pos_ctrl_frame.grid(row=4, column=0, columnspan=4, pady=5)
        tk.Button(pos_ctrl_frame, text="添加新词性", command=self.app.add_new_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="上一个", command=self.app.previous_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="下一个", command=self.app.next_entry).pack(side=tk.LEFT, padx=2)
        tk.Button(pos_ctrl_frame, text="删除词性", command=self.app.delete_entry).pack(side=tk.LEFT, padx=2)
        self.app.pos_page = tk.Label(pos_ctrl_frame, text="0/0")
        self.app.pos_page.pack(side=tk.LEFT, padx=5)

        # 例句控制按钮
        example_ctrl_frame = tk.Frame(frame)
        example_ctrl_frame.grid(row=5, column=0, columnspan=4, pady=5)
        tk.Button(example_ctrl_frame, text="添加新例句", command=self.app.add_new_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="上一条", command=self.app.previous_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="下一条", command=self.app.next_example).pack(side=tk.LEFT, padx=2)
        tk.Button(example_ctrl_frame, text="删除例句", command=self.app.delete_example).pack(side=tk.LEFT, padx=2)
        self.app.example_page = tk.Label(example_ctrl_frame, text="0/0")
        self.app.example_page.pack(side=tk.LEFT, padx=5)

    def show_empty_message(self):
        """显示空消息"""
        self.app.img_canvas.delete("all")
        self.app.img_canvas.create_text(250, 250, text="找不到图片,请在目录中创建image文件夹", fill="red")
        self.app.title_label.config(text="错误状态")

    def import_image(self):
        """导入图片功能"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的图片",
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            pron = self.app.current_data["pronunciations"][self.app.current_pronunciation_index]
            pron["imported_source_path"] = file_path
            self.app.image_processor.update_thumbnail_panel()  # 立即更新缩略图
            messagebox.showinfo("导入成功", f"已选择图片: {os.path.basename(file_path)}")

    def update_title_display(self, current_index, total_images, image_name):
        """更新标题显示"""
        self.app.title_label.config(
            text=f"{image_name} (第{current_index + 1}页/共{total_images}页)")
