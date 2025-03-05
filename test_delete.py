import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import glob
import json


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字典json生成")

        # 初始化数据结构
        self.current_data = {
            "image": "",
            "pronunciations": []
        }

        # 加载所有图片文件（包含已处理）
        image_dir = "image"
        output_dir = "output"
        image_extensions = ["*.png", "*.jpg", "*.jpeg"]
        all_images = []
        for ext in image_extensions:
            all_images.extend(glob.glob(os.path.join(image_dir, ext)))# 获取所有图片文件
        self.image_files = sorted(all_images)# 什么顺序

        # 加载配置文件
        config_path = "config.json"
        self.current_image_index = 0  # 默认索引
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

        nav_frame = tk.Frame(left_frame)
        nav_frame.pack(pady=10)

        tk.Button(nav_frame, text="上一页", width=8, command=self.show_previous_image).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="下一页", width=8, command=self.show_next_image).pack(side=tk.LEFT, padx=2)

        self.page_entry = tk.Entry(nav_frame, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="跳转", width=6, command=self.jump_to_page).pack(side=tk.LEFT, padx=2)

        tk.Button(nav_frame, text="提交", width=8, bg='#4CAF50', command=self.submit_data).pack(side=tk.LEFT, padx=5)

    def create_form_panel(self):
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        self.create_pronunciation_section(right_frame)
        self.create_pos_section(right_frame)

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

    def initialize_data(self):
        self.current_data["pronunciations"] = [{
            "zhuang_spelling": "",
            "ipa": "",
            "entries": [{
                "part_of_speech": "",
                "meaning": "",
                "examples": [{"壮文": "", "中文": ""}]
            }]
        }]

    def load_current_image(self):# 加载当前图片
        try:
            if not self.image_files:
                return

            image_path = self.image_files[self.current_image_index]
            self.current_data["image"] = os.path.basename(image_path)

            # 尝试加载现有标注数据
            json_path = os.path.join("output", os.path.splitext(self.current_data["image"])[0] + ".json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.current_data = data[0]
            else:
                self.initialize_data()

            # 加载图片
            img = Image.open(image_path)
            img.thumbnail((1000, 1000))# img.th
            photo = ImageTk.PhotoImage(img)# 创建一个ImageTk.PhotoImage对象

            self.img_canvas.image = photo
            self.img_canvas.delete("all")
            self.img_canvas.create_image(100, 100   , image=photo)# 将图片居中显示 250是什么意思 250是图片的中心点
            self.title_label.config(
                text=f"{self.current_data['image']} (第{self.current_image_index + 1}页/共{len(self.image_files)}页)")

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

        # 更新读音字段
        self.zh_wen_entry.delete(0, tk.END)
        self.zh_wen_entry.insert(0, pron.get("zhuang_spelling", ""))
        self.ipa_entry.delete(0, tk.END)
        self.ipa_entry.insert(0, pron.get("ipa", ""))

        # 更新词性字段
        entry = pron["entries"][self.current_entry_index]
        self.pos_entries["part_of_speech"].delete(0, tk.END)
        self.pos_entries["part_of_speech"].insert(0, entry.get("part_of_speech", ""))
        self.pos_entries["meaning"].delete(0, tk.END)
        self.pos_entries["meaning"].insert(0, entry.get("meaning", ""))

        # 更新例句字段
        example = entry["examples"][self.current_example_index]
        self.pos_entries["example_zhuang"].delete(0, tk.END)
        self.pos_entries["example_zhuang"].insert(0, example.get("壮文", ""))
        self.pos_entries["example_chinese"].delete(0, tk.END)
        self.pos_entries["example_chinese"].insert(0, example.get("中文", ""))

        # 更新页码显示
        self.pronunciation_page.config(
            text=f"{self.current_pronunciation_index + 1}/{len(self.current_data['pronunciations'])}")
        self.pos_page.config(
            text=f"{self.current_entry_index + 1}/{len(pron['entries'])}")
        self.example_page.config(
            text=f"例句 {self.current_example_index + 1}/{len(entry['examples'])}")

    def save_current_form(self):
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
        os.makedirs("output", exist_ok=True)
        filename = f"{os.path.splitext(self.current_data['image'])[0]}.json"
        full_path = os.path.join("output", filename)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump([self.current_data], f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"数据已保存到\n{full_path}")
        self.show_next_image()

    def on_close(self):
        # 保存当前索引
        config = {
            "last_index": self.current_image_index
        }
        with open("config.json", "w") as f:
            json.dump(config, f)
        self.root.destroy()

    def delete_pronunciation(self):
        if messagebox.askyesno("确认", "确定要删除当前读音及其所有词性信息吗？"):
            self.save_current_form()
            del self.current_data["pronunciations"][self.current_pronunciation_index]
            if not self.current_data["pronunciations"]:
                self.current_data["pronunciations"].append({
                    "zhuang_spelling": "",
                    "ipa": "",
                    "entries": [{"part_of_speech": "", "meaning": "", "examples": [{"壮文": "", "中文": ""}]}]
                })
            self.current_pronunciation_index = min(self.current_pronunciation_index,
                                                 len(self.current_data["pronunciations"]) - 1)
            self.load_current_image()

    def delete_entry(self):
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if len(pron["entries"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前词性及其所有例句吗？"):
                self.save_current_form()
                del pron["entries"][self.current_entry_index]
                self.current_entry_index = max(0, self.current_entry_index - 1)
                self.update_form()

    def delete_example(self):
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][self.current_entry_index]
        if len(entry["examples"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前例句吗？"):
                self.save_current_form()
                del entry["examples"][self.current_example_index]
                self.current_example_index = max(0, self.current_example_index - 1)
                self.update_form()

    def add_new_pronunciation(self):
        self.save_current_form()
        self.current_data["pronunciations"].append({
            "zhuang_spelling": "",
            "ipa": "",
            "entries": [{
                "part_of_speech": "",
                "meaning": "",
                "examples": [{"壮文": "", "中文": ""}]
            }]
        })
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


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()