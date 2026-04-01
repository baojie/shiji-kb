/**
 * 语义标注阅读增强交互脚本
 * Semantic Reading Enhancement Interactive Script
 */

// ========== 全局状态 ==========

const state = {
    annotationMode: 'full',
    hiddenTypes: new Set(),
    selectedEntity: null,
    entityData: new Map(), // 存储每个实体的详细信息
};

// ========== 初始化 ==========

document.addEventListener('DOMContentLoaded', () => {
    console.log('语义阅读系统初始化...');

    initializeControlPanel();
    initializeEntityInteractions();
    collectEntityData();

    console.log('初始化完成');
});

// ========== 控制面板 ==========

function initializeControlPanel() {
    // 浮动按钮切换面板
    const toggleBtn = document.getElementById('control-toggle');
    const panel = document.getElementById('control-panel');

    if (toggleBtn && panel) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            panel.classList.toggle('active');
        });

        // 点击面板外关闭（不包括浮动按钮）
        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target) &&
                !toggleBtn.contains(e.target) &&
                panel.classList.contains('active')) {
                panel.classList.remove('active');
            }
        });

        // 点击面板内不关闭
        panel.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // 标注模式切换
    const modeSelect = document.getElementById('annotation-mode');
    if (modeSelect) {
        modeSelect.addEventListener('change', (e) => {
            changeAnnotationMode(e.target.value);
        });
    }

    // 生成实体类型过滤器
    generateEntityFilters();

    // 全选/全不选按钮
    const selectAllBtn = document.getElementById('select-all-types');
    const deselectAllBtn = document.getElementById('deselect-all-types');

    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            toggleAllEntityTypes(true);
        });
    }

    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => {
            toggleAllEntityTypes(false);
        });
    }
}

function changeAnnotationMode(mode) {
    state.annotationMode = mode;

    // 强制同步更新DOM属性
    const body = document.body;
    body.setAttribute('data-annotation-mode', mode);

    // 强制浏览器重新计算样式（触发reflow）
    void body.offsetHeight;

    console.log(`切换标注模式: ${mode}`);
}

function generateEntityFilters() {
    const filterContainer = document.getElementById('entity-filters');
    if (!filterContainer) return;

    // 获取所有实体类型
    const entityTypes = new Set();
    document.querySelectorAll('.entity').forEach(entity => {
        const className = Array.from(entity.classList).find(c => c.startsWith('entity-'));
        if (className) {
            entityTypes.add(className.replace('entity-', ''));
        }
    });

    // 创建复选框
    const sortedTypes = Array.from(entityTypes).sort();
    sortedTypes.forEach(type => {
        const label = document.querySelector(`.entity-${type}`)?.dataset.type || type;
        const count = document.querySelectorAll(`.entity-${type}`).length;

        const checkbox = document.createElement('label');
        checkbox.innerHTML = `
            <input type="checkbox" checked data-entity-type="${type}">
            <span>${label} (${count})</span>
        `;

        checkbox.querySelector('input').addEventListener('change', (e) => {
            toggleEntityType(type, e.target.checked);
        });

        filterContainer.appendChild(checkbox);
    });
}

function toggleEntityType(type, visible) {
    if (visible) {
        state.hiddenTypes.delete(type);
    } else {
        state.hiddenTypes.add(type);
    }

    // 更新DOM - 使用CSS类而不是直接修改style
    document.querySelectorAll(`.entity-${type}`).forEach(entity => {
        if (visible) {
            entity.classList.remove('hidden');
        } else {
            entity.classList.add('hidden');
        }
    });

    console.log(`${visible ? '显示' : '隐藏'}实体类型: ${type}`);
}

function toggleAllEntityTypes(visible) {
    const filterContainer = document.getElementById('entity-filters');
    if (!filterContainer) return;

    // 获取所有复选框并更新状态
    const checkboxes = filterContainer.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        const type = checkbox.dataset.entityType;

        // 更新复选框状态
        checkbox.checked = visible;

        // 更新实体显示状态
        toggleEntityType(type, visible);
    });

    console.log(`${visible ? '全选' : '全不选'}所有实体类型`);
}

// ========== 实体交互 ==========

function initializeEntityInteractions() {
    document.querySelectorAll('.entity').forEach(entity => {
        // 点击事件
        entity.addEventListener('click', (e) => {
            e.stopPropagation();
            handleEntityClick(entity);
        });

        // 双击事件（可选：跳转到相关内容）
        entity.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            handleEntityDoubleClick(entity);
        });
    });

    // 点击空白处关闭信息面板
    document.addEventListener('click', () => {
        if (state.selectedEntity) {
            closeInfoPanel();
        }
    });

    // 信息面板点击不传播
    const infoPanel = document.getElementById('info-panel');
    if (infoPanel) {
        infoPanel.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    // 点击遮罩层关闭面板
    const overlay = document.getElementById('info-panel-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeInfoPanel);
    }
}

function handleEntityClick(entity) {
    // 取消之前的选中
    if (state.selectedEntity) {
        state.selectedEntity.classList.remove('active');
    }

    // 选中当前实体
    state.selectedEntity = entity;
    entity.classList.add('active');

    // 显示详细信息
    showEntityInfo(entity);
}

function handleEntityDoubleClick(entity) {
    const canonical = entity.dataset.canonical;
    console.log(`双击实体: ${canonical}`);

    // 查找所有同名实体
    const sameEntities = findSameEntities(canonical);
    highlightEntities(sameEntities);
}

function findSameEntities(canonical) {
    const entities = [];
    document.querySelectorAll('.entity').forEach(entity => {
        if (entity.dataset.canonical === canonical) {
            entities.push(entity);
        }
    });
    return entities;
}

function highlightEntities(entities) {
    // 清除之前的高亮
    document.querySelectorAll('.entity.active').forEach(e => {
        e.classList.remove('active');
    });

    // 高亮所有匹配实体
    entities.forEach(entity => {
        entity.classList.add('active');
    });

    console.log(`高亮 ${entities.length} 个同名实体`);
}

// ========== 信息面板 ==========

function showEntityInfo(entity) {
    const infoPanel = document.getElementById('info-panel');
    const infoContent = document.getElementById('info-content');

    if (!infoPanel || !infoContent) return;

    const type = entity.dataset.type;
    const canonical = entity.dataset.canonical;
    const display = entity.textContent;
    const entityId = entity.dataset.entityId;

    // 查找所有同名实体
    const sameEntities = findSameEntities(canonical);
    const occurrences = sameEntities.length;

    // 生成信息内容
    infoContent.innerHTML = `
        <h3>${display}</h3>

        <div class="entity-info">
            <div class="info-field">
                <div class="info-label">类型</div>
                <div class="info-value">${type}</div>
            </div>

            ${canonical !== display ? `
            <div class="info-field">
                <div class="info-label">规范名</div>
                <div class="info-value">${canonical}</div>
            </div>
            ` : ''}

            <div class="info-field">
                <div class="info-label">出现次数</div>
                <div class="info-value">${occurrences} 次</div>
            </div>
        </div>

        <div style="margin-top: 1rem;">
            <button
                onclick="highlightAllOccurrences('${canonical}')"
                style="width: 100%; padding: 0.625rem; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8125rem; font-weight: 500; transition: background 0.2s;"
                onmouseover="this.style.background='#2563eb'"
                onmouseout="this.style.background='#3b82f6'">
                高亮全部 ${occurrences} 处
            </button>
        </div>

        ${generateRelatedEntities(entity)}
    `;

    // 智能定位：在实体附近显示卡片
    positionInfoPanel(entity, infoPanel);

    // 显示遮罩层和面板
    const overlay = document.getElementById('info-panel-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
    infoPanel.classList.add('active');
}

function positionInfoPanel(entity, panel) {
    const entityRect = entity.getBoundingClientRect();
    const panelWidth = 320; // 预估宽度
    const panelHeight = 300; // 预估高度
    const spacing = 12; // 与实体的间距
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let left, top;

    // 默认：显示在实体右上方
    left = entityRect.right + spacing;
    top = entityRect.top;

    // 如果右侧空间不足，显示在左侧
    if (left + panelWidth > viewportWidth - 20) {
        left = entityRect.left - panelWidth - spacing;
    }

    // 如果左侧也不足，居中显示在实体下方
    if (left < 20) {
        left = entityRect.left + (entityRect.width / 2) - (panelWidth / 2);
        top = entityRect.bottom + spacing;
    }

    // 确保不超出视口左右边界
    left = Math.max(20, Math.min(left, viewportWidth - panelWidth - 20));

    // 确保不超出视口上下边界
    if (top + panelHeight > viewportHeight - 20) {
        top = Math.max(20, viewportHeight - panelHeight - 20);
    }
    if (top < 20) {
        top = 20;
    }

    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
}

function generateRelatedEntities(entity) {
    // 查找同段落的其他实体
    const paragraph = entity.closest('p, h1, h2, h3');
    if (!paragraph) return '';

    const relatedEntities = new Set();
    paragraph.querySelectorAll('.entity').forEach(e => {
        if (e !== entity && !e.classList.contains('hidden')) {
            relatedEntities.add(`${e.dataset.type}: ${e.textContent}`);
        }
    });

    if (relatedEntities.size === 0) return '';

    return `
        <div style="margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
            <div class="info-label" style="margin-bottom: 0.5rem;">相关实体 (同段落)</div>
            <div style="display: flex; flex-direction: column; gap: 0.375rem;">
                ${Array.from(relatedEntities).slice(0, 5).map(name =>
                    `<div style="color: #6b7280; font-size: 0.8125rem; line-height: 1.4;">• ${name}</div>`
                ).join('')}
                ${relatedEntities.size > 5 ? `<div style="color: #9ca3af; font-size: 0.75rem; margin-top: 0.25rem;">还有 ${relatedEntities.size - 5} 个...</div>` : ''}
            </div>
        </div>
    `;
}

function closeInfoPanel() {
    const infoPanel = document.getElementById('info-panel');
    const overlay = document.getElementById('info-panel-overlay');

    if (infoPanel) {
        infoPanel.classList.remove('active');
    }

    if (overlay) {
        overlay.classList.remove('active');
    }

    // 取消选中
    if (state.selectedEntity) {
        state.selectedEntity.classList.remove('active');
        state.selectedEntity = null;
    }
}

function highlightAllOccurrences(canonical) {
    const entities = findSameEntities(canonical);
    highlightEntities(entities);

    // 滚动到第一个出现位置
    if (entities.length > 0) {
        entities[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// ========== 数据收集 ==========

function collectEntityData() {
    const data = new Map();

    document.querySelectorAll('.entity').forEach(entity => {
        const canonical = entity.dataset.canonical;
        const type = entity.dataset.type;

        if (!data.has(canonical)) {
            data.set(canonical, {
                canonical,
                type,
                display: new Set(),
                occurrences: [],
            });
        }

        const entityData = data.get(canonical);
        entityData.display.add(entity.textContent);
        entityData.occurrences.push(entity);
    });

    state.entityData = data;
    console.log(`收集到 ${data.size} 个独立实体`);
}

// ========== 实用工具 ==========

/**
 * 获取实体统计信息
 */
function getEntityStats() {
    const stats = {
        total: 0,
        byType: {},
    };

    document.querySelectorAll('.entity').forEach(entity => {
        const className = Array.from(entity.classList).find(c => c.startsWith('entity-'));
        if (className) {
            const type = className.replace('entity-', '');
            stats.byType[type] = (stats.byType[type] || 0) + 1;
            stats.total++;
        }
    });

    return stats;
}

/**
 * 导出标注数据（JSON格式）
 */
function exportAnnotations() {
    const annotations = [];

    document.querySelectorAll('.entity').forEach(entity => {
        annotations.push({
            type: entity.dataset.type,
            display: entity.textContent,
            canonical: entity.dataset.canonical,
            id: entity.dataset.entityId,
        });
    });

    const json = JSON.stringify(annotations, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = 'annotations.json';
    a.click();

    console.log(`导出 ${annotations.length} 条标注`);
}

/**
 * 搜索实体
 */
function searchEntity(query) {
    const results = [];

    state.entityData.forEach((data, canonical) => {
        if (canonical.includes(query) ||
            Array.from(data.display).some(d => d.includes(query))) {
            results.push({
                canonical,
                type: data.type,
                count: data.occurrences.length,
            });
        }
    });

    return results;
}

// ========== 键盘快捷键 ==========

document.addEventListener('keydown', (e) => {
    // ESC 关闭信息面板
    if (e.key === 'Escape') {
        closeInfoPanel();
    }

    // Ctrl/Cmd + F 激活搜索（未实现）
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        // TODO: 实现搜索功能
    }
});

// ========== 调试工具 ==========

// 在控制台暴露一些有用的函数
window.semanticReading = {
    getStats: getEntityStats,
    search: searchEntity,
    export: exportAnnotations,
    state,
};

console.log('提示: 在控制台使用 semanticReading 对象访问调试工具');
console.log('例如: semanticReading.getStats() 查看统计信息');
