#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL")
    
    def send_email(self, to_email, subject, html_content):
        """发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html'))
            
            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # 启用TLS加密
            server.login(self.smtp_username, self.smtp_password)
            
            # 发送邮件
            server.send_message(msg)
            server.quit()
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False
    
    def send_welcome_email(self, email, name, token):
        """发送欢迎邮件"""
        subject = "欢迎订阅 TopRepo - GitHub 热门项目日报"
        
        # 构建退订链接
        unsubscribe_link = f"http://yourdomain.com/unsubscribe/{token}"
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #0366d6; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                a {{ color: #0366d6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>欢迎订阅 TopRepo!</h1>
                <p>亲爱的 {name or '用户'},</p>
                <p>感谢您订阅 TopRepo - GitHub 热门项目日报！</p>
                <p>从现在开始，您将每天收到 GitHub 上最热门和增长最快的项目更新。</p>
                <p>我们希望这些信息能帮助您了解开源社区的最新动态，发现有价值的项目。</p>
                <p>如果您有任何问题或建议，请随时回复此邮件。</p>
                <p>祝您编码愉快！</p>
                <div class="footer">
                    <p>如果您不想再接收这些邮件，可以 <a href="{unsubscribe_link}">点击这里退订</a>。</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(email, subject, html_content)
    
    def send_daily_update(self, subscribers, trending_repos, growing_repos):
        """发送每日更新邮件"""
        subject = f"TopRepo 每日更新 - {datetime.now().strftime('%Y-%m-%d')}"
        
        # 创建仓库HTML表格
        trending_table = self._create_repo_table(trending_repos[:5], "最新热门仓库")
        growing_table = self._create_repo_table(growing_repos[:5], "增长最快的仓库", is_growing=True)
        
        for subscriber in subscribers:
            try:
                email = subscriber["email"]
                name = subscriber["name"] or "用户"
                token = subscriber.get("token", "")
                
                # 构建退订链接
                unsubscribe_link = f"http://yourdomain.com/unsubscribe/{token}"
                
                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                        h1 {{ color: #0366d6; }}
                        h2 {{ color: #0366d6; margin-top: 30px; }}
                        table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                        th, td {{ text-align: left; padding: 8px; }}
                        th {{ background-color: #f1f1f1; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        .repo-name {{ font-weight: bold; }}
                        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
                        a {{ color: #0366d6; text-decoration: none; }}
                        .view-more {{ margin-top: 15px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>TopRepo 每日更新</h1>
                        <p>亲爱的 {name},</p>
                        <p>以下是今天 GitHub 上最热门和增长最快的项目：</p>
                        
                        {trending_table}
                        
                        {growing_table}
                        
                        <p class="view-more"><a href="http://yourdomain.com">查看更多热门项目 →</a></p>
                        
                        <div class="footer">
                            <p>如果您不想再接收这些邮件，可以 <a href="{unsubscribe_link}">点击这里退订</a>。</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                self.send_email(email, subject, html_content)
            except Exception as e:
                logger.error(f"发送每日更新邮件给 {subscriber.get('email')} 时出错: {str(e)}")
    
    def _create_repo_table(self, repos, title, is_growing=False):
        """创建仓库HTML表格"""
        html = f"<h2>{title}</h2>"
        
        if is_growing:
            html += """
            <table border="1">
                <tr>
                    <th>仓库</th>
                    <th>语言</th>
                    <th>星标</th>
                    <th>增长率</th>
                </tr>
            """
            
            for repo in repos:
                growth_rate = repo.get("growth_rate", 0)
                html += f"""
                <tr>
                    <td class="repo-name"><a href="{repo['url']}">{repo['full_name']}</a></td>
                    <td>{repo['language']}</td>
                    <td>⭐ {repo['stars']}</td>
                    <td>+{growth_rate:.2%}</td>
                </tr>
                """
        else:
            html += """
            <table border="1">
                <tr>
                    <th>仓库</th>
                    <th>语言</th>
                    <th>星标</th>
                    <th>描述</th>
                </tr>
            """
            
            for repo in repos:
                description = repo['description'][:80] + "..." if repo['description'] and len(repo['description']) > 80 else repo['description']
                html += f"""
                <tr>
                    <td class="repo-name"><a href="{repo['url']}">{repo['full_name']}</a></td>
                    <td>{repo['language']}</td>
                    <td>⭐ {repo['stars']}</td>
                    <td>{description}</td>
                </tr>
                """
        
        html += "</table>"
        return html 