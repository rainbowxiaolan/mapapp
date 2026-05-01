(function() {
    const searchForm = document.getElementById('searchForm');
    const topicInput = document.getElementById('topic');
    const resultArea = document.getElementById('resultArea');

    // 点击热门标签自动填入并搜索
    document.querySelectorAll('.topic-tag').forEach(tag => {
        tag.addEventListener('click', function(e) {
            e.preventDefault();
            topicInput.value = this.getAttribute('data-topic');
            searchForm.dispatchEvent(new Event('submit'));
        });
    });

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const topic = topicInput.value.trim();
        if (!topic) return;

        // 显示加载状态
        resultArea.innerHTML = '<p style="text-align:center;padding:20px;">正在分析数据，请稍候……</p>';

        try {
            const formData = new FormData();
            formData.append('topic', topic);
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                throw new Error('服务器错误');
            }
            const html = await response.text();
            resultArea.innerHTML = html;
        } catch (error) {
            resultArea.innerHTML = '<p style="color:red;text-align:center;">分析失败，请稍后重试。</p>';
        }
    });
})();
