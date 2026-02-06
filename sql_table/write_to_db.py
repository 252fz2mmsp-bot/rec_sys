#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据导入脚本 - 将txt和csv文件数据导入MySQL数据库
"""

import pymysql
import csv
import os
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataImporter:
    """数据导入器"""
    
    def __init__(self, host='localhost', port=3306, user='root', 
                 password='123456', database='rec_sys'):
        """
        初始化数据库连接
        
        Args:
            host: 数据库主机
            port: 端口
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.connection_config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4'
        }
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(**self.connection_config)
            self.cursor = self.connection.cursor()
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("数据库连接已关闭")
    
    def create_tables(self, sql_file='create_tables.sql'):
        """
        执行建表SQL脚本
        
        Args:
            sql_file: SQL文件路径
        """
        try:
            if not os.path.exists(sql_file):
                logger.warning(f"SQL文件不存在: {sql_file}")
                return
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 移除注释并分割SQL语句
            lines = []
            for line in sql_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    lines.append(line)
            
            sql_content = ' '.join(lines)
            sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for sql in sql_statements:
                if sql:
                    try:
                        self.cursor.execute(sql)
                        self.connection.commit()
                        logger.info(f"执行SQL成功")
                    except Exception as e:
                        logger.error(f"执行SQL失败: {e}")
                        logger.error(f"SQL语句: {sql[:100]}...")
                        raise
            
            logger.info("数据表创建成功")
        except Exception as e:
            logger.error(f"创建数据表失败: {e}")
            raise
    
    def parse_datetime(self, time_str):
        """
        解析日期时间字符串
        
        Args:
            time_str: 时间字符串
            
        Returns:
            datetime对象或None
        """
        if not time_str or time_str.strip() == '' or time_str.strip() == '0':
            return None
        
        time_str = time_str.strip()
        
        # 尝试解析Unix时间戳
        if time_str.isdigit():
            try:
                timestamp = int(time_str)
                # 判断是秒级还是毫秒级时间戳
                if timestamp > 9999999999:  # 毫秒级
                    return datetime.fromtimestamp(timestamp / 1000)
                else:  # 秒级
                    return datetime.fromtimestamp(timestamp)
            except (ValueError, OSError) as e:
                logger.warning(f"无法解析时间戳: {time_str}, 错误: {e}")
                return None
        
        # 尝试多种日期格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y%m%d%H%M%S',
            '%Y%m%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"无法解析时间格式: {time_str}")
        return None
    
    def import_user_behavior(self, file_path, batch_size=1000):
        """
        导入用户行为数据
        
        Args:
            file_path: 行为数据txt文件路径
            batch_size: 批量插入大小
        """
        logger.info(f"开始导入用户行为数据: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return
        
        sql = """
        INSERT INTO user_behavior 
        (user_id, item_id, scene, app_type, app_version, position, event, 
         event_time, ip, country, province, city)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        batch_data = []
        total_count = 0
        error_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 使用制表符或逗号分割
                        parts = line.split('\t') if '\t' in line else line.split(',')
                        
                        if len(parts) < 11:
                            logger.warning(f"第{line_num}行数据列数不足: {line}")
                            error_count += 1
                            continue
                        
                        # 解析数据
                        user_id = parts[0].strip()
                        item_id = parts[1].strip()
                        scene = parts[2].strip() if len(parts) > 2 else None
                        app_type = parts[3].strip() if len(parts) > 3 else None
                        app_version = parts[4].strip() if len(parts) > 4 else None
                        position = parts[5].strip() if len(parts) > 5 else None
                        event = parts[6].strip() if len(parts) > 6 else None
                        event_time = self.parse_datetime(parts[7]) if len(parts) > 7 else None
                        ip = parts[8].strip() if len(parts) > 8 else None
                        country = parts[9].strip() if len(parts) > 9 else None
                        province = parts[10].strip() if len(parts) > 10 else None
                        city = parts[11].strip() if len(parts) > 11 else None
                        
                        batch_data.append((
                            user_id, item_id, scene, app_type, app_version, 
                            position, event, event_time, ip, country, province, city
                        ))
                        
                        # 批量插入
                        if len(batch_data) >= batch_size:
                            self.cursor.executemany(sql, batch_data)
                            self.connection.commit()
                            total_count += len(batch_data)
                            logger.info(f"已导入 {total_count} 条用户行为数据")
                            batch_data = []
                    
                    except Exception as e:
                        logger.error(f"第{line_num}行数据处理失败: {e}")
                        error_count += 1
                        continue
                
                # 插入剩余数据
                if batch_data:
                    self.cursor.executemany(sql, batch_data)
                    self.connection.commit()
                    total_count += len(batch_data)
            
            logger.info(f"用户行为数据导入完成: 成功{total_count}条, 失败{error_count}条")
        
        except Exception as e:
            logger.error(f"导入用户行为数据失败: {e}")
            self.connection.rollback()
            raise
    
    def import_user_info(self, file_path, batch_size=1000):
        """
        导入用户信息数据
        
        Args:
            file_path: 用户数据txt文件路径
            batch_size: 批量插入大小
        """
        logger.info(f"开始导入用户信息数据: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return
        
        sql = """
        INSERT INTO user_info 
        (uid, member_level, modeler_level, reg_time, sex, country, province, city, login_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        member_level=VALUES(member_level),
        modeler_level=VALUES(modeler_level),
        reg_time=VALUES(reg_time),
        sex=VALUES(sex),
        country=VALUES(country),
        province=VALUES(province),
        city=VALUES(city),
        login_time=VALUES(login_time)
        """
        
        batch_data = []
        total_count = 0
        error_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 使用制表符或逗号分割
                        parts = line.split('\t') if '\t' in line else line.split(',')
                        
                        if len(parts) < 9:
                            logger.warning(f"第{line_num}行数据列数不足: {line}")
                            error_count += 1
                            continue
                        
                        # 解析数据
                        uid = parts[0].strip()
                        member_level = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                        modeler_level = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                        reg_time = self.parse_datetime(parts[3]) if len(parts) > 3 else None
                        sex = parts[4].strip() if len(parts) > 4 else None
                        country = parts[5].strip() if len(parts) > 5 else None
                        province = parts[6].strip() if len(parts) > 6 else None
                        city = parts[7].strip() if len(parts) > 7 else None
                        login_time = self.parse_datetime(parts[8]) if len(parts) > 8 else None
                        
                        batch_data.append((
                            uid, member_level, modeler_level, reg_time, sex, 
                            country, province, city, login_time
                        ))
                        
                        # 批量插入
                        if len(batch_data) >= batch_size:
                            self.cursor.executemany(sql, batch_data)
                            self.connection.commit()
                            total_count += len(batch_data)
                            logger.info(f"已导入 {total_count} 条用户信息数据")
                            batch_data = []
                    
                    except Exception as e:
                        logger.error(f"第{line_num}行数据处理失败: {e}")
                        error_count += 1
                        continue
                
                # 插入剩余数据
                if batch_data:
                    self.cursor.executemany(sql, batch_data)
                    self.connection.commit()
                    total_count += len(batch_data)
            
            logger.info(f"用户信息数据导入完成: 成功{total_count}条, 失败{error_count}条")
        
        except Exception as e:
            logger.error(f"导入用户信息数据失败: {e}")
            self.connection.rollback()
            raise
    
    def import_item_info(self, file_path, batch_size=1000):
        """
        导入商品信息数据
        
        Args:
            file_path: 商品数据txt/csv文件路径（逗号分隔，有表头）
            batch_size: 批量插入大小
        """
        logger.info(f"开始导入商品信息数据: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return
        
        sql = """
        INSERT INTO item_info 
        (_id, group_name, first_level_category_name, second_level_category_name, 
         tags_name_list, cover_first, group_desc)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        group_name=VALUES(group_name),
        first_level_category_name=VALUES(first_level_category_name),
        second_level_category_name=VALUES(second_level_category_name),
        tags_name_list=VALUES(tags_name_list),
        cover_first=VALUES(cover_first),
        group_desc=VALUES(group_desc)
        """
        
        batch_data = []
        total_count = 0
        error_count = 0
        
        # 读取txt/csv文件（逗号分隔，有表头）
        # 读取txt/csv文件（逗号分隔，有表头）
        try:
            # 使用UTF-8编码读取
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                header = next(csv_reader)  # 读取表头
                logger.info(f"文件表头: {header}")
                
                for line_num, row in enumerate(csv_reader, 2):  # 从第2行开始
                    try:
                        if not row or all(not cell for cell in row):
                            continue
                        
                        if len(row) < 6:
                            logger.warning(f"第{line_num}行数据列数不足(需要至少6列): {row}")
                            error_count += 1
                            continue
                        
                        # 解析数据
                        _id = row[0].strip() if row[0] else None
                        group_name = row[1].strip() if len(row) > 1 and row[1] else None
                        first_level_category = row[2].strip() if len(row) > 2 and row[2] else None
                        second_level_category = row[3].strip() if len(row) > 3 and row[3] else None
                        tags_name_list = row[4].strip() if len(row) > 4 and row[4] else None
                        cover_first = row[5].strip() if len(row) > 5 and row[5] else None
                        group_desc = row[6].strip() if len(row) > 6 and row[6] else None
                        
                        batch_data.append((
                            _id, group_name, first_level_category, second_level_category,
                            tags_name_list, cover_first, group_desc
                        ))
                        
                        # 批量插入
                        if len(batch_data) >= batch_size:
                            self.cursor.executemany(sql, batch_data)
                            self.connection.commit()
                            total_count += len(batch_data)
                            logger.info(f"已导入 {total_count} 条商品信息数据")
                            batch_data = []
                    
                    except Exception as e:
                        logger.error(f"第{line_num}行数据处理失败: {e}")
                        error_count += 1
                        continue
                
                # 插入剩余数据
                if batch_data:
                    self.cursor.executemany(sql, batch_data)
                    self.connection.commit()
                    total_count += len(batch_data)
                
                logger.info(f"商品信息数据导入完成: 成功{total_count}条, 失败{error_count}条")
        
        except Exception as e:
            logger.error(f"导入商品信息数据失败: {e}")
            self.connection.rollback()
            raise


def main():
    """主函数"""
    # 当前目录的文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件路径配置
    behavior_file = os.path.join(current_dir, 'action_en_2025-11-30.txt')
    user_file = os.path.join(current_dir, 'ods_user_en.txt')
    item_file = os.path.join(current_dir, 'model_export.txt')  # 改为txt格式
    sql_file = os.path.join(current_dir, 'create_tables.sql')
    
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'database': 'rec_sys'
    }
    
    importer = DataImporter(**db_config)
    
    try:
        # 连接数据库
        importer.connect()
        
        # 创建表
        logger.info("=" * 50)
        logger.info("步骤1: 创建数据表")
        logger.info("=" * 50)
        importer.create_tables(sql_file)
        
        # # 导入用户行为数据
        logger.info("\n" + "=" * 50)
        logger.info("步骤2: 导入用户行为数据")
        logger.info("=" * 50)
        importer.import_user_behavior(behavior_file)
        
        # 导入用户信息数据
        logger.info("\n" + "=" * 50)
        logger.info("步骤3: 导入用户信息数据")
        logger.info("=" * 50)
        importer.import_user_info(user_file)
        
        # 导入商品信息数据
        logger.info("\n" + "=" * 50)
        logger.info("步骤4: 导入商品信息数据")
        logger.info("=" * 50)
        importer.import_item_info(item_file)
        
        logger.info("\n" + "=" * 50)
        logger.info("所有数据导入完成!")
        logger.info("=" * 50)
    
    except Exception as e:
        logger.error(f"数据导入过程出错: {e}")
        raise
    
    finally:
        importer.close()


if __name__ == '__main__':
    main()
