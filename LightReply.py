import json
import os
import sys
import threading
import asyncio
import re
from mitmproxy import ctx
from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.style import Style
import winreg
import ctypes
import mistune
from tkinter import font, StringVar
import re

VERSION = "Alpha_4.5_am"

class CertManager:
    @staticmethod
    def install_cert():
        try:
            # 获取证书路径
            home_dir = os.path.expanduser("~")
            cert_dir = os.path.join(home_dir, ".mitmproxy")
            cert_path = os.path.join(cert_dir, "mitmproxy-ca-cert.cer")
            
            if not os.path.exists(cert_dir):
                os.makedirs(cert_dir)
                
            if not os.path.exists(cert_path):
                print("正在生成证书...")
                # 使用mitmdump生成证书
                import subprocess
                try:
                    subprocess.run(["mitmdump", "--set", "confdir=" + cert_dir, "-q", "-n"], timeout=2)
                except subprocess.TimeoutExpired:
                    pass  # 忽略超时，因为我们只需要生成证书
                
            if os.path.exists(cert_path):
                # 使用certutil安装证书到根证书存储区
                cmd = f'certutil -addstore -f "Root" "{cert_path}"'
                result = os.system(cmd)
                if result == 0:
                    print("证书安装成功")
                    return True
                else:
                    print(f"证书安装失败，错误代码：{result}")
                    return False
            else:
                print(f"证书文件不存在：{cert_path}")
                return False
                
        except Exception as e:
            print(f"安装证书时出错：{e}")
            return False

class ProxyConfig:
    def __init__(self):
        self.config_file = "config.json"
        self.rules = []
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = data.get('rules', [])
            else:
                self.rules = []
        except Exception as e:
            print(f"加载配置文件错误: {e}")
            self.rules = []

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'rules': self.rules}, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存配置文件错误: {e}")
            return False

class LightReplyAddon:
    def __init__(self):
        self.config = ProxyConfig()

    def response(self, flow: http.HTTPFlow) -> None:
        for rule in self.config.rules:
            url = flow.request.pretty_url
            if ((rule['match_type'] == 'exact' and rule['url'] == url) or
                (rule['match_type'] == 'prefix' and url.startswith(rule['url'])) or
                (rule['match_type'] == 'contains' and rule['url'] in url)):
                # 创建新的响应
                flow.response = http.Response.make(
                    200,  # 状态码
                    rule['content'].encode('utf-8'),  # 响应内容
                    {"Content-Type": "text/html; charset=utf-8"}  # 响应头
                )

class ProxyManager:
    def __init__(self):
        self.proxy_host = "127.0.0.1"
        self.proxy_port = 8080

    def set_system_proxy(self, enable=True):
        try:
            internet_settings = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
                0, winreg.KEY_ALL_ACCESS)

            if enable:
                # 设置代理服务器
                proxy_server = f"{self.proxy_host}:{self.proxy_port}"
                winreg.SetValueEx(internet_settings, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(internet_settings, 'ProxyServer', 0, winreg.REG_SZ, proxy_server)
                
                # 设置不使用代理的地址，只排除本地回环地址
                winreg.SetValueEx(internet_settings, 'ProxyOverride', 0, winreg.REG_SZ, '<local>')
            else:
                # 禁用代理
                winreg.SetValueEx(internet_settings, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
                # 清除代理设置
                try:
                    winreg.DeleteValue(internet_settings, 'ProxyServer')
                    winreg.DeleteValue(internet_settings, 'ProxyOverride')
                except:
                    pass

            winreg.CloseKey(internet_settings)
            
            # 刷新所有代理设置
            INTERNET_OPTION_REFRESH = 37
            INTERNET_OPTION_SETTINGS_CHANGED = 39
            INTERNET_OPTION_PROXY_SETTINGS_CHANGED = 95
            
            ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_REFRESH, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
            ctypes.windll.Wininet.InternetSetOptionW(0, INTERNET_OPTION_PROXY_SETTINGS_CHANGED, 0, 0)
            return True
        except Exception as e:
            print(f"设置系统代理错误: {e}")
            return False

class GUI(ttk.Window):
    def __init__(self):
        # 主题列表
        self.themes = [
            "darkly", "cosmo", "flatly", "litera", "minty",
            "lumen", "sandstone", "yeti", "pulse", "united",
            "morph", "journal", "simplex", "solar", "superhero"
        ]
        
        super().__init__(themename="darkly")
        self.title(f"LightReply {VERSION}")
        self.geometry("800x600")
        
        self.proxy_manager = ProxyManager()
        self.config = ProxyConfig()
        
        # 主题变量
        self.current_theme = StringVar(value="darkly")
        self.current_theme.trace_add("write", self.change_theme)
        
        self.create_widgets()
        self.proxy_running = False
        self.proxy_thread = None
        # 不禁用停止按钮，让它一直可用

    def create_widgets(self):
        # 创建菜单栏
        self.menubar = ttk.Menu(self)
        super().configure(menu=self.menubar)
        
        # 文件菜单
        file_menu = ttk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="刷新配置", command=self.refresh_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        
        # 视图菜单
        view_menu = ttk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="视图", menu=view_menu)
        
        # 主题子菜单
        theme_menu = ttk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="主题", menu=theme_menu)
        
        # 添加主题选项
        for theme in self.themes:
            theme_menu.add_radiobutton(
                label=theme.capitalize(),
                value=theme,
                variable=self.current_theme
            )
            
        # 工具菜单
        tools_menu = ttk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="安装证书", command=self.install_certificate)
        
        # 帮助菜单
        help_menu = ttk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_readme)
        
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 代理控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, pady=(0, 10))
        
        # 工具栏按钮
        self.proxy_btn = ttk.Button(
            control_frame, 
            text="启动代理", 
            command=self.start_proxy,
            bootstyle="success-outline",
            width=12
        )
        self.proxy_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="停止代理",
            command=self.stop_proxy,
            bootstyle="danger-outline",
            width=12
        )
        self.stop_btn.pack(side=LEFT, padx=5)
        
        self.cert_btn = ttk.Button(
            control_frame,
            text="安装证书",
            command=self.install_certificate,
            bootstyle="info-outline",
            width=12
        )
        self.cert_btn.pack(side=LEFT, padx=5)
        
        # 创建右对齐的按钮容器
        right_buttons = ttk.Frame(control_frame)
        right_buttons.pack(side=RIGHT, fill=X)
        
        # 右侧按钮
        self.help_btn = ttk.Button(
            right_buttons,
            text="使用说明",
            command=self.show_readme,
            bootstyle="primary-outline",  # 改用主要颜色以提高辨识度
            width=12
        )
        self.help_btn.pack(side=RIGHT, padx=5)
        
        self.refresh_btn = ttk.Button(
            right_buttons,
            text="刷新配置",
            command=self.refresh_config,
            bootstyle="info-outline",
            width=12
        )
        self.refresh_btn.pack(side=RIGHT, padx=5)        # 创建规则列表框架
        rules_frame = ttk.LabelFrame(main_frame, text="规则列表", padding=10)
        rules_frame.pack(fill=BOTH, expand=True)

        # 创建表格和滚动条容器
        tree_container = ttk.Frame(rules_frame)
        tree_container.pack(fill=BOTH, expand=True)

        # 创建规则表格
        columns = ("描述", "URL", "匹配类型", "操作")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings")
        
        # 设置列宽和标题
        self.tree.column("描述", width=200)
        self.tree.column("URL", width=300)
        self.tree.column("匹配类型", width=100)
        self.tree.column("操作", width=150)
        
        for col in columns:
            self.tree.heading(col, text=col)

        # 添加滚动条
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局表格和滚动条
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # 规则管理按钮
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=X, pady=10)

        # 左侧按钮
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side=LEFT, fill=X)

        ttk.Button(
            left_buttons,
            text="添加规则",
            command=self.add_rule,
            bootstyle="info-outline",
            width=12
        ).pack(side=LEFT, padx=5)

        # 右侧按钮组
        right_buttons = ttk.Frame(buttons_frame)
        right_buttons.pack(side=RIGHT, fill=X)

        ttk.Button(
            right_buttons,
            text="删除规则",
            command=self.delete_rule,
            bootstyle="danger-outline",
            width=12
        ).pack(side=RIGHT, padx=5)

        ttk.Button(
            right_buttons,
            text="修改规则",
            command=self.edit_rule,
            bootstyle="warning-outline",
            width=12
        ).pack(side=RIGHT, padx=5)

        self.update_rules_display()
        
        # 添加双击修改功能
        self.tree.bind('<Double-1>', lambda e: self.edit_rule())

    def toggle_proxy(self):
        if not self.proxy_running:
            self.start_proxy()
        else:
            self.stop_proxy()
    
    def change_theme(self, *args):
        """切换主题"""
        style = Style()
        style.theme_use(self.current_theme.get())
            
    def refresh_config(self):
        """刷新配置并重新加载规则"""
        self.config.load_config()
        self.update_rules_display()
        
        # 如果代理正在运行，重新加载代理的配置
        if self.proxy_running and hasattr(self, 'addon'):
            self.addon.config.load_config()
            Messagebox.show_info("成功", "配置已刷新")
        else:
            Messagebox.show_info("成功", "配置已刷新（代理未运行）")

    def show_readme(self):
        """显示使用说明"""
        dialog = ReadmeDialog(self)
        dialog.focus()  # 设置焦点到说明窗口
        
    def install_certificate(self):
        """安装HTTPS证书"""
        if CertManager.install_cert():
            Messagebox.show_info("证书安装", "证书安装成功！")
        else:
            Messagebox.show_error("证书安装", "证书安装失败，请查看控制台输出了解详细信息")

    def start_proxy(self):
        try:
            if self.proxy_running:
                Messagebox.show_warning("提示", "代理已经在运行中")
                return
                
            print("正在启动代理...")
            # 先尝试关闭可能存在的旧代理设置
            self.proxy_manager.set_system_proxy(False)
            
            # 设置新的代理
            if self.proxy_manager.set_system_proxy(True):
                # 创建配置参数
                from mitmproxy.options import Options
                from mitmproxy.tools.dump import DumpMaster
                import asyncio
                
                # 获取用户主目录下的 .mitmproxy 证书路径
                home_dir = os.path.expanduser("~")
                cert_dir = os.path.join(home_dir, ".mitmproxy")
                
                # 确保证书目录存在
                if not os.path.exists(cert_dir):
                    os.makedirs(cert_dir)
                
                options = Options(
                    listen_host='0.0.0.0',  # 监听所有接口
                    listen_port=8080,
                    ssl_insecure=True,
                    confdir=cert_dir  # 使用 .mitmproxy 目录
                )
                
                async def start_proxy_async():
                    master = DumpMaster(options, with_termlog=False)
                    self.addon = LightReplyAddon()  # 保存对 addon 的引用
                    master.addons.add(self.addon)
                    await master.run()
                    return master
                
                def run():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    self.master = loop.run_until_complete(start_proxy_async())
                    loop.run_forever()
                
                self.proxy_thread = threading.Thread(target=run)
                self.proxy_thread.daemon = True
                self.proxy_thread.start()
                self.proxy_running = True
                self.proxy_btn.configure(state="disabled")
                # 停止按钮始终保持可用状态
                Messagebox.show_info("代理已启动", "系统代理已设置成功")
            else:
                Messagebox.show_error("系统提示", "无法设置系统代理")
        except Exception as e:
            error_msg = str(e)
            print(f"启动代理时出错：{error_msg}")
            print("详细错误信息：")
            import traceback
            traceback.print_exc()
            Messagebox.show_error("系统提示", "启动代理失败，请查看控制台输出了解详细信息")

    def stop_proxy(self):
        try:
            # 先恢复系统代理设置
            self.proxy_manager.set_system_proxy(False)
            
            # 停止代理服务
            if hasattr(self, 'master'):
                try:
                    if hasattr(self.master, 'should_exit'):
                        self.master.should_exit.set()
                    if hasattr(self.master, 'shutdown'):
                        self.master.shutdown()
                    self.master = None
                except:
                    pass
            
            # 确保线程正确结束
            if self.proxy_thread and self.proxy_thread.is_alive():
                try:
                    self.proxy_thread.join(timeout=1)
                except:
                    pass
            
            self.proxy_running = False
            self.proxy_btn.configure(state="normal")
            # 停止按钮始终保持可用状态
            Messagebox.show_info("代理已停止", "系统代理已恢复默认设置")
        except Exception as e:
            error_msg = str(e)
            print(f"停止代理时出错：{error_msg}")
            print("详细错误信息：")
            import traceback
            traceback.print_exc()
            Messagebox.show_error("系统提示", "停止代理失败，请查看控制台输出了解详细信息")

    def update_rules_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for rule in self.config.rules:
            self.tree.insert(
                '', 
                END, 
                values=(
                    rule['description'],
                    rule['url'],
                    rule['match_type'],
                    rule['modify_type']
                )
            )

    def add_rule(self):
        dialog = RuleDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.config.rules.append(dialog.result)
            self.config.save_config()
            self.update_rules_display()

    def delete_rule(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("警告", "请先选择要删除的规则")
            return
            
        if Messagebox.show_question("确认", "确定要删除选中的规则吗？"):
            for item in selected:
                idx = self.tree.index(item)
                del self.config.rules[idx]
            self.config.save_config()
            self.update_rules_display()
            
    def edit_rule(self):
        selected = self.tree.selection()
        if not selected:
            Messagebox.show_warning("警告", "请先选择要修改的规则")
            return
            
        # 只修改第一个选中的规则
        item = selected[0]
        idx = self.tree.index(item)
        rule = self.config.rules[idx]
        
        dialog = RuleDialog(self, rule)
        self.wait_window(dialog)
        if dialog.result:
            self.config.rules[idx] = dialog.result
            self.config.save_config()
            self.update_rules_display()

class ReadmeDialog(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("使用说明")
        self.geometry("800x600")
        
        # 配置背景颜色
        style = ttk.Style()
        self.bg_color = "#f5f5f0"  # 米白色背景
        self.configure(background=self.bg_color)
        
        # 创建主容器
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=BOTH, expand=True)
        style.configure("Custom.TFrame", background=self.bg_color)
        self.main_container.configure(style="Custom.TFrame")
        
        # 创建文本查看器
        text_frame = ttk.Frame(self.main_container)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        text_frame.configure(style="Custom.TFrame")
        
        self.text = ttk.Text(
            text_frame,
            wrap="word",
            height=30,
            padx=20,
            pady=10,
            spacing1=4,  # 段落前间距
            spacing2=4,  # 段落中间距
            spacing3=6,  # 段落后间距
            background=self.bg_color,
            font=("Microsoft YaHei", 10)  # 使用微软雅黑字体
        )
        self.text.pack(fill=BOTH, expand=True, side=LEFT)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(fill=Y, side=RIGHT)
        
        # 连接滚动条
        self.text.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.text.yview)
        
        # 添加关闭按钮
        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(fill=X, pady=10)
        btn_frame.configure(style="Custom.TFrame")
        
        ttk.Button(
            btn_frame,
            text="关闭",
            command=self.destroy,
            width=15,
            bootstyle="secondary-outline"
        ).pack(side=BOTTOM, pady=10)
        
    def setup_text_styles(self):
        """设置文本样式"""
        base_font = "Microsoft YaHei"  # 微软雅黑
        
        # 配置标签样式
        self.text.tag_configure(
            "h1",
            font=(base_font, 20, "bold"),
            spacing1=16,
            spacing3=12,
            foreground="#2c3e50"
        )
        self.text.tag_configure(
            "h2",
            font=(base_font, 16, "bold"),
            spacing1=14,
            spacing3=10,
            foreground="#34495e"
        )
        self.text.tag_configure(
            "h3",
            font=(base_font, 14, "bold"),
            spacing1=12,
            spacing3=8,
            foreground="#404040"
        )
        
        # 正文样式
        self.text.tag_configure(
            "p",
            font=(base_font, 10),
            spacing1=6,
            spacing3=6,
            foreground="#333333"
        )
        
        # 代码样式
        self.text.tag_configure(
            "code",
            font=("Consolas", 9),
            background="#f8f9fa",
            relief="solid",
            borderwidth=1,
            spacing1=8,
            spacing3=8,
            lmargin1=20,
            lmargin2=20
        )
        
        # 列表样式
        self.text.tag_configure(
            "list",
            font=(base_font, 10),
            lmargin1=30,
            lmargin2=50
        )
        
        # 引用样式
        self.text.tag_configure(
            "quote",
            font=(base_font, 10, "italic"),
            background="#f8f9fa",
            lmargin1=30,
            lmargin2=30,
            rmargin=30
        )
        title_font = "Arial" if "Arial" in font.families() else "TkDefaultFont"
        code_font = "Consolas" if "Consolas" in font.families() else "Courier"
        
        # 标题样式
        self.text.tag_configure(
            "h1",
            font=(title_font, 20, "bold"),
            spacing1=15,
            spacing3=10,
            foreground="#1a73e8"
        )
        self.text.tag_configure(
            "h2",
            font=(title_font, 16, "bold"),
            spacing1=12,
            spacing3=8,
            foreground="#2b579a"
        )
        self.text.tag_configure(
            "h3",
            font=(title_font, 14, "bold"),
            spacing1=10,
            spacing3=6,
            foreground="#515151"
        )
        
        # 文本样式
        self.text.tag_configure(
            "bold",
            font=(title_font, 10, "bold"),
            foreground="#202124"
        )
        self.text.tag_configure(
            "italic",
            font=(title_font, 10, "italic"),
            foreground="#202124"
        )
        
        # 代码样式
        self.text.tag_configure(
            "code",
            font=(code_font, 9),
            background="#f6f8fa",
            borderwidth=1,
            relief="solid",
            spacing1=10,
            spacing3=10,
            lmargin1=20,
            lmargin2=20,
            rmargin=20
        )
        self.text.tag_configure(
            "code-inline",
            font=(code_font, 9),
            background="#f6f8fa",
            relief="solid",
            borderwidth=1
        )
        
        # 列表样式
        self.text.tag_configure(
            "list",
            lmargin1=40,
            lmargin2=60
        )
        
        # 引用样式
        self.text.tag_configure(
            "quote",
            lmargin1=30,
            lmargin2=30,
            rmargin=30,
            background="#f8f9fa",
            borderwidth=2,
            relief="solid"
        )
        
        # 普通段落样式
        self.text.tag_configure(
            "paragraph",
            font=(title_font, 10),
            spacing1=5,
            spacing3=5,
            foreground="#333333"
        )
        
        # 配置文本样式
        self.setup_text_styles()
        
        # 加载说明文件内容
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            about_file = os.path.join(script_dir, "about.md")
            
            with open(about_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 使用mistune渲染Markdown
            markdown = mistune.create_markdown(renderer=mistune.HTMLRenderer())
            html = markdown(content)
            self.render_markdown(html)
            
        except Exception as e:
            error_msg = f"无法加载说明文件: {str(e)}"
            print(error_msg)
            self.text.insert("1.0", error_msg)
        
        # 设置只读
        self.text.configure(state="disabled")
        
        # 添加关闭按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, pady=10, padx=10)
        
        ttk.Button(
            btn_frame,
            text="关闭",
            command=self.destroy,
            width=15,
            bootstyle="secondary-outline"
        ).pack(side=BOTTOM, pady=10)

    def render_markdown(self, html):
        """渲染Markdown内容"""
        self.text.delete("1.0", "end")
        
        # 解析HTML
        current_tag = None
        in_list = False
        in_code = False
        code_block = []
        
        # 清理HTML
        html = html.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        
        # 分段处理
        lines = html.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 处理标题
            if "<h1>" in line:
                text = re.sub("<[^>]+>", "", line).strip()
                self.text.insert("end", text + "\n\n", "h1")
            elif "<h2>" in line:
                text = re.sub("<[^>]+>", "", line).strip()
                self.text.insert("end", text + "\n\n", "h2")
            elif "<h3>" in line:
                text = re.sub("<[^>]+>", "", line).strip()
                self.text.insert("end", text + "\n\n", "h3")
            
            # 处理代码块
            elif "<pre><code>" in line:
                in_code = True
                code_block = []
                i += 1
                while i < len(lines) and "</code></pre>" not in lines[i]:
                    if lines[i].startswith("`"):
                        code_block.append(lines[i][1:])  # 移除开头的反引号
                    else:
                        code_block.append(lines[i])
                    i += 1
                if code_block:
                    self.text.insert("end", "\n")
                    for code_line in code_block:
                        if code_line.strip():  # 只处理非空行
                            self.text.insert("end", code_line + "\n", "code")
                    self.text.insert("end", "\n")
                in_code = False
            
            # 处理列表
            elif "<li>" in line:
                text = re.sub("<[^>]+>", "", line).strip()
                if not in_list:
                    self.text.insert("end", "\n")
                    in_list = True
                # 处理列表项中的加粗
                text = re.sub("<strong>(.*?)</strong>", "\\1", text)
                self.text.insert("end", "• " + text + "\n", "list")
                # 如果加粗文本存在，添加加粗样式
                if "<strong>" in line:
                    bold_text = re.search("<strong>(.*?)</strong>", line)
                    if bold_text:
                        start = self.text.index("end-2c linestart")
                        end = self.text.index("end-1c")
                        self.text.tag_add("bold", start, end)
            
            # 处理段落
            elif "<p>" in line:
                if in_list:
                    self.text.insert("end", "\n")
                    in_list = False
                text = re.sub("<[^>]+>", "", line).strip()
                if text:
                    # 处理段落中的特殊格式
                    if "<strong>" in line or "<code>" in line:
                        pos = "end"
                        self.text.insert("end", text + "\n\n", "p")
                        # 处理加粗
                        for m in re.finditer("<strong>(.*?)</strong>", line):
                            bold_start = text.find(m.group(1))
                            bold_end = bold_start + len(m.group(1))
                            self.text.tag_add("bold", f"end-2c linestart+{bold_start}c", 
                                            f"end-2c linestart+{bold_end}c")
                        # 处理代码
                        for m in re.finditer("<code>(.*?)</code>", line):
                            code_start = text.find(m.group(1))
                            code_end = code_start + len(m.group(1))
                            self.text.tag_add("code-inline", f"end-2c linestart+{code_start}c",
                                            f"end-2c linestart+{code_end}c")
                    else:
                        self.text.insert("end", text + "\n\n", "p")
            
            # 处理空行
            elif not line.strip():
                if in_list:
                    in_list = False
                self.text.insert("end", "\n")
            
            i += 1

    def process_inline_styles(self, text):
        """处理内联样式（加粗、斜体、代码等）"""
        processed_text = ""
        pos = 0
        
        while pos < len(text):
            # 查找下一个标签
            next_tag_pos = float('inf')
            next_tag_type = None
            
            for tag, length in [
                ('<code>', 6),
                ('</code>', 7),
                ('<strong>', 8),
                ('</strong>', 9),
                ('<em>', 4),
                ('</em>', 5)
            ]:
                tag_pos = text.find(tag, pos)
                if tag_pos != -1 and tag_pos < next_tag_pos:
                    next_tag_pos = tag_pos
                    next_tag_type = (tag, length)
            
            if next_tag_type is None:
                # 没有更多标签，添加剩余文本
                processed_text += text[pos:]
                break
            
            # 添加标签前的文本
            processed_text += text[pos:next_tag_pos]
            tag, length = next_tag_type
            
            # 处理不同类型的标签
            if tag == '<code>':
                end_pos = text.find('</code>', next_tag_pos)
                if end_pos != -1:
                    code_text = text[next_tag_pos + length:end_pos]
                    processed_text += f"「{code_text}」"  # 使用特殊标记包围代码
                    pos = end_pos + 7
                    self.text.tag_add("code-inline", f"end-{len(code_text)+2}c", "end")
                else:
                    pos = next_tag_pos + length
            elif tag == '<strong>':
                end_pos = text.find('</strong>', next_tag_pos)
                if end_pos != -1:
                    bold_text = text[next_tag_pos + length:end_pos]
                    processed_text += bold_text
                    pos = end_pos + 9
                    self.text.tag_add("bold", f"end-{len(bold_text)}c", "end")
                else:
                    pos = next_tag_pos + length
            elif tag == '<em>':
                end_pos = text.find('</em>', next_tag_pos)
                if end_pos != -1:
                    italic_text = text[next_tag_pos + length:end_pos]
                    processed_text += italic_text
                    pos = end_pos + 5
                    self.text.tag_add("italic", f"end-{len(italic_text)}c", "end")
                else:
                    pos = next_tag_pos + length
            else:
                pos = next_tag_pos + length
        
        return processed_text

class RuleDialog(ttk.Toplevel):
    def __init__(self, parent, rule=None):
        super().__init__(parent)
        self.title("修改规则" if rule else "添加规则")
        self.geometry("800x700")  # 增加窗口宽度和高度
        
        self.rule = rule
        self.result = None
        self.create_widgets()

    def create_widgets(self):
        # 主容器
        main_container = ttk.Frame(self)
        main_container.pack(fill=BOTH, expand=True)
        
        # 创建滚动区域
        scroll_frame = ttk.Frame(main_container, padding=20)
        scroll_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # 输入区域
        input_frame = ttk.Frame(scroll_frame)
        input_frame.pack(fill=BOTH, expand=True)

        # 描述
        ttk.Label(input_frame, text="规则描述:").pack(fill=X, pady=2)
        self.description = ttk.Entry(input_frame)
        if self.rule:
            self.description.insert(0, self.rule['description'])
        self.description.pack(fill=X, pady=(0, 5))

        # URL
        ttk.Label(input_frame, text="URL:").pack(fill=X, pady=2)
        self.url = ttk.Entry(input_frame)
        if self.rule:
            self.url.insert(0, self.rule['url'])
        self.url.pack(fill=X, pady=(0, 5))

        # 匹配类型
        ttk.Label(input_frame, text="匹配类型:").pack(fill=X, pady=2)
        self.match_type = ttk.Combobox(
            input_frame,
            values=["exact", "prefix", "contains"],
            state="readonly"
        )
        self.match_type.set(self.rule['match_type'] if self.rule else "exact")
        self.match_type.pack(fill=X, pady=(0, 5))

        # 修改类型
        ttk.Label(input_frame, text="修改类型:").pack(fill=X, pady=2)
        self.modify_type = ttk.Combobox(
            input_frame,
            values=["response"],
            state="readonly"
        )
        self.modify_type.set("response")
        self.modify_type.pack(fill=X, pady=(0, 5))

        # 修改内容
        ttk.Label(input_frame, text="修改内容:").pack(fill=X, pady=2)
        self.content = ttk.Text(input_frame, height=8)  # 进一步减小文本框高度
        if self.rule:
            self.content.insert('1.0', self.rule['content'])
        self.content.pack(fill=BOTH, pady=(0, 5))

        # 底部按钮区域 - 使用新的Frame确保它始终在底部
        btn_frame = ttk.Frame(main_container)
        btn_frame.pack(fill=X, side=BOTTOM, padx=20, pady=10)
        
        # 将按钮直接放在底部Frame中
        ttk.Button(
            btn_frame,
            text="保存",
            command=self.save,
            width=15,
            bootstyle="success-outline"
        ).pack(side=LEFT, expand=True, padx=5)
        
        ttk.Button(
            btn_frame,
            text="取消",
            command=self.cancel,
            width=15,
            bootstyle="secondary-outline"
        ).pack(side=LEFT, expand=True, padx=5)
        


    def save(self):
        self.result = {
            'description': self.description.get(),
            'url': self.url.get(),
            'match_type': self.match_type.get(),
            'modify_type': self.modify_type.get(),
            'content': self.content.get('1.0', END).strip()
        }
        self.destroy()

    def cancel(self):
        self.destroy()

if __name__ == '__main__':
    app = GUI()
    app.mainloop()
