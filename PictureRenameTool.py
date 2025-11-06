import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime


class PictureRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Picture_Rename")
        self.root.geometry("520x420")
        self.root.resizable(False, False)

        self.selected_file = None
        self.device_name = None
        self.fixed_devices = ["交换机", "电池", "水晶头", "面板", "模块", "热熔设备", "其他"]
        self.device_buttons = {}
        self.device_count = self.load_device_count()

        # 主框架
        left_frame = tk.Frame(root, width=150)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # --- 左侧：设备按钮 ---
        tk.Label(left_frame, text="选择设备：", font=("微软雅黑", 10)).pack(pady=(0, 8))
        for dev in self.fixed_devices:
            btn = tk.Button(
                left_frame,
                text=dev,
                width=12,
                height=2,
                font=("微软雅黑", 9),
                bg="SystemButtonFace",
                command=lambda d=dev: self.select_device(d)
            )
            btn.pack(pady=4, fill="x", padx=2)
            self.device_buttons[dev] = btn

        # 总数显示（仅6个固定设备）
        self.label_summary = tk.Label(left_frame, text="累计总数：\n" + self.get_summary_text(), justify="left", font=("微软雅黑", 8))
        self.label_summary.pack(pady=10, fill="x")

        # --- 右侧操作区 ---
        self.btn_select = tk.Button(right_frame, text="选择图片", width=20, height=2, command=self.select_file)
        self.btn_select.pack(pady=8)

        self.label_file = tk.Label(right_frame, text="未选择任何图片", fg="gray", wraplength=280)
        self.label_file.pack(pady=5)

        tk.Label(right_frame, text="备注（可选）：", font=("微软雅黑", 9)).pack(pady=(8, 2))
        self.entry_remark = tk.Entry(right_frame, width=20, font=("微软雅黑", 9))
        self.entry_remark.pack(pady=2)

        tk.Label(right_frame, text="输入设备数量：", font=("微软雅黑", 9)).pack(pady=(8, 2))
        self.entry_quantity = tk.Entry(right_frame, width=10, font=("Arial", 10))
        self.entry_quantity.pack(pady=2)
        self.entry_quantity.insert(0, "1")

        self.btn_rename = tk.Button(right_frame, text="生成重命名副本", width=20, height=2, state="disabled", command=self.rename_copy)
        self.btn_rename.pack(pady=15)

        # --- 右上角 Carrot 日志入口 ---
        self.carrot_label = tk.Label(
            root,
            text="Carrot",
            bg="#4A90E2",      # 蓝色
            fg="white",
            font=("Arial", 8, "bold"),
            width=6,
            height=1,
            relief="flat",
            cursor="hand2"
        )
        self.carrot_label.place(x=460, y=10)
        self.carrot_label.bind("<Button-1>", lambda e: self.view_log())

    def select_device(self, name):
        # 清除所有按钮高亮
        for btn in self.device_buttons.values():
            btn.config(bg="SystemButtonFace")
        # 高亮当前选中按钮
        if name in self.device_buttons:
            self.device_buttons[name].config(bg="#d0e0ff")

        if name == "其他":
            custom_name = simpledialog.askstring("自定义设备", "请输入设备名称：", parent=self.root)
            if custom_name and custom_name.strip():
                self.device_name = custom_name.strip()
            else:
                self.device_name = None
                self.device_buttons["其他"].config(bg="SystemButtonFace")
                return
        else:
            self.device_name = name

        self.update_summary()

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="请选择一张图片",
            filetypes=[("图像文件", "*.jpg;*.jpeg;*.png;*.bmp;*.gif"), ("所有文件", "*.*")]
        )
        if file_path:
            self.selected_file = os.path.abspath(file_path)
            self.label_file.config(text=f"已选择：{os.path.basename(self.selected_file)}", fg="black")
            self.btn_rename.config(state="normal")
        else:
            self.selected_file = None
            self.label_file.config(text="未选择任何图片", fg="gray")
            self.btn_rename.config(state="disabled")

    def get_summary_text(self):
        lines = []
        for dev in ["交换机", "电池", "水晶头", "面板", "模块", "热熔设备"]:
            lines.append(f"{dev}：{self.device_count.get(dev, 0)} 个")
        return "\n".join(lines)

    def update_summary(self):
        self.label_summary.config(text="累计总数：\n" + self.get_summary_text())

    def load_device_count(self):
        log_path = "rename_log.txt"
        count = {dev: 0 for dev in ["交换机", "电池", "水晶头", "面板", "模块", "热熔设备"]}
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if "] 领取" in line:
                        try:
                            # 尝试从日志重建总数（增强鲁棒性）
                            parts = line.split("领取", 1)[1].split("个", 1)[0]
                            # 提取设备名（支持带备注）
                            if "_" in parts:
                                possible_dev = parts.split("_")[0]
                                if possible_dev in count:
                                    # 找数量（最后一个下划线后的部分）
                                    num_str = parts.split("_")[-1]
                                    if num_str.isdigit():
                                        count[possible_dev] += int(num_str)
                            else:
                                # 无备注：如 "电池_5"
                                if "_" in parts:
                                    dev_part, num_part = parts.rsplit("_", 1)
                                    if dev_part in count and num_part.isdigit():
                                        count[dev_part] += int(num_part)
                        except:
                            continue
        return count

    def save_device_count(self):
        log_path = "rename_log.txt"
        summary_line = "[设备统计]: " + ", ".join([f"{k}:{v}" for k, v in self.device_count.items()])
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{summary_line}\n")

    def rename_copy(self):
        if not self.selected_file:
            messagebox.showwarning("警告", "请先选择图片！")
            return
        if not self.device_name:
            messagebox.showwarning("警告", "请先选择设备！")
            return

        quantity_str = self.entry_quantity.get().strip()
        if not quantity_str.isdigit() or len(quantity_str) == 0:
            messagebox.showwarning("警告", "请输入有效的设备数量（正整数）")
            return
        quantity_int = int(quantity_str)

        remark = self.entry_remark.get().strip()

        try:
            directory = os.path.dirname(self.selected_file)
            ext = os.path.splitext(self.selected_file)[1].lower()
            date_str = datetime.now().strftime("%Y%m%d")

            # 构建新文件名
            if remark:
                new_name = f"{date_str}_{self.device_name}_{remark}_{quantity_str}{ext}"
                display_name = f"{self.device_name}_{remark}_{quantity_str}"
            else:
                new_name = f"{date_str}_{self.device_name}_{quantity_str}{ext}"
                display_name = f"{self.device_name}_{quantity_str}"

            new_path = os.path.join(directory, new_name)

            if os.path.exists(new_path):
                if not messagebox.askyesno("覆盖确认", f"文件 {new_name} 已存在，是否覆盖？"):
                    return

            shutil.copy2(self.selected_file, new_path)

            # === 修复：设备总数 += 输入的数量（不是 +1）===
            if self.device_name in self.device_count:
                self.device_count[self.device_name] += quantity_int
                self.save_device_count()
                self.update_summary()

            # === 合并日志为单行 ===
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"[{timestamp}] 领取{display_name}个（文件：{new_name}）"

            with open("rename_log.txt", 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")

            messagebox.showinfo("成功", f"已生成文件：\n{new_name}")

        except Exception as e:
            messagebox.showerror("错误", f"操作失败：\n{str(e)}")

    def view_log(self):
        password = simpledialog.askstring("密码验证", "请输入日志查看密码：", show='*', parent=self.root)
        if password == "admin5678":
            log_path = "rename_log.txt"
            if not os.path.exists(log_path):
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("# 图片重命名日志\n")
            try:
                os.startfile(log_path)  # Windows only
            except Exception:
                messagebox.showerror("错误", "无法打开日志，请手动查看同目录下的 rename_log.txt")
        else:
            if password is not None:
                messagebox.showerror("错误", "密码错误！")


if __name__ == "__main__":
    root = tk.Tk()
    app = PictureRenamerApp(root)
    root.mainloop()