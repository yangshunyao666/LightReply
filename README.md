# LightReply2.1
### 请注意，我是用copilot写的，7月额度用完了，8月才会更新，还有很多功能没做，很多bug和观感没优化,谢谢支持！

LightReply 是一个强大的HTTP/HTTPS请求拦截和修改工具，类似于HTTP Debugger的自动回复功能。

## 特性

- HTTP/HTTPS请求拦截和修改
- 自动设置系统代理
- 美观的GUI界面（使用ttk bootstrap）
- 灵活的URL匹配规则：
  - 完全匹配
  - 前缀匹配
  - 包含匹配
- 配置文件管理
- 支持脚本配置

## 安装依赖

```bash
.\setup.bat
```
或直接双击运行
## 使用方法

1. 运行主程序：
   ```bash
   python LightReply.py #不推荐
   ```
或
   ```bash
   .\start.bat #推荐，有管理员权限
   ```
或直接双击运行
2. 点击"启动代理"按钮开始拦截
3. 使用界面添加、编辑或删除规则
4. 规则会自动保存到config.json文件中
5. 记得点刷新规则来立即生效！

## 配置文件格式

config.json示例：
```json
{
    "rules": [
        {
            "description": "规则描述",
            "url": "example.com",
            "match_type": "exact|prefix|contains",
            "modify_type": "response",
            "content": "修改后的内容"
        }
    ]
}
```

## 注意事项

1. 首次使用时需要安装mitmproxy的证书（使用setup.bat即可）
2. 程序会自动设置系统代理
3. 关闭程序时会自动恢复系统代理设置