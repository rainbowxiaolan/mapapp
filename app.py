# Flask应用主入口
# 微博热点话题情绪地图系统

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入服务模块
from services.collector import get_weibo_data_by_topic, get_collector
from services.preprocess import preprocess_records
from services.sentiment import batch_analyze_sentiment
from services.geo_parser import parse_locations
from services.aggregator import aggregate_by_province, build_table_data, get_aggregator
from services.visualizer import EmotionMapVisualizer
from services.ai_summary import generate_ai_summary

# 新增数据生成模块
from services.data_generator import get_or_generate_stats, ensure_all_provinces

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['JSON_AS_ASCII'] = False  # 支持中文

# 导入配置
from config.settings import get_config

# 获取配置
config = get_config()
app.config.update(config)


@app.route('/')
def index():
    """
    首页路由
    展示话题输入界面
    """
    return render_template('index.html')


@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    """
    分析路由
    处理话题分析请求并展示结果页
    """
    error_message = None
    topic = None
    map_html = None
    table_data = []
    summary = {}

    try:
        # 获取话题参数
        if request.method == 'POST':
            topic = request.form.get('topic', '').strip()
        else:
            topic = request.args.get('topic', '').strip()

        if not topic:
            error_message = "请输入一个话题"
            # 如果是AJAX请求，返回JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': error_message
                })
            return render_template('result.html',
                                 topic=topic or '未知话题',
                                 map_html='',
                                 table_data=[],
                                 summary={},
                                 error_message=error_message)

        # 步骤1：获取微博数据
        data_mode = app.config.get('DATA_SOURCE', {}).get('MODE', 'mock')
        use_real_crawler = data_mode == 'crawler'
        print(f"正在获取话题 '{topic}' 的微博数据...（使用{'真实爬虫' if use_real_crawler else 'Mock数据'}）")
        raw_data = get_weibo_data_by_topic(topic, use_real=use_real_crawler)

        if not raw_data:
            error_message = f"未找到话题 '{topic}' 相关的微博数据，请尝试其他话题（如：春节、世界杯、高考）"
            return render_template('result.html',
                                 topic=topic,
                                 map_html='',
                                 table_data=[],
                                 summary={},
                                 error_message=error_message)

        print(f"获取到 {len(raw_data)} 条微博数据")

        # 步骤2：数据清洗
        print("正在清洗数据...")
        cleaned_data = preprocess_records(raw_data)
        print(f"清洗后剩余 {len(cleaned_data)} 条有效数据")

        if not cleaned_data:
            error_message = "数据清洗后没有有效数据"
            return render_template('result.html',
                                 topic=topic,
                                 map_html='',
                                 table_data=[],
                                 summary={},
                                 error_message=error_message)

        # 步骤3：地理位置解析
        print("正在解析地理位置...")
        parsed_data = parse_locations(cleaned_data)

        # 过滤出有有效地理位置的记录
        from services.geo_parser import get_parser
        parser = get_parser()
        valid_data = parser.filter_valid_locations(parsed_data)
        print(f"有效地理位置数据 {len(valid_data)} 条")

        if not valid_data:
            error_message = "没有找到有效的地理位置数据"
            return render_template('result.html',
                                 topic=topic,
                                 map_html='',
                                 table_data=[],
                                 summary={},
                                 error_message=error_message)

        # 步骤4：情感分析
        print("正在进行情感分析...")
        analyzed_data = batch_analyze_sentiment(valid_data)
        print("情感分析完成")

        # 步骤5：数据聚合（使用 data_generator 生成百万级模拟数据）
        print("正在生成省份情绪数据...")
        # 提取 mock 数据的 sentiment 和 normalized_location（复用已有解析结果）
        mock_with_sentiment = []
        for rec in analyzed_data:
            if rec.get("normalized_location") and rec.get("sentiment"):
                mock_with_sentiment.append(rec)

        aggregated = get_or_generate_stats(topic, mock_with_sentiment)
        # 补全 34 个省份
        aggregated = ensure_all_provinces(aggregated)

        if not aggregated:
            error_message = "数据聚合失败，没有有效的省份数据"
            return render_template('result.html',
                                 topic=topic,
                                 map_html='',
                                 table_data=[],
                                 summary={},
                                 error_message=error_message)

        print(f"聚合完成，共 {len(aggregated)} 个省份")

        # 步骤6：构建表格数据（保留，但页面不展示）
        table_data = build_table_data(aggregated)

	# 步骤7.5：AI 智能解读
	print("正在生成AI智能解读...")
	ai_summary_text = generate_ai_summary(topic, table_data)

        # 步骤7：获取汇总统计
        aggregator = get_aggregator()
        summary = aggregator.get_summary_stats(aggregated)
        summary['province_count'] = 34  # 硬编码为 34 个省级行政区

        # 步骤8：生成地图
        print("正在生成地图...")
        visualizer = EmotionMapVisualizer()
        map_html = visualizer.render_map_html(aggregated)
        print("地图生成完成")

    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        error_message = f"处理过程中发生错误: {str(e)}"

    return render_template('result.html',
                     topic=topic,
                     map_html=map_html or '',
                     table_data=table_data,
                     summary=summary,
                     ai_summary=ai_summary_text,
                     error_message=error_message)


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return render_template('index.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return render_template('index.html'), 500


if __name__ == '__main__':
    print("=" * 50)
    print("微博热点话题情绪地图系统")
    print("=" * 50)
    print("正在启动服务器...")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)

    # 配置静态文件路由
    from flask import send_from_directory
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)

    # 开发模式启动
    app.run(debug=True, host='0.0.0.0', port=5000)