import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import glob
import json
import shutil
from datetime import datetime
import re


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("字典json生成")

        # 初始化数据结构（新增imported_image字段）
        self.current_data = {
            "image": "",
            "annotator": "",
            "page_info": {
                "page_num": "",
                "word_num": ""
            },
            "imported_source_path": "",  # 新增导入图片路径
            "imported_image": [],       # 新增导入图片数组
            "pronunciations": []
        }

        # 加载所有图片文件
        image_dir = "image"
        output_dir = "output"
        image_extensions = ["*.png", "*.jpg", "*.jpeg"]
        all_images = []
        for ext in image_extensions:
            all_images.extend(glob.glob(os.path.join(image_dir, ext)))
        self.image_files = sorted(all_images)

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

        nav_frame = tk.Frame(left_frame)
        nav_frame.pack(pady=10)

        # 新增导入按钮
        tk.Button(nav_frame, text="导入图片", width=8, command=self.import_image).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="上一页", width=8, command=self.show_previous_image).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="下一页", width=8, command=self.show_next_image).pack(side=tk.LEFT, padx=2)

        self.page_entry = tk.Entry(nav_frame, width=6)
        self.page_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="跳转", width=6, command=self.jump_to_page).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_frame, text="提交", width=8, bg='#4CAF50', command=self.submit_data).pack(side=tk.LEFT, padx=5)


    def create_form_panel(self):
        right_frame = tk.Frame(self.main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)

        self.create_annotation_info_section(right_frame)
        self.create_pronunciation_section(right_frame)
        self.create_pos_section(right_frame)

    def create_annotation_info_section(self, parent):
        """新增的标注信息区域"""
        frame = tk.LabelFrame(parent, text="标注信息", font=("微软雅黑", 10), padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)

        # 标注作者
        tk.Label(frame, text="标注作者:").grid(row=0, column=0, sticky='e', padx=5)
        self.annotator_entry = tk.Entry(frame, width=25)
        self.annotator_entry.grid(row=0, column=1, pady=2, sticky='w')

        # 页码信息
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

            # 加载现有数据时保留导入信息
            original_import = {
                "source": self.current_data.get("imported_source_path", ""),
                "images": self.current_data.get("imported_image", [])
            }

            # 尝试加载现有标注数据
            json_path = os.path.join("output", os.path.splitext(self.current_data["image"])[0] + ".json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.current_data = data[0]
                        # 保留原有标注信息
                        original_annotator = self.current_data.get("annotator", "")
                        original_page_info = self.current_data.get("page_info", {})

                        self.current_data = data[0]

                        # 保持当前标注信息（如果新加载的数据没有这些字段）
                        self.current_data.setdefault("annotator", original_annotator)
                        self.current_data.setdefault("page_info", original_page_info)

                        self.current_data["imported_source_path"] = original_import["source"]
                        self.current_data["imported_image"] = original_import["images"]
            else:
                # 初始化时保留现有标注信息
                original_annotator = self.current_data.get("annotator", "")
                original_page_info = self.current_data.get("page_info", {})
                self.initialize_data()
                self.current_data["annotator"] = original_annotator
                self.current_data["page_info"] = original_page_info

            # 更新标注信息字段
            self.annotator_entry.delete(0, tk.END)
            self.annotator_entry.insert(0, self.current_data.get("annotator", ""))

            self.page_num_entry.delete(0, tk.END)
            self.page_num_entry.insert(0, self.current_data["page_info"].get("page_num", ""))

            self.word_num_entry.delete(0, tk.END)
            self.word_num_entry.insert(0, self.current_data["page_info"].get("word_num", ""))

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
        # 保存标注信息
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
            original_index = self.current_pronunciation_index

            # 先保存数据再删除
            self.save_current_form()
            del self.current_data["pronunciations"][original_index]

            # 处理空列表情况
            if not self.current_data["pronunciations"]:
                self.current_data["pronunciations"].append({
                    "zhuang_spelling": "",
                    "ipa": "",
                    "entries": [{"part_of_speech": "", "meaning": "", "examples": [{"壮文": "", "中文": ""}]}]
                })

            # 更新索引（优先保持当前位置）
            new_total = len(self.current_data["pronunciations"])
            self.current_pronunciation_index = min(original_index, new_total - 1)

            # 重置下级索引并更新界面
            self.current_entry_index = 0
            self.current_example_index = 0
            self.update_form()  # 改为直接更新表单

            # 更新标题显示
            self.title_label.config(
                text=f"{self.current_data['image']} (第{self.current_image_index + 1}页/共{len(self.image_files)}页)")

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
        """添加新读音时保留标注信息"""
        self.save_current_form()

        # 保存当前标注信息
        current_annotator = self.current_data["annotator"]
        current_page_info = self.current_data["page_info"].copy()

        # 创建新读音条目
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

        # 恢复标注信息
        self.current_data["annotator"] = current_annotator
        self.current_data["page_info"] = current_page_info

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
        """处理图片导入"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的图片",
            # 修改文件类型参数格式
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ]
        )

        if file_path:
            self.current_data["imported_source_path"] = file_path
            messagebox.showinfo("导入成功", f"已选择图片: {os.path.basename(file_path)}")

    def submit_data(self):
        """处理提交时图片复制"""
        self.save_current_form()

        # 处理导入图片的复制
        if self.current_data["imported_source_path"]:
            source_path = self.current_data["imported_source_path"]
            input_dir = "input_image"
            os.makedirs(input_dir, exist_ok=True)

            # 生成统一时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            imported_images = []

            try:
                # 遍历所有读音生成副本
                for pron in self.current_data["pronunciations"]:
                    # 清理文件名非法字符
                    pron_name = re.sub(r'[\\/*?:"<>|]', "", pron.get("zhuang_spelling", "unnamed"))
                    ext = os.path.splitext(source_path)[1]
                    filename = f"{pron_name}_{timestamp}{ext}"
                    dest_path = os.path.join(input_dir, filename)

                    # 复制文件
                    shutil.copyfile(source_path, dest_path)
                    imported_images.append(filename)

                # 更新导入图片记录
                self.current_data["imported_image"] = imported_images
                # 清空导入路径防止重复处理
                self.current_data["imported_source_path"] = ""

            except Exception as e:
                messagebox.showerror("错误", f"文件复制失败: {str(e)}")
                return

        # 保存数据
        os.makedirs("output", exist_ok=True)
        filename = f"{os.path.splitext(self.current_data['image'])[0]}.json"
        full_path = os.path.join("output", filename)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump([self.current_data], f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"数据已保存到\n{full_path}")
        self.show_next_image()

    def copy_imported_image(self, src_path):
        """复制导入的图片到input_image目录"""
        input_dir = "input_image"
        os.makedirs(input_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        # 为每个读音生成图片副本
        for idx, pron in enumerate(self.current_data["pronunciations"]):
            # 生成文件名
            pron_name = pron.get("zhuang_spelling", "").strip()
            if not pron_name:
                pron_name = f"pron_{idx + 1}"

            # 清理非法字符
            pron_name = "".join(c for c in pron_name if c.isalnum() or c in ('_', '-')).rstrip()
            ext = os.path.splitext(src_path)[1]
            base_name = f"{pron_name}_{timestamp}{ext}"

            # 处理重复文件名
            target_path = os.path.join(input_dir, base_name)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(input_dir, f"{pron_name}_{timestamp}_{counter}{ext}")
                counter += 1

            # 执行复制
            try:
                shutil.copy(src_path, target_path)
                print(f"已保存导入图片: {target_path}")
            except Exception as e:
                print(f"图片保存失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()