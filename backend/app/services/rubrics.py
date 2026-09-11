from app.models.collaboration import PositionCategory


POSITION_CATEGORY_LABELS = {
    PositionCategory.design: "设计",
    PositionCategory.development: "代码开发",
    PositionCategory.data: "数据分析",
    PositionCategory.content: "内容创作",
    PositionCategory.operations: "运营执行",
    PositionCategory.general: "通用协作",
}

PROJECT_REVIEW_RUBRICS = {
    PositionCategory.design: ("design-performance-v1", ["需求与方案", "设计执行", "协作沟通", "交付规范"]),
    PositionCategory.development: ("development-performance-v1", ["功能正确性", "代码质量", "测试与可靠性", "协作交付"]),
    PositionCategory.data: ("data-performance-v1", ["数据质量", "分析方法", "结果解释", "可复现交付"]),
    PositionCategory.content: ("content-performance-v1", ["内容准确性", "结构与表达", "受众适配", "协作交付"]),
    PositionCategory.operations: ("operations-performance-v1", ["方案规划", "组织协调", "现场执行", "复盘改进"]),
    PositionCategory.general: ("general-performance-v1", ["专业表现", "沟通协作", "成果交付", "时间管理"]),
}

EVIDENCE_RUBRICS = {
    "visual_poster": ("visual-poster-v1", ["需求与场景理解", "信息层级与可读性", "视觉一致性与执行质量", "过程与迭代证据", "个人贡献与答辩解释"]),
    "data_visualization": ("data-v1", ["问题定义与数据来源", "清洗与质量控制", "方法正确性", "结果解释与可视化", "复现、限制与个人贡献"]),
    "code_project": ("code-v1", ["需求实现与功能正确性", "结构与可读性", "异常、安全与边界处理", "测试与可复现性", "版本过程与个人贡献"]),
    "document": ("content-v1", ["受众与目标理解", "结构与表达清晰度", "事实、引用与原创性", "渠道适配与完成质量", "修订过程与个人贡献"]),
    "operations_record": ("operations-v1", ["目标与执行计划", "进度与资源管理", "协作与相关方沟通", "风险响应", "指标结果、复盘与个人贡献"]),
}

EVIDENCE_RUBRIC_WEIGHTS = {
    "visual_poster": [15, 25, 20, 20, 20],
    "data_visualization": [20, 20, 20, 20, 20],
    "code_project": [25, 20, 15, 20, 20],
    "document": [20, 20, 20, 20, 20],
    "operations_record": [20, 20, 20, 20, 20],
}


def project_rubric(category: PositionCategory):
    return PROJECT_REVIEW_RUBRICS.get(category, PROJECT_REVIEW_RUBRICS[PositionCategory.general])


def evidence_rubric(evidence_type: str):
    return EVIDENCE_RUBRICS.get(evidence_type)
