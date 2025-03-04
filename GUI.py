import tkinter as tk
from PIL import Image, ImageTk


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片浏览器")
        self.create_widgets()
        self.setup_initial_state()

    def create_widgets(self):
        """创建主界面组件"""
        # 主容器
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        # 左侧图片区域
        self.create_image_panel()
        # 右侧表单区域
        self.create_form_panel()

    def create_image_panel(self):
        """图片显示区域"""
        left_frame = tk.Frame(self.main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # 图片标题
        self.title_label = tk.Label(left_frame, text="", font=("微软雅黑", 12))
        self.title_label.pack(pady=5)

        # 图片画布
        self.img_canvas = tk.Canvas(left_frame, width=500, height=500, bg='#e0e0e0')
        self.img_canvas.pack()

        # 导航按钮
        nav_frame = tk.Frame(left_frame)
        nav_frame.pack(pady=10)
        tk.Button(nav_frame, text="上一页", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="下一页", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="提交", width=10, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)

    def create_form_panel(self):
        """右侧表单区域"""
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        # 读音信息
        self.create_pronunciation_section(right_frame)
        # 词性信息
        self.create_pos_section(right_frame)

    def create_pronunciation_section(self, parent):
        """读音输入部分"""
        frame = tk.LabelFrame(parent, text="读音信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # 输入字段
        tk.Label(frame, text="壮文音:").grid(row=0, column=0, sticky='e', padx=5)
        self.zh_wen_entry = tk.Entry(frame, width=25)
        self.zh_wen_entry.grid(row=0, column=1, pady=2)

        tk.Label(frame, text="国际音标:").grid(row=0, column=2, sticky='e', padx=5)
        self.ipa_entry = tk.Entry(frame, width=25)
        self.ipa_entry.grid(row=0, column=3, pady=2)

        # 导航控制
        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=1, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新读音").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个").pack(side=tk.LEFT, padx=2)
        self.pronunciation_page = tk.Label(ctrl_frame, text="0/0")
        self.pronunciation_page.pack(side=tk.LEFT, padx=5)

    def create_pos_section(self, parent):
        """词性信息部分"""
        frame = tk.LabelFrame(parent, text="词性信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 输入字段
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

        # 导航控制
        ctrl_frame = tk.Frame(frame)
        ctrl_frame.grid(row=4, column=0, columnspan=4, pady=5)
        tk.Button(ctrl_frame, text="添加新词性").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="上一个").pack(side=tk.LEFT, padx=2)
        tk.Button(ctrl_frame, text="下一个").pack(side=tk.LEFT, padx=2)
        self.pos_page = tk.Label(ctrl_frame, text="0/0")
        self.pos_page.pack(side=tk.LEFT, padx=5)

    def setup_initial_state(self):
        """初始化界面状态"""
        # 图片占位
        self.img_canvas.create_text(250, 250, text="图片显示区域",
                                    font=("微软雅黑", 14), fill="#666")
        self.title_label.config(text="未加载图片")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()