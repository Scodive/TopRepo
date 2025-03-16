#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
import logging
from datetime import datetime, timedelta
import requests
from github import Github
from dotenv import load_dotenv
import pandas as pd
from database import Database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

class TrendingFetcher:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.g = Github(self.github_token)
        self.db = Database()
        self.trending_url = "https://api.github.com/search/repositories"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.github_token}"
        }
    
    def fetch_trending_repos(self, days=1, language=None, limit=20):
        """获取指定天数内的trending仓库"""
        logger.info(f"获取过去{days}天内的trending仓库...")
        
        # 计算日期范围
        date_range = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 构建查询参数
        query = f"created:>{date_range}"
        if language:
            query += f" language:{language}"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        # 发送请求
        response = requests.get(self.trending_url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            return []
        
        repos = response.json().get("items", [])
        return self._process_repos(repos, "new")
    
    def fetch_fastest_growing(self, days=7, limit=20):
        """获取增长最快的仓库"""
        logger.info(f"获取过去{days}天内增长最快的仓库...")
        
        # 计算日期范围
        date_range = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 构建查询参数
        query = f"pushed:>{date_range} stars:>100"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100  # 获取更多数据以便计算增长率
        }
        
        # 发送请求
        response = requests.get(self.trending_url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            return []
        
        repos = response.json().get("items", [])
        
        # 获取每个仓库的历史星标数据并计算增长率
        growing_repos = []
        for repo in repos:
            try:
                repo_obj = self.g.get_repo(f"{repo['owner']['login']}/{repo['name']}")
                # 获取仓库的星标历史
                stars_before = self._get_stars_before_days(repo_obj, days)
                stars_now = repo["stargazers_count"]
                
                if stars_before > 0:
                    growth_rate = (stars_now - stars_before) / stars_before
                    repo["growth_rate"] = growth_rate
                    repo["stars_increased"] = stars_now - stars_before
                    growing_repos.append(repo)
                
                # 避免API速率限制
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"处理仓库 {repo['full_name']} 时出错: {str(e)}")
        
        # 按增长率排序
        growing_repos.sort(key=lambda x: x.get("growth_rate", 0), reverse=True)
        return self._process_repos(growing_repos[:limit], "growing")
    
    def _get_stars_before_days(self, repo, days):
        """估算几天前的星标数"""
        try:
            # 获取最近的星标事件
            stargazers = list(repo.get_stargazers_with_dates())
            if not stargazers:
                return repo.stargazers_count
            
            # 计算日期范围
            target_date = datetime.now() - timedelta(days=days)
            
            # 找到目标日期前的星标数
            for i, sg in enumerate(reversed(stargazers)):
                if sg.starred_at < target_date:
                    return len(stargazers) - i
            
            return 0
        except Exception as e:
            logger.error(f"获取星标历史时出错: {str(e)}")
            # 如果无法获取历史数据，使用当前星标数的估计值
            return int(repo.stargazers_count * 0.9)  # 假设之前的星标数是当前的90%
    
    def _process_repos(self, repos, category):
        """处理仓库数据并保存到数据库"""
        processed_repos = []
        
        for repo in repos:
            try:
                processed_repo = {
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "owner": repo["owner"]["login"],
                    "owner_avatar": repo["owner"]["avatar_url"],
                    "description": repo["description"] or "",
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"] or "Unknown",
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "category": category,
                    "fetch_date": datetime.now().strftime("%Y-%m-%d")
                }
                
                if category == "growing" and "growth_rate" in repo:
                    processed_repo["growth_rate"] = repo["growth_rate"]
                    processed_repo["stars_increased"] = repo["stars_increased"]
                
                processed_repos.append(processed_repo)
            except Exception as e:
                logger.error(f"处理仓库数据时出错: {str(e)}")
        
        # 保存到数据库
        if processed_repos:
            self.db.save_repos(processed_repos)
        
        return processed_repos
    
    def update_readme(self, trending_repos, growing_repos):
        """更新GitHub README文件"""
        logger.info("更新README文件...")
        
        # 创建Markdown表格
        trending_table = self._create_markdown_table(trending_repos, "最新热门仓库")
        growing_table = self._create_markdown_table(growing_repos, "增长最快的仓库", is_growing=True)
        
        # 读取当前README内容
        try:
            with open("README.md", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 查找更新标记
            start_mark = "<!-- TRENDING_REPOS_START -->"
            end_mark = "<!-- TRENDING_REPOS_END -->"
            
            if start_mark in content and end_mark in content:
                # 替换内容
                new_content = content.split(start_mark)[0] + start_mark + "\n\n"
                new_content += f"*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
                new_content += trending_table + "\n\n" + growing_table + "\n\n"
                new_content += end_mark + content.split(end_mark)[1]
                
                # 写入文件
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                logger.info("README更新成功")
            else:
                logger.warning("README中未找到更新标记")
        except Exception as e:
            logger.error(f"更新README时出错: {str(e)}")
    
    def _create_markdown_table(self, repos, title, is_growing=False):
        """创建Markdown格式的表格"""
        table = f"### {title}\n\n"
        
        if is_growing:
            table += "| 排名 | 仓库 | 语言 | ⭐ 星标 | 增长率 | 新增星标 |\n"
            table += "|------|------|------|---------|---------|----------|\n"
            
            for i, repo in enumerate(repos[:10], 1):
                growth_rate = repo.get("growth_rate", 0)
                stars_increased = repo.get("stars_increased", 0)
                table += f"| {i} | [{repo['full_name']}]({repo['url']}) | {repo['language']} | {repo['stars']} | {growth_rate:.2%} | +{stars_increased} |\n"
        else:
            table += "| 排名 | 仓库 | 语言 | ⭐ 星标 | 描述 |\n"
            table += "|------|------|------|---------|------|\n"
            
            for i, repo in enumerate(repos[:10], 1):
                description = repo['description'][:100] + "..." if repo['description'] and len(repo['description']) > 100 else repo['description']
                table += f"| {i} | [{repo['full_name']}]({repo['url']}) | {repo['language']} | {repo['stars']} | {description} |\n"
        
        return table
    
    def run(self):
        """运行抓取任务"""
        try:
            # 获取trending仓库
            trending_repos = self.fetch_trending_repos(days=1)
            
            # 获取增长最快的仓库
            growing_repos = self.fetch_fastest_growing(days=7)
            
            # 更新README
            self.update_readme(trending_repos, growing_repos)
            
            logger.info(f"成功获取 {len(trending_repos)} 个trending仓库和 {len(growing_repos)} 个增长最快的仓库")
            return trending_repos, growing_repos
        except Exception as e:
            logger.error(f"抓取任务执行失败: {str(e)}")
            return [], []

if __name__ == "__main__":
    fetcher = TrendingFetcher()
    fetcher.run() 