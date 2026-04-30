# services/visualizer.py
# 地图可视化模块 - 从本地 static/js 加载 ECharts 和 china.js，无外部 CDN 依赖

import json
from typing import Dict, Any

ALL_PROVINCES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
    "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
    "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
]


class EmotionMapVisualizer:
    """情绪地图可视化器 - 本地 ECharts"""

    def render_map_html(self, aggregated: Dict[str, Dict[str, Any]],
                        width: str = "100%", height: str = "550px") -> str:
        # 补全省份并生成数据
        province_stats = {}
        for province in ALL_PROVINCES:
            if province in aggregated:
                province_stats[province] = aggregated[province]
            else:
                province_stats[province] = {
                    "positive": 0, "negative": 0, "neutral": 0, "total": 0,
                    "emotion_index": 0, "dominant_emotion": "neutral"
                }

        series_data = [{"name": p, "value": s["emotion_index"]} for p, s in province_stats.items()]

        province_stats_json = json.dumps(province_stats, ensure_ascii=False)
        series_data_json = json.dumps(series_data, ensure_ascii=False)

        html = f"""
<div id="emotion-map-container" style="width: {width}; height: {height};"></div>

<!-- 顺序加载本地 ECharts 核心库和地图数据 -->
<script src="/static/js/echarts.min.js"></script>
<script src="/static/js/china.js"></script>

<script>
    (function() {{
        var container = document.getElementById('emotion-map-container');
        if (!container) {{
            console.error('找不到地图容器');
            return;
        }}
        var provinceStats = {province_stats_json};
        var seriesData = {series_data_json};

        // 确保 echarts 和地图数据均已加载（china.js 会注册 'china' 地图）
        if (typeof echarts === 'undefined') {{
            container.innerHTML = '<div style="padding:20px;text-align:center;">ECharts 加载失败，请检查 static/js/echarts.min.js 是否存在</div>';
            return;
        }}

        try {{
            var myChart = echarts.init(container);
            function formatter(params) {{
                var province = params.name;
                var info = provinceStats[province];
                if (!info) return '<div>暂无数据</div>';
                var dominantMap = {{ 'positive': '正向', 'negative': '负向', 'neutral': '中性' }};
                var icon = info.dominant_emotion === 'positive' ? '🟢' :
                           info.dominant_emotion === 'negative' ? '🔴' : '⚪';
                return '<div style="padding: 8px; line-height: 1.5; font-size: 12px;">' +
                       '<strong>' + province + ' ' + icon + '</strong><br/>' +
                       '<span style="color:#10b981;">正向: ' + info.positive + '</span><br/>' +
                       '<span style="color:#ef4444;">负向: ' + info.negative + '</span><br/>' +
                       '<span style="color:#6b7280;">中性: ' + info.neutral + '</span><br/>' +
                       '<strong>总数: ' + info.total + '</strong><br/>' +
                       '<span style="font-weight:bold;">主导: ' + dominantMap[info.dominant_emotion] + '</span><br/>' +
                       '<span style="color:#6366f1;">情绪指数: ' + info.emotion_index.toFixed(2) + '</span></div>';
            }}

            myChart.setOption({{
                title: {{
                    text: '微博热点话题情绪分布地图',
                    subtext: '鼠标悬停查看详情',
                    left: 'center',
                    top: 10,
                    textStyle: {{ fontSize: 20, color: '#333' }},
                    subtextStyle: {{ fontSize: 12, color: '#666' }}
                }},
                tooltip: {{
                    trigger: 'item',
                    formatter: formatter,
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    borderColor: '#aaa',
                    borderWidth: 1
                }},
                visualMap: {{
                    min: -1,
                    max: 1,
                    calculable: true,
                    inRange: {{ color: ['#ef4444', '#fbbf24', '#10b981'] }},
                    outOfRange: {{ color: ['#e5e7eb'] }},
                    text: ['正向', '负向'],
                    textStyle: {{ color: '#333' }}
                }},
                series: [{{
                    name: '情绪指数',
                    type: 'map',
                    map: 'china',
                    roam: true,
                    data: seriesData,
                    label: {{ show: false }},
                    emphasis: {{ label: {{ show: true }} }},
                    itemStyle: {{ borderColor: '#aaa', borderWidth: 0.5 }}
                }}]
            }});
            window.addEventListener('resize', function() {{ myChart.resize(); }});
            console.log('地图渲染成功');
        }} catch(e) {{
            console.error('地图渲染失败:', e);
            container.innerHTML = '<div style="padding:20px;text-align:center;">地图渲染失败：' + e.message + '</div>';
        }}
    }})();
</script>
"""
        return html


def render_emotion_map(aggregated):
    visualizer = EmotionMapVisualizer()
    return visualizer.render_map_html(aggregated)