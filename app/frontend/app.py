"""
RecSys Admin Console - Streamlit 前端应用
用于展示数据、调试接口，并为未来接入推荐算法和搜索服务预留 UI 空间
"""
import streamlit as st
import requests
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime

# ==================== 全局配置 ====================
API_BASE_URL = "http://localhost:8000/api/v1"

# 页面配置
st.set_page_config(
    page_title="RecSys Admin Console",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== 通用工具函数 ====================

def fetch_data(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    """
    通用的 API 请求函数
    
    Args:
        endpoint: API 端点路径（不含 base_url）
        params: 查询参数字典
    
    Returns:
        API 响应的 JSON 数据，如果请求失败返回 None
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到后端服务，请确保 FastAPI 服务已启动！")
        return None
    except requests.exceptions.Timeout:
        st.error("⏱️ 请求超时，请检查网络连接或后端服务状态。")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP 错误: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ 未知错误: {str(e)}")
        return None


def format_datetime(dt_str: Optional[str]) -> str:
    """格式化日期时间字符串"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return dt_str


# ==================== 页面 1: 数据管理 ====================

def page_data_manager():
    """数据管理页面 - 展示用户和商品列表"""
    st.title("🗃️ 数据管理 (Data Manager)")
    st.markdown("---")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 左侧：用户列表
    with col1:
        st.subheader("👤 用户列表 (Users)")
        
        # 获取用户数据
        users_data = fetch_data("/users/", params={"skip": 0, "limit": 50})
        
        if users_data and users_data.get("data"):
            data = users_data["data"]
            items = data.get("items", [])
            total = data.get("total", 0)
            
            # 显示统计指标
            st.metric("总用户数", total)
            st.metric("当前加载数量", len(items))
            
            # 转换为 DataFrame 并展示
            if items:
                df_users = pd.DataFrame(items)
                # 选择关键列展示
                display_columns = ["uid", "sex", "city", "member_level", "reg_time"]
                available_columns = [col for col in display_columns if col in df_users.columns]
                
                if available_columns:
                    df_display = df_users[available_columns].copy()
                    # 格式化时间列
                    if "reg_time" in df_display.columns:
                        df_display["reg_time"] = df_display["reg_time"].apply(
                            lambda x: format_datetime(x) if pd.notna(x) else "N/A"
                        )
                    st.dataframe(df_display, use_container_width=True, height=400)
                else:
                    st.dataframe(df_users, use_container_width=True, height=400)
            else:
                st.info("📭 暂无用户数据")
        else:
            st.warning("⚠️ 无法加载用户数据")
    
    # 右侧：商品列表
    with col2:
        st.subheader("📦 商品列表 (Items)")
        
        # 获取商品数据
        items_data = fetch_data("/items/", params={"skip": 0, "limit": 50})
        
        if items_data and items_data.get("data"):
            data = items_data["data"]
            items = data.get("items", [])
            total = data.get("total", 0)
            
            # 显示统计指标
            st.metric("总商品数", total)
            st.metric("当前加载数量", len(items))
            
            # 转换为 DataFrame 并展示
            if items:
                df_items = pd.DataFrame(items)
                # 选择关键列展示
                display_columns = ["id", "group_name", "first_level_category_name", 
                                 "second_level_category_name"]
                available_columns = [col for col in display_columns if col in df_items.columns]
                
                if available_columns:
                    df_display = df_items[available_columns].copy()
                    st.dataframe(df_display, use_container_width=True, height=400)
                else:
                    st.dataframe(df_items, use_container_width=True, height=400)
            else:
                st.info("📭 暂无商品数据")
        else:
            st.warning("⚠️ 无法加载商品数据")


# ==================== 页面 2: 用户画像 ====================

def page_user_profile():
    """用户画像页面 - 查看特定用户的详细信息"""
    st.title("👤 用户画像 (User Profile)")
    st.markdown("---")
    
    # 创建输入区域
    col1, col2 = st.columns([3, 1])
    with col1:
        user_id = st.text_input("🔍 请输入用户 ID (User ID)", placeholder="例如: user_12345")
    with col2:
        st.write("")  # 占位
        st.write("")  # 占位
        query_button = st.button("查询", type="primary", use_container_width=True)
    
    # 查询用户信息
    if query_button and user_id:
        with st.spinner("正在查询用户信息..."):
            user_data = fetch_data(f"/users/{user_id}")
            
            if user_data and user_data.get("data"):
                user_info = user_data["data"]
                
                st.success(f"✅ 找到用户: {user_id}")
                st.markdown("---")
                
                # 显示用户详细信息
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 📋 基本信息")
                    st.write(f"**用户 ID:** {user_info.get('uid', 'N/A')}")
                    st.write(f"**性别:** {user_info.get('sex', 'N/A')}")
                    st.write(f"**国家:** {user_info.get('country', 'N/A')}")
                    st.write(f"**省份:** {user_info.get('province', 'N/A')}")
                    st.write(f"**城市:** {user_info.get('city', 'N/A')}")
                
                with col2:
                    st.markdown("### 🎖️ 会员信息")
                    member_status = "✅ 是" if user_info.get('member_level', 0) == 1 else "❌ 否"
                    modeler_status = "✅ 是" if user_info.get('modeler_level', 0) == 1 else "❌ 否"
                    st.write(f"**会员身份:** {member_status}")
                    st.write(f"**建模师身份:** {modeler_status}")
                
                with col3:
                    st.markdown("### ⏰ 时间信息")
                    st.write(f"**注册时间:** {format_datetime(user_info.get('reg_time'))}")
                    st.write(f"**上次登录:** {format_datetime(user_info.get('login_time'))}")
                    st.write(f"**记录创建:** {format_datetime(user_info.get('created_at'))}")
                
                # JSON 详情（可折叠）
                with st.expander("📄 查看完整 JSON 数据"):
                    st.json(user_info)
                
                st.markdown("---")
                
                # 预留位置：用户行为时间线
                st.info("💡 **功能预留**: 此处未来将展示该用户的行为流水 (User Behavior Timeline)")
                st.markdown("""
                **计划展示内容：**
                - 📅 用户浏览历史
                - 🛒 购买记录
                - ⭐ 收藏商品
                - 💬 评论互动
                - 📊 行为趋势图表
                """)
                
            else:
                st.error(f"❌ 未找到用户 ID 为 '{user_id}' 的用户")
    
    elif query_button and not user_id:
        st.warning("⚠️ 请输入用户 ID")


# ==================== 页面 3: 算法调试 ====================

def page_algo_debugger():
    """算法调试页面 - 推荐和搜索功能测试"""
    st.title("🛠️ 算法调试 (Algo Debugger)")
    st.markdown("---")
    
    # 创建两个 Tab 标签页
    tab1, tab2 = st.tabs(["🎯 推荐模拟", "🔍 搜索测试"])
    
    # ========== Tab 1: 推荐模拟 ==========
    with tab1:
        st.subheader("🎯 推荐模拟 (Recommendation Simulator)")
        st.markdown("为指定用户生成个性化推荐列表")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            rec_user_id = st.text_input(
                "目标用户 ID", 
                placeholder="例如: user_12345",
                key="rec_user_id"
            )
        
        with col2:
            algo_model = st.selectbox(
                "选择推荐算法",
                options=["Random (随机推荐)", "Popular (热门推荐)", "ItemCF (协同过滤)"],
                index=0
            )
        
        with col3:
            st.write("")  # 占位
            st.write("")  # 占位
            rec_button = st.button("生成推荐", type="primary", use_container_width=True)
        
        if rec_button and rec_user_id:
            st.markdown("---")
            st.info("🚧 **功能开发中**: 当前展示 Mock 数据，实际推荐接口尚未实现")
            
            # TODO: 未来此处应调用实际的推荐接口
            # Example: recommend_data = fetch_data(f"/recommend/{rec_user_id}", 
            #                                       params={"model": algo_model, "top_k": 10})
            
            # Mock 推荐结果
            st.success(f"✅ 为用户 `{rec_user_id}` 生成推荐（算法: {algo_model}）")
            
            mock_recommendations = [
                {"rank": 1, "item_id": "item_001", "score": 0.95, "title": "3D打印机 Pro Max"},
                {"rank": 2, "item_id": "item_002", "score": 0.89, "title": "建模软件会员套餐"},
                {"rank": 3, "item_id": "item_003", "score": 0.87, "title": "高精度树脂材料"},
                {"rank": 4, "item_id": "item_004", "score": 0.82, "title": "创意模型设计课程"},
                {"rank": 5, "item_id": "item_005", "score": 0.78, "title": "UV固化灯"},
            ]
            
            # 以卡片形式展示推荐结果
            for i in range(0, len(mock_recommendations), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(mock_recommendations):
                        rec = mock_recommendations[i + j]
                        with col:
                            with st.container():
                                st.markdown(f"""
                                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; 
                                            background-color: #f9f9f9; margin-bottom: 10px;">
                                    <h4>🏆 #{rec['rank']} - {rec['title']}</h4>
                                    <p><strong>商品 ID:</strong> {rec['item_id']}</p>
                                    <p><strong>推荐分数:</strong> <span style="color: #ff6b6b; 
                                       font-size: 1.2em; font-weight: bold;">{rec['score']:.2f}</span></p>
                                </div>
                                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.code("""
# TODO: 实际实现代码示例
def get_recommendations(user_id: str, model: str, top_k: int = 10):
    endpoint = f"/recommend/{user_id}"
    params = {"model": model, "top_k": top_k}
    return fetch_data(endpoint, params)
            """, language="python")
        
        elif rec_button and not rec_user_id:
            st.warning("⚠️ 请输入目标用户 ID")

    # ========== Tab 2: 搜索测试 (修改后) ==========
    with tab2:
        st.subheader("🔍 搜索效果对比 (Search Comparison)")
        st.markdown("对比 **传统关键词匹配** 与 **智能分词搜索** 的结果差异")
        
        col_input, col_btn = st.columns([4, 1])
        
        with col_input:
            search_query = st.text_input(
                "输入搜索关键词 (尝试输入模糊词，如 '打印耗材')",
                placeholder="例如: 3D打印机",
                key="search_query"
            )
        
        with col_btn:
            st.write("") 
            st.write("") 
            search_button = st.button("开始比对", type="primary", use_container_width=True)
        
        if search_button and search_query:
            st.markdown("---")
            
            # 创建左右对比布局
            col_basic, col_smart = st.columns(2)
            
            # --- 左侧：一般搜索 (Mock) ---
            with col_basic:
                st.info("🔡 **方案 A: 一般搜索 (LIKE '%kw%')**")
                st.caption("逻辑: 仅匹配完全包含输入字符串的商品标题。")
                
                # Mock 逻辑：如果不包含明确的词，模拟找不到
                mock_basic_results = []
                if "3D" in search_query or "打印" in search_query:
                    mock_basic_results = [
                        {"id": "101", "title": "3D打印机 Pro", "match": "完全匹配"},
                        {"id": "102", "title": "家用3D打印机", "match": "完全匹配"},
                    ]
                
                if mock_basic_results:
                    st.dataframe(
                        pd.DataFrame(mock_basic_results), 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.warning("🚫 无匹配结果 (关键词未完全命中)")

            # --- 右侧：分词搜索 (Mock) ---
            with col_smart:
                st.success("🧠 **方案 B: 分词/语义搜索 (Tokenizer)**")
                st.caption("逻辑: 对输入进行分词、去除停用词、同义词扩展，计算相关度。")
                
                # Mock 分词展示
                st.markdown("##### 🛠️ 分词解析:")
                # 简单的模拟分词
                tokens = search_query.replace(" ", "").replace("3D", "3D ").split()
                if not tokens: tokens = [search_query]
                
                # 展示 Tags
                token_html = "".join([f'<span style="background-color: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 12px; margin-right: 5px; font-size: 0.9em;">{t}</span>' for t in tokens])
                st.markdown(token_html, unsafe_allow_html=True)
                
                st.write("") # Spacer

                # Mock 智能结果 (总是有更多结果)
                mock_smart_results = [
                    {"title": "3D打印机 Pro Max", "score": 0.98, "reason": "核心词命中"},
                    {"title": "各种打印耗材套餐", "score": 0.85, "reason": "同义词扩展"},
                    {"title": "高精度树脂(适配打印)", "score": 0.72, "reason": "语义相关"},
                    {"title": "模型后期处理工具", "score": 0.60, "reason": "关联推荐"},
                ]
                
                df_smart = pd.DataFrame(mock_smart_results)
                st.dataframe(
                    df_smart,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "score": st.column_config.ProgressColumn(
                            "相关度", format="%.2f", min_value=0, max_value=1
                        )
                    }
                )

            st.markdown("---")
            st.markdown("#### 📝 对比总结")
            st.markdown(f"""
            - **一般搜索**: 仅找到了 **{len(mock_basic_results)}** 个严格匹配的商品，容易受错别字或用户表达习惯影响。
            - **分词搜索**: 识别出了 `{tokens}` 等特征，召回了 **{len(mock_smart_results)}** 个潜在相关商品，包括同义词和相关品类。
            """)
            
            # 代码预览区
            with st.expander("查看后端实现逻辑差异 (伪代码)"):
                col_code1, col_code2 = st.columns(2)
                with col_code1:
                    st.code("""
# 一般搜索
sql = "SELECT * FROM items WHERE title LIKE :q"
db.execute(sql, {"q": f"%{query}%"})
                    """, language="python")
                with col_code2:
                    st.code("""
# 分词搜索
tokens = tokenizer.cut(query)
# ElasticSearch / Vector Search
query = {
    "bool": {
        "should": [{"match": {"title": t}} for t in tokens]
    }
}
es.search(index="items", body=query)
                    """, language="python")
        
        elif search_button and not search_query:
            st.warning("⚠️ 请输入搜索关键词")


# ==================== 主应用逻辑 ====================

def main():
    """主应用入口"""
    
    # 侧边栏导航
    st.sidebar.title("🎯 RecSys Console")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "📑 导航菜单",
        options=[
            "🗃️ 数据管理 (Data Manager)",
            "👤 用户画像 (User Profile)",
            "🛠️ 算法调试 (Algo Debugger)"
        ],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ 系统配置")
    st.sidebar.text(f"API 地址:\n{API_BASE_URL}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 系统状态")
    
    # 检查后端连接状态
    try:
        health_check = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/", timeout=2)
        if health_check.status_code == 200:
            st.sidebar.success("✅ 后端服务正常")
        else:
            st.sidebar.error("❌ 后端服务异常")
    except:
        st.sidebar.error("❌ 后端服务未启动")
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 **提示**: 确保 FastAPI 后端服务运行在 http://localhost:8000")
    
    # 根据选择的页面渲染对应内容
    if page == "🗃️ 数据管理 (Data Manager)":
        page_data_manager()
    elif page == "👤 用户画像 (User Profile)":
        page_user_profile()
    elif page == "🛠️ 算法调试 (Algo Debugger)":
        page_algo_debugger()


if __name__ == "__main__":
    main()
