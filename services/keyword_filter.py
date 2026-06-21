"""
关键词自动审查服务（Python原生实现，无需第三方敏感词库）
支持：reject词(拒绝发布)、warning词(进入人工审核)
使用 pyahocorasick 进行高效多关键词匹配（若安装了该库）
否则使用简单的字符串查找（关键词较少时够用）
"""

import re
import os

# 全局关键词缓存
_keywords_cache = []  # [(keyword, level), ...]
_ahocorasick_automaton = None

USE_AHOCORASICK = False
try:
    import ahocorasick
    USE_AHOCORASICK = True
except ImportError:
    pass


def _load_keywords_from_db():
    """从数据库加载关键词到内存缓存"""
    from app import db
    from app.models import Keyword

    try:
        keywords = Keyword.query.filter_by(is_active=1).all()
        return [(k.keyword, k.level) for k in keywords]
    except Exception:
        return []


def _build_ahocorasick():
    """构建Aho-Corasick自动机（高效多关键词匹配）"""
    global _ahocorasick_automaton, _keywords_cache
    _keywords_cache = _load_keywords_from_db()

    if not USE_AHOCORASICK or not _keywords_cache:
        return None

    automaton = ahocorasick.Automaton()
    for keyword, level in _keywords_cache:
        automaton.add_word(keyword, (keyword, level))
    automaton.make_automaton()
    _ahocorasick_automaton = automaton
    return automaton


def _build_simple_trie():
    """构建简单的关键词列表（用于降级方案）"""
    global _keywords_cache
    _keywords_cache = _load_keywords_from_db()


def get_keywords():
    """获取关键词缓存"""
    global _keywords_cache
    if not _keywords_cache:
        _build_simple_trie()
    return _keywords_cache


def refresh_cache():
    """刷新关键词缓存（管理后台修改关键词后调用）"""
    global _ahocorasick_automaton
    _ahocorasick_automaton = None
    _build_simple_trie()
    if USE_AHOCORASICK:
        _build_ahocorasick()


def check_text(text):
    """
    检查文本是否包含敏感词
    返回: {'passed': bool, 'action': str, 'hits': [{'keyword': str, 'level': str}]}
    """
    if not text or not text.strip():
        return {'passed': True, 'action': 'approve', 'hits': []}

    keywords = get_keywords()
    if not keywords:
        return {'passed': True, 'action': 'approve', 'hits': []}

    hits = []
    text_lower = text.lower()

    # 使用ahocorasick高效匹配
    if USE_AHOCORASICK and _ahocorasick_automaton:
        for end_idx, (keyword, level) in _ahocorasick_automaton.iter(text_lower):
            hits.append({'keyword': keyword, 'level': level})
    else:
        # 简单匹配（关键词较少时够用）
        for keyword, level in keywords:
            if keyword.lower() in text_lower:
                hits.append({'keyword': keyword, 'level': level})

    # 去重
    seen = set()
    unique_hits = []
    for h in hits:
        if h['keyword'] not in seen:
            seen.add(h['keyword'])
            unique_hits.append(h)
    hits = unique_hits

    # 判断处理动作 (level: 1=警告/review, 2=拒绝/reject)
    has_reject = any(h['level'] == 2 for h in hits)
    has_warning = any(h['level'] == 1 for h in hits)

    if has_reject:
        return {'passed': False, 'action': 'reject', 'hits': hits}
    elif has_warning:
        return {'passed': False, 'action': 'review', 'hits': hits}
    else:
        return {'passed': True, 'action': 'approve', 'hits': []}


def check_post_content(title, content, images=None):
    """
    检查帖子内容（标题+正文）
    返回审核结果
    """
    full_text = f"{title or ''} {content or ''}"
    return check_text(full_text)


def async_refresh():
    """在后台线程中刷新缓存，避免阻塞请求"""
    import threading
    t = threading.Thread(target=refresh_cache)
    t.daemon = True
    t.start()
