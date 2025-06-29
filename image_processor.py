"""
图像处理模块
包含图像加载、显示、截图、缩略图生成等功能
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageGrab
import os
import tempfile
import time
from datetime import datetime


class ImageProcessor:
    def __init__(self, app_instance):
        self.app = app_instance
        self.temp_dir = os.path.abspath("temp")
        
    def load_and_display_image(self, image_path):
        """加载并显示主图片"""
        try:
            img = Image.open(image_path)
            img.thumbnail((1000, 1000))
            photo = ImageTk.PhotoImage(img)
            
            self.app.img_canvas.image = photo
            self.app.img_canvas.delete("all")
            self.app.img_canvas.create_image(50, 50, image=photo)
            
            return True
        except Exception as e:
            self.app.img_canvas.delete("all")
            self.app.img_canvas.create_text(250, 250, text="图片加载失败", fill="red")
            print(f"错误: {str(e)}")
            return False
    
    def show_enlarged_image(self, image_path):
        """显示放大后的图片"""
        try:
            win = tk.Toplevel(self.app.root)
            win.title("放大预览")

            img = Image.open(image_path)
            # 根据屏幕尺寸调整图片大小
            screen_width = self.app.root.winfo_screenwidth()
            screen_height = self.app.root.winfo_screenheight()
            img.thumbnail((screen_width - 100, screen_height - 100))

            photo = ImageTk.PhotoImage(img)
            label = tk.Label(win, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)

            # 双击关闭窗口
            label.bind("<Double-Button-1>", lambda e: win.destroy())
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片：{str(e)}")
    
    def create_thumbnail(self, image_path, size=(50, 50)):
        """创建缩略图"""
        try:
            img = Image.open(image_path)
            img.thumbnail(size)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"缩略图创建失败: {str(e)}")
            return None
    
    def update_thumbnail_panel(self):
        """更新缩略图显示（显示当前读音的截图）"""
        # 清空现有缩略图
        for label in self.app.thumbnail_labels:
            label.destroy()
        self.app.thumbnail_labels.clear()
        self.app.thumbnail_images.clear()

        # 获取当前读音数据
        pron = self.app.current_data["pronunciations"][self.app.current_pronunciation_index]

        # 优先级：临时图片 > 已提交图片
        temp_path = pron.get("imported_source_path", "")
        if temp_path and os.path.exists(temp_path):
            try:
                img = Image.open(temp_path)
                img.thumbnail((50, 50))
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(self.app.thumbnail_frame, image=photo,
                                 borderwidth=2, relief="solid",
                                 highlightbackground="red")
                label.bind("<Button-1>", lambda e, path=temp_path: self.show_enlarged_image(path))
                label.image = photo
                label.pack(side=tk.LEFT, padx=2)
                self.app.thumbnail_labels.append(label)
                self.app.thumbnail_images.append(photo)
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
                    label = tk.Label(self.app.thumbnail_frame, image=photo,
                                     borderwidth=1, relief="solid")
                    label.image = photo
                    label.pack(side=tk.LEFT, padx=2)
                    label.bind("<Button-1>", lambda e, path=img_path: self.show_enlarged_image(path))
                    self.app.thumbnail_labels.append(label)
                    self.app.thumbnail_images.append(photo)
                except Exception as e:
                    print(f"缩略图加载失败: {str(e)}")

    def capture_screen(self):
        """实时截图功能"""
        try:
            # 确保临时目录存在
            os.makedirs(self.temp_dir, exist_ok=True)

            # 阶段1：截取全屏
            self.app.root.withdraw()  # 隐藏主窗口
            time.sleep(0.3)  # 等待窗口完全隐藏

            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            fullscreen_temp_path = os.path.join(self.temp_dir, f"fullscreen_{timestamp}.png")

            # 截取并保存全屏
            screenshot = ImageGrab.grab()
            screenshot.save(fullscreen_temp_path, "PNG")

            # 阶段2：在全屏截图上选区
            self._create_selection_window(fullscreen_temp_path, timestamp)

        except Exception as main_error:
            messagebox.showerror("严重错误", f"截图过程失败：{str(main_error)}")
        finally:
            self.app.root.deiconify()

    def _create_selection_window(self, fullscreen_temp_path, timestamp):
        """创建选区窗口"""
        selector_window = tk.Toplevel(self.app.root)
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
                pron = self.app.current_data["pronunciations"][self.app.current_pronunciation_index]
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

    @staticmethod
    def sort_key(file_path):
        """文件排序键函数"""
        filename = os.path.basename(file_path)
        main_name = os.path.splitext(filename)[0]
        parts = main_name.split('_')
        num1 = int(parts[1])
        num2 = int(parts[3])
        return (num1, num2)
