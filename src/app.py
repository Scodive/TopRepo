#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from dotenv import load_dotenv
from database import Database
from fetch_trending import TrendingFetcher
from email_service import EmailService
from apscheduler.schedulers.background import BackgroundScheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY", "dev_secret_key")

# 初始化数据库
db = Database()

# 初始化邮件服务
email_service = EmailService()

# 创建调度器
scheduler = BackgroundScheduler()

def fetch_and_update():
    """抓取数据并更新"""
    logger.info("开始定时抓取任务...")
    fetcher = TrendingFetcher()
    trending_repos, growing_repos = fetcher.run()
    
    # 发送邮件给订阅者
    if trending_repos and growing_repos:
        subscribers = db.get_active_subscribers()
        if subscribers:
            email_service.send_daily_update(subscribers, trending_repos, growing_repos)
    
    logger.info("定时抓取任务完成")

# 设置定时任务
fetch_interval = int(os.getenv("FETCH_INTERVAL_HOURS", "24"))
scheduler.add_job(fetch_and_update, 'interval', hours=fetch_interval, id='fetch_job')

# 启动调度器
scheduler.start()

@app.route('/')
def index():
    """首页"""
    # 获取最新的trending仓库
    trending_repos = db.get_trending_repos(category="new", limit=10)
    growing_repos = db.get_growing_repos(limit=10)
    
    # 如果数据库中没有数据，则立即抓取
    if not trending_repos or not growing_repos:
        fetcher = TrendingFetcher()
        trending_repos, growing_repos = fetcher.run()
    
    return render_template(
        'index.html', 
        trending_repos=trending_repos, 
        growing_repos=growing_repos,
        update_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/subscribe', methods=['POST'])
def subscribe():
    """订阅服务"""
    email = request.form.get('email')
    name = request.form.get('name', '')
    
    if not email:
        flash('请提供有效的邮箱地址', 'error')
        return redirect(url_for('index'))
    
    # 生成唯一token用于退订
    token = str(uuid.uuid4())
    
    # 添加订阅者
    success = db.add_subscriber(email, name, token)
    
    if success:
        # 发送欢迎邮件
        email_service.send_welcome_email(email, name, token)
        flash('订阅成功！请查收欢迎邮件', 'success')
    else:
        flash('您已经订阅过了', 'info')
    
    return redirect(url_for('index'))

@app.route('/unsubscribe/<token>')
def unsubscribe(token):
    """退订服务"""
    success = db.remove_subscriber(token=token)
    
    if success:
        return render_template('unsubscribe.html', success=True)
    else:
        return render_template('unsubscribe.html', success=False)

@app.route('/api/trending')
def api_trending():
    """API: 获取trending仓库"""
    category = request.args.get('category', 'new')
    limit = int(request.args.get('limit', 20))
    
    if category == 'growing':
        repos = db.get_growing_repos(limit=limit)
    else:
        repos = db.get_trending_repos(category=category, limit=limit)
    
    return jsonify({
        'status': 'success',
        'data': repos,
        'count': len(repos),
        'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/refresh')
def refresh_data():
    """手动刷新数据"""
    fetcher = TrendingFetcher()
    trending_repos, growing_repos = fetcher.run()
    
    return redirect(url_for('index'))

@app.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')

@app.errorhandler(404)
def page_not_found(e):
    """404页面"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """500页面"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 