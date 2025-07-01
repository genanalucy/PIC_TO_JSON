"""
数据管理模块
包含表单数据处理、JSON文件操作、图片文件管理等功能
"""

import os
import json
import glob
import shutil
import re
from datetime import datetime
from tkinter import messagebox


class DataManager:
    def __init__(self, app_instance):
        self.app = app_instance
        
    def load_image_files(self):
        """加载图片文件列表"""
        image_dir = "image"
        image_extensions = ["*.png", "*.jpg", "*.jpeg"]
        from image_processor import ImageProcessor
        return sorted(
            [f for ext in image_extensions for f in glob.glob(os.path.join(image_dir, ext))],
            key=ImageProcessor.sort_key
        )
    
    def load_config(self):
        """加载配置文件"""
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = json.load(f)
                    return config.get("last_index", 0)
            except:
                return 0
        return 0
    
    def save_config(self, current_index):
        """保存配置文件"""
        with open("config.json", "w") as f:
            json.dump({"last_index": current_index}, f)
    
    def load_current_image_data(self, image_path):
        """加载当前图片的数据，优先proofread_file"""
        current_image_filename = os.path.basename(image_path)
        json_name = os.path.splitext(current_image_filename)[0] + ".json"
        proofread_json_path = os.path.join("proofread_file", json_name)
        output_json_path = os.path.join("output", json_name)

        new_data_template = {
            "image": current_image_filename,
            "annotator": self.app.current_data.get("annotator", ""),
            "page_info": self.app.current_data.get("page_info", {"page_num": "", "word_num": ""}),
            "simplified_Chinese_character": "",
            "pronunciations": [{
                "zhuang_spelling": "",
                "ipa": "",
                "imported_source_path": "",
                "imported_image": [],
                "old_image_path": "",
                "dialect_type": 0,
                "entries": [{
                    "part_of_speech": "",
                    "meaning": "",
                    "examples": [{"壮文": "", "中文": ""}]
                }]
            }]
        }

        # 优先proofread_file
        json_path = None
        if os.path.exists(proofread_json_path):
            json_path = proofread_json_path
        elif os.path.exists(output_json_path):
            json_path = output_json_path

        if json_path:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    loaded_data = data[0]
                    if not loaded_data["pronunciations"]:
                        loaded_data["pronunciations"] = new_data_template["pronunciations"].copy()
                    loaded_data["annotator"] = data[0]["annotator"]
                    loaded_data["page_info"] = data[0]["page_info"]
                    return loaded_data
        return new_data_template

    def save_current_form_data(self):
        """保存当前表单数据到内存"""
        self.app.current_data["annotator"] = self.app.annotator_entry.get()
        self.app.current_data["page_info"]["page_num"] = self.app.page_num_entry.get()
        self.app.current_data["page_info"]["word_num"] = self.app.word_num_entry.get()
        self.app.current_data["simplified_Chinese_character"] = self.app.chinese_char_entry.get()

        pron = self.app.current_data["pronunciations"][self.app.current_pronunciation_index]
        pron["zhuang_spelling"] = self.app.zh_wen_entry.get()
        pron["ipa"] = self.app.ipa_entry.get()
        pron["dialect_type"] = int(self.app.dialect_var.get())

        entry = pron["entries"][self.app.current_entry_index]
        entry["part_of_speech"] = self.app.pos_entries["part_of_speech"].get()
        entry["meaning"] = self.app.pos_entries["meaning"].get()

        example = entry["examples"][self.app.current_example_index]
        # 例句用Text控件
        example["壮文"] = self.app.pos_entries["example_zhuang"].get("1.0", "end-1c")
        example["中文"] = self.app.pos_entries["example_chinese"].get("1.0", "end-1c")

    def update_form_fields(self):
        """更新表单字段显示"""
        # 更新基本信息字段
        self.app.annotator_entry.delete(0, 'end')
        self.app.annotator_entry.insert(0, self.app.current_data.get("annotator", ""))

        self.app.page_num_entry.delete(0, 'end')
        self.app.page_num_entry.insert(0, self.app.current_data["page_info"].get("page_num", ""))

        self.app.word_num_entry.delete(0, 'end')
        self.app.word_num_entry.insert(0, self.app.current_data["page_info"].get("word_num", ""))

        # 更新读音信息
        pron = self.app.current_data["pronunciations"][self.app.current_pronunciation_index]

        self.app.chinese_char_entry.delete(0, 'end')
        self.app.chinese_char_entry.insert(0, self.app.current_data.get("simplified_Chinese_character", ""))

        self.app.zh_wen_entry.delete(0, 'end')
        self.app.zh_wen_entry.insert(0, pron.get("zhuang_spelling", ""))
        
        self.app.ipa_entry.delete(0, 'end')
        self.app.ipa_entry.insert(0, pron.get("ipa", ""))
        
        dialect_type = pron.get("dialect_type", 0)
        self.app.dialect_var.set(dialect_type)

        # 更新词性信息
        entry = pron["entries"][self.app.current_entry_index]
        self.app.pos_entries["part_of_speech"].delete(0, 'end')
        self.app.pos_entries["part_of_speech"].insert(0, entry.get("part_of_speech", ""))
        
        self.app.pos_entries["meaning"].delete(0, 'end')
        self.app.pos_entries["meaning"].insert(0, entry.get("meaning", ""))

        # 更新例句信息（Text控件）
        example = entry["examples"][self.app.current_example_index]
        self.app.pos_entries["example_zhuang"].delete("1.0", "end")
        self.app.pos_entries["example_zhuang"].insert("1.0", example.get("壮文", ""))
        
        self.app.pos_entries["example_chinese"].delete("1.0", "end")
        self.app.pos_entries["example_chinese"].insert("1.0", example.get("中文", ""))

        # 更新页码显示
        self.app.pronunciation_page.config(
            text=f"{self.app.current_pronunciation_index + 1}/{len(self.app.current_data['pronunciations'])}")
        self.app.pos_page.config(
            text=f"{self.app.current_entry_index + 1}/{len(pron['entries'])}")
        self.app.example_page.config(
            text=f"{self.app.current_example_index + 1}/{len(entry['examples'])}")

    def submit_data(self):
        # 保存当前表单数据
        self.save_current_form_data()
        
        # 处理图片文件
        for pron in self.app.current_data["pronunciations"]:
            temp_source = pron.get("imported_source_path", "")
            old_source_path = pron.get("old_image_path", "")
            # 时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            
            if temp_source == old_source_path:
                continue  

            try:
                # 创建输chu目录
                input_dir = "output_image"
                os.makedirs(input_dir, exist_ok=True)

                # 获取读音名称并清理非法字符
                pron_name = pron.get("zhuang_spelling", "unnamed")
                pron_name_clean = re.sub(r'[\\/*?:"<>|]', "", pron_name)

                # 文件扩展名
                _, ext = os.path.splitext(temp_source)
                ext = ext if ext else ".jpg"

                # 生成路径
                new_filename = f"{pron_name_clean}_{timestamp}{ext}"
                dest_path = os.path.join(input_dir, new_filename)

                # 移动临时文件
                shutil.move(temp_source, dest_path)

                # 更新数据
                pron["imported_source_path"] = dest_path
                pron["old_image_path"] = dest_path
                pron["imported_image"] = [new_filename]

                # 删除旧文件
                if os.path.exists(old_source_path):
                    os.remove(old_source_path)
                    print(f"已删除历史文件: {old_source_path}")

                # 删除旧的source文件
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

        # 保存JSON文件
        self._save_json_file()

    def _save_json_file(self):
        """保存JSON文件"""
        # 确保输出目录存在
        os.makedirs("output", exist_ok=True)
        
        # 构造JSON文件名
        filename = f"{os.path.splitext(self.app.current_data['image'])[0]}.json"
        full_path = os.path.join("output", filename)

        # 保存JSON文件
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump([self.app.current_data], f, ensure_ascii=False, indent=2)

        # 显示成功消息
        messagebox.showinfo("成功", f"数据已保存到\n{full_path}")

    def delete_pronunciation_data(self, index):
        """删除读音数据及关联文件"""
        pron = self.app.current_data["pronunciations"][index]
        
        # 删除关联的图片文件
        old_path = pron.get("imported_source_path", "")
        if os.path.exists(old_path):
            os.remove(old_path)
            print(f"已删除历史文件: {old_path}")
        
        # 删除数据
        del self.app.current_data["pronunciations"][index]
        
        # 如果没有读音了，创建默认读音
        if not self.app.current_data["pronunciations"]:
            self.app.current_data["pronunciations"].append({
                "zhuang_spelling": "",
                "ipa": "",
                "imported_source_path": "",
                "imported_image": [],
                "dialect_type": 0,
                "entries": [{
                    "part_of_speech": "",
                    "meaning": "",
                    "examples": [{"壮文": "", "中文": ""}]
                }]
            })

    def add_new_pronunciation(self):
        """添加新读音"""
        new_pron = {
            "zhuang_spelling": "",
            "ipa": "",
            "imported_source_path": "",
            "old_image_path": "",
            "imported_image": [],
            "dialect_type": 0,
            "entries": [{
                "part_of_speech": "",
                "meaning": "",
                "examples": [{"壮文": "", "中文": ""}]
            }]
        }
        self.app.current_data["pronunciations"].append(new_pron)
        return len(self.app.current_data["pronunciations"]) - 1

    def add_new_entry(self, pron_index):
        """添加新词性条目"""
        pron = self.app.current_data["pronunciations"][pron_index]
        new_entry = {
            "part_of_speech": "",
            "meaning": "",
            "examples": [{"壮文": "", "中文": ""}]
        }
        pron["entries"].append(new_entry)
        return len(pron["entries"]) - 1

    def add_new_example(self, pron_index, entry_index):
        """添加新例句"""
        entry = self.app.current_data["pronunciations"][pron_index]["entries"][entry_index]
        new_example = {"壮文": "", "中文": ""}
        entry["examples"].append(new_example)
        return len(entry["examples"]) - 1

    def delete_entry(self, pron_index, entry_index):
        """删除词性条目"""
        pron = self.app.current_data["pronunciations"][pron_index]
        if len(pron["entries"]) > 1:
            del pron["entries"][entry_index]
            return True
        return False

    def delete_example(self, pron_index, entry_index, example_index):
        """删除例句"""
        entry = self.app.current_data["pronunciations"][pron_index]["entries"][entry_index]
        if len(entry["examples"]) > 1:
            del entry["examples"][example_index]
            return True
        return False
