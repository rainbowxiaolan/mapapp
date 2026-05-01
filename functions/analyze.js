export async function onRequestPost(context) {
    const { request } = context;
    const body = await request.formData();
    const topic = body.get('topic')?.trim();
    if (!topic) {
        return new Response(JSON.stringify({ error: "请输入话题" }), { status: 400 });
    }

    // ----- 生成模拟统计数据（你可以替换成真实的检索/生成逻辑）-----
    const provinces = ["北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江",
        "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南",
        "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "台湾",
        "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
    ];

    const aggregated = {};
    let totalRecords = 0;
    provinces.forEach(p => {
        const positive = Math.floor(Math.random() * 1000);
        const negative = Math.floor(Math.random() * 500);
        const neutral = Math.floor(Math.random() * 700);
        const total = positive + negative + neutral;
        aggregated[p] = {
            positive, negative, neutral, total,
            emotion_index: (positive - negative) / total,
            dominant_emotion: positive > negative ? 'positive' : (negative > positive ? 'negative' : 'neutral')
        };
        totalRecords += total;
    });

    const summary = {
        total_records: totalRecords,
        province_count: provinces.length,
        overall_dominant_emotion: 'positive',
        overall_emotion_index: 0.22
    };

    const mapData = Object.keys(aggregated).map(p => ({
        name: p,
        value: aggregated[p].emotion_index
    }));

    // 生成 HTML 片段
    const resultHtml = `
    <div class="topic-section">
        <h2>分析话题：${topic}</h2>
        <div class="summary-stats">
            <div class="stat-item">
                <span class="stat-label">微博总数</span>
                <span class="stat-value">${summary.total_records.toLocaleString()}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">覆盖省份</span>
                <span class="stat-value">${summary.province_count}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">整体主导情绪</span>
                <span class="stat-value stat-emotion-${summary.overall_dominant_emotion}">
                    ${summary.overall_dominant_emotion === 'positive' ? '正向' : (summary.overall_dominant_emotion === 'negative' ? '负向' : '中性')}
                </span>
            </div>
            <div class="stat-item">
                <span class="stat-label">整体情绪指数</span>
                <span class="stat-value">${summary.overall_emotion_index.toFixed(3)}</span>
            </div>
        </div>
    </div>
    <div class="map-section">
        <h3>情绪分布地图</h3>
        <div class="map-legend">
            <div class="legend-item"><span class="legend-color legend-positive"></span><span>正向情绪</span></div>
            <div class="legend-item"><span class="legend-color legend-negative"></span><span>负向情绪</span></div>
            <div class="legend-item"><span class="legend-color legend-neutral"></span><span>中性情绪</span></div>
        </div>
        <div id="emotion-map-container" style="width:100%;height:550px;"></div>
    </div>
    <script>
        (function() {
            // 如果 ECharts 还没有加载（可能未在页面引入），等待
            if (typeof echarts === 'undefined') return;
            fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
                .then(res => res.json())
                .then(geoJson => {
                    echarts.registerMap('china', geoJson);
                    var myChart = echarts.init(document.getElementById('emotion-map-container'));
                    myChart.setOption({
                        title: { text: '微博热点话题情绪分布地图', subtext: '鼠标悬停查看详情', left:'center' },
                        tooltip: { trigger:'item' },
                        visualMap: {
                            min: -1, max: 1,
                            left:'left', top:'bottom',
                            text:['正向','负向'],
                            inRange: { color: ['#ef4444','#fbbf24','#10b981'] }
                        },
                        series: [{
                            name: '情绪指数',
                            type: 'map',
                            map: 'china',
                            data: ${JSON.stringify(mapData)},
                            label: { show: false },
                            emphasis: { label: { show: true } }
                        }]
                    });
                });
        })();
    </script>
    `;

    return new Response(resultHtml, {
        headers: { 'Content-Type': 'text/html' }
    });
}