"""
主程序入口文件
整合所有模块，提供应用程序主要逻辑
"""
"""
0319(2)
1.修复 outoflist
2.修复方言按钮全选问题
3.标注作者逻辑更新
0320
1.修改截图保存逻辑,目前支持同音截图
2.文件排序逻辑更新,现在会先根据页数排序,页数相同再根据字数排序
0701
1.增加校对功能：增加三个字段proofread、proofread_man、is_wrong
2.增加作者框的显示长度
3.例句实现多行显示

"""
import tkinter as tk
from tkinter import messagebox
import os

from image_processor import ImageProcessor
from ui_components import UIComponents
from data_manager import DataManager


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("600x1400")
        self.root.title("字典json生成0320v2.0.5")

        # 初始化
        self.current_data = {
            "image": "",
            "annotator": "",
            "page_info": {
                "page_num": "",
                "word_num": ""
            },
            "simplified_Chinese_character": "",
            "imported_source_path": "",
            "imported_image": [],
            "pronunciations": []
        }


        self.image_processor = ImageProcessor(self)
        self.ui_components = UIComponents(self)
        self.data_manager = DataManager(self)

        self.current_image_index = 0
        self.current_pronunciation_index = 0
        self.current_entry_index = 0
        self.current_example_index = 0

        # 加载图片文件和配置
        self.image_files = self.data_manager.load_image_files()
        last_index = self.data_manager.load_config()
        if 0 <= last_index < len(self.image_files):
            self.current_image_index = last_index

        # 界面
        self.create_widgets()

        # 加载当前图片
        if self.image_files:
            self.load_current_image()
        else:
            self.ui_components.show_empty_message()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        """创建界面组件"""
        self.ui_components.create_main_widgets()

    def load_current_image(self):
        """加载当前图片"""
        try:
            if not self.image_files:
                return

            image_path = self.image_files[self.current_image_index]
            
            # 加载数据
            self.current_data = self.data_manager.load_current_image_data(image_path)

            # 重置导航索引
            self.current_pronunciation_index = 0
            self.current_entry_index = 0
            self.current_example_index = 0

            # 加载和显示图片
            if self.image_processor.load_and_display_image(image_path):
                # 更新标题
                self.ui_components.update_title_display(
                    self.current_image_index,
                    len(self.image_files),
                    self.current_data['image']
                )

                # 更新缩略图
                self.image_processor.update_thumbnail_panel()

                # 更新表单
                self.data_manager.update_form_fields()

        except Exception as e:
            print(f"加载图片错误: {str(e)}")

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

        self.data_manager.submit_data()

    def on_close(self):
        """程序关闭时保存配置"""
        self.data_manager.save_config(self.current_image_index)
        self.root.destroy()

    # 读音相关操作
    def add_new_pronunciation(self):
        """添加新读音"""
        self.data_manager.save_current_form_data()
        new_index = self.data_manager.add_new_pronunciation()
        self.current_pronunciation_index = new_index
        self.current_entry_index = 0
        self.current_example_index = 0
        self.data_manager.update_form_fields()
        self.image_processor.update_thumbnail_panel()

    def previous_pronunciation(self):
        """上一个读音"""
        if self.current_pronunciation_index > 0:
            self.data_manager.save_current_form_data()
            self.current_pronunciation_index -= 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.data_manager.update_form_fields()
            self.image_processor.update_thumbnail_panel()

    def next_pronunciation(self):
        """下一个读音"""
        if self.current_pronunciation_index < len(self.current_data["pronunciations"]) - 1:
            self.data_manager.save_current_form_data()
            self.current_pronunciation_index += 1
            self.current_entry_index = 0
            self.current_example_index = 0
            self.data_manager.update_form_fields()
            self.image_processor.update_thumbnail_panel()

    def delete_pronunciation(self):
        """删除当前读音"""
        if messagebox.askyesno("确认", "确定要删除当前读音及其所有词性信息吗？"):
            original_index = self.current_pronunciation_index
            self.data_manager.save_current_form_data()
            
            self.data_manager.delete_pronunciation_data(original_index)
            
            self.current_pronunciation_index = min(original_index, len(self.current_data["pronunciations"]) - 1)
            self.current_entry_index = 0
            self.current_example_index = 0
            self.data_manager.update_form_fields()
            self.image_processor.update_thumbnail_panel()

    # 词性相关操作
    def add_new_entry(self):
        """添加新词性"""
        self.data_manager.save_current_form_data()
        new_index = self.data_manager.add_new_entry(self.current_pronunciation_index)
        self.current_entry_index = new_index
        self.current_example_index = 0
        self.data_manager.update_form_fields()

    def previous_entry(self):
        """上一个词性"""
        if self.current_entry_index > 0:
            self.data_manager.save_current_form_data()
            self.current_entry_index -= 1
            self.current_example_index = 0
            self.data_manager.update_form_fields()

    def next_entry(self):
        """下一个词性"""
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if self.current_entry_index < len(pron["entries"]) - 1:
            self.data_manager.save_current_form_data()
            self.current_entry_index += 1
            self.current_example_index = 0
            self.data_manager.update_form_fields()

    def delete_entry(self):
        """删除词性"""
        pron = self.current_data["pronunciations"][self.current_pronunciation_index]
        if len(pron["entries"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前词性及其所有例句吗？"):
                self.data_manager.save_current_form_data()
                if self.data_manager.delete_entry(self.current_pronunciation_index, self.current_entry_index):
                    self.current_entry_index = max(0, self.current_entry_index - 1)
                    self.current_example_index = 0
                    self.data_manager.update_form_fields()

    # 例句相关操作
    def add_new_example(self):
        """添加新例句"""
        self.data_manager.save_current_form_data()
        new_index = self.data_manager.add_new_example(
            self.current_pronunciation_index, 
            self.current_entry_index
        )
        self.current_example_index = new_index
        self.data_manager.update_form_fields()

    def previous_example(self):
        """上一条例句"""
        if self.current_example_index > 0:
            self.data_manager.save_current_form_data()
            self.current_example_index -= 1
            self.data_manager.update_form_fields()

    def next_example(self):
        """下一条例句"""
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][
            self.current_entry_index]
        if self.current_example_index < len(entry["examples"]) - 1:
            self.data_manager.save_current_form_data()
            self.current_example_index += 1
            self.data_manager.update_form_fields()

    def delete_example(self):
        """删除例句"""
        entry = self.current_data["pronunciations"][self.current_pronunciation_index]["entries"][
            self.current_entry_index]
        if len(entry["examples"]) > 1:
            if messagebox.askyesno("确认", "确定要删除当前例句吗？"):
                self.data_manager.save_current_form_data()
                if self.data_manager.delete_example(
                    self.current_pronunciation_index, 
                    self.current_entry_index, 
                    self.current_example_index
                ):
                    self.current_example_index = max(0, self.current_example_index - 1)
                    self.data_manager.update_form_fields()

    def proofread_action(self):
        """校对按钮回调"""
        import json
        import shutil
        # 1. 校对人不能为空
        proofread_man = self.proofread_man_entry.get().strip()
        if not proofread_man:
            messagebox.showerror("提示", "校对人名字不能为空！")
            return
        # 2. 保存当前表单数据
        self.data_manager.save_current_form_data()
        # 3. 读取output原始json
        image_path = self.image_files[self.current_image_index]
        json_name = os.path.splitext(os.path.basename(image_path))[0] + ".json"
        output_json_path = os.path.join("output", json_name)
        proofread_json_path = os.path.join("proofread_file", json_name)
        # 4. 读取原始数据
        if os.path.exists(output_json_path):
            with open(output_json_path, "r", encoding="utf-8") as f:
                try:
                    old_data = json.load(f)
                except Exception:
                    old_data = []
        else:
            old_data = []
        # 5. 获取当前数据副本
        new_data = [dict(self.current_data)]
        # 6. 增加校对字段
        new_data[0]["proofread"] = "1"
        new_data[0]["proofread_man"] = proofread_man
        # 7. 判断内容是否有更改
        import copy
        def _remove_proof_fields(d):
            d = copy.deepcopy(d)
            d.pop("proofread", None)
            d.pop("proofread_man", None)
            d.pop("is_wrong", None)
            return d
        is_wrong = "0"
        if old_data:
            import json as _json
            old_clean = _remove_proof_fields(old_data[0])
            new_clean = _remove_proof_fields(new_data[0])
            if _json.dumps(old_clean, sort_keys=True, ensure_ascii=False) != _json.dumps(new_clean, sort_keys=True, ensure_ascii=False):
                is_wrong = "1"
        else:
            is_wrong = "1"
        new_data[0]["is_wrong"] = is_wrong
        # 8. 保存到proofread_file
        os.makedirs("proofread_file", exist_ok=True)
        with open(proofread_json_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("提示", "校对完成，文件已保存到proofread_file！")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()
