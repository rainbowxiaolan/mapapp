// 最简前端：话题标签填充输入框，并让表单正常提交（不拦截任何事件）
(function() {
    const searchForm = document.getElementById('searchForm');
    const topicInput = document.getElementById('topic');
    const topicTags = document.querySelectorAll('.topic-tag');

    if (topicTags.length && topicInput && searchForm) {
        topicTags.forEach(tag => {
            tag.addEventListener('click', function(e) {
                e.preventDefault();
                const topic = this.getAttribute('data-topic');
                if (topic) {
                    topicInput.value = topic;
                    // 直接提交表单（不经过 fetch，页面会正常刷新）
                    searchForm.submit();
                }
            });
        });
    }
})();