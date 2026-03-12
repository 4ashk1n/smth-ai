"""Application pipelines."""

from ai_module.application.pipelines.layout_quality_pipeline import LayoutQualityPipeline
from ai_module.application.pipelines.text_quality_pipeline import TextQualityPipeline

__all__ = ["TextQualityPipeline", "LayoutQualityPipeline"]
