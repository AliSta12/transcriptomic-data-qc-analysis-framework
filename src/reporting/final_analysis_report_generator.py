from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors


@dataclass
class FinalAnalysisReportResult:
    pdf_path: str


class FinalAnalysisReportGenerator:
    """
    Generates final PDF report for the Transcriptomic Data QC & Analysis Framework.
    """

    def _add_page_number(self, canvas, doc) -> None:
        page_number = canvas.getPageNumber()

        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            landscape(A4)[0] - 40,
            20,
            f"Page {page_number}",
        )
        canvas.restoreState() 

    def _get_metric_value(
        self,
        dataframe: pd.DataFrame,
        metric_name: str,
        default: str = "N/A",
    ) -> str:
        matching_rows = dataframe[
            dataframe["metric"] == metric_name
        ]

        if matching_rows.empty:
            return default

        return self._format_table_value(
            matching_rows.iloc[0]["value"]
        )
    
    def generate(
        self,
        cleaner_result,
        analysis_result,
        dataset_name: str,
        output_directory: str,
    ) -> FinalAnalysisReportResult:

        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = output_dir / "final_report.pdf"

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        story = []
        
        dataset_overview = analysis_result.dataset_overview.summary_dataframe

        sample_count = self._get_metric_value(
            dataset_overview,
            "sample_count",
        )
        gene_count = self._get_metric_value(
            dataset_overview,
            "gene_count",
        )
        group_count = self._get_metric_value(
            dataset_overview,
            "group_count",
        )
        analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        story.append(
            Paragraph(
                "Transcriptomic Data QC & Analysis Framework",
                styles["Title"],
            )
        )
        story.append(Spacer(1, 18))

        story.append(
            Paragraph(
                "Final Analysis Report",
                styles["Heading1"],
            )
        )
        story.append(Spacer(1, 8))

        title_table_data = [
            ["Dataset", dataset_name],
            ["Samples", sample_count],
            ["Genes", gene_count],
            ["Groups", group_count],
            ["Data readiness", cleaner_result.final_status],
            ["Analysis date", analysis_date],
        ]

        title_table = Table(
            title_table_data,
            colWidths=[120, 260],
        )
        title_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(title_table)
        story.append(Spacer(1, 18))

        self._add_section(
            story,
            styles,
            "1. Project Overview",
            "This report summarizes rule-based data cleaning, harmonization, quality control "
            "and exploratory transcriptomic analysis performed on a public gene expression dataset.",
        )

        self._add_dataframe_section(
            story,
            styles,
            "2. Dataset Description",
            analysis_result.dataset_overview.summary_dataframe,
        )

        self._add_dataframe_section(
            story,
            styles,
            "3. Data Quality Assessment",
            cleaner_result.data_quality_report,
        )

        self._add_dataframe_section(
            story,
            styles,
            "4. Cleaning & Harmonization Summary",
            cleaner_result.harmonization_report,
        )

        self._add_dataframe_section(
            story,
            styles,
            "5. Data Readiness Assessment",
            cleaner_result.data_readiness_report,
        )

        self._add_dataframe_section(
            story,
            styles,
            "6. Exploratory Transcriptomic Analysis",
            analysis_result.analysis_summary.summary_dataframe,
        )

        story.append(Spacer(1, 10))

        image_items = [
            (
                cleaner_result.missing_data_plot_path,
                "MISSING DATA SUMMARY",
                "Shows whether missing values were detected in the uploaded expression matrix.",
            ),
            (
                cleaner_result.qc_status_summary_plot_path,
                "QC STATUS SUMMARY",
                "Summarizes PASS, WARNING, FAIL and REQUIRES REVIEW statuses across quality checks.",
            ),
            (
                analysis_result.class_distribution.plot_path,
                "CLASS DISTRIBUTION",
                "Shows the number and percentage of samples in each biological group.",
            ),
            (
                analysis_result.pca_analysis.plot_path,
                "PCA ANALYSIS",
                "Visualizes sample-level structure using the first two principal components.",
            ),
            (
                analysis_result.variable_gene_analysis.barplot_path,
                "TOP VARIABLE GENES",
                "Ranks the top 50 genes by variance for exploratory visualization.",
            ),
            (
                analysis_result.heatmap.plot_path,
                "HEATMAP OF TOP VARIABLE GENES",
                "Shows expression patterns across samples for the top 50 most variable genes.",
            ),
            (
                analysis_result.sample_clustering.plot_path,
                "SAMPLE CLUSTERING DENDROGRAM",
                "Groups samples based on similarity of expression profiles.",
            ),
        ]

        story.append(
            KeepTogether(
                [
                    Paragraph("7. QC Evidence and Exploratory Visualizations", styles["Heading1"]),
                    Spacer(1, 12),
                ]
            )
        )

        self._add_qc_evidence_summary_box(
            story=story,
            styles=styles,
            cleaner_result=cleaner_result,
        )

        image_items = [
            item
            for item in image_items
            if item[1] != "QC STATUS SUMMARY"
        ]

        if self._missing_data_count_is_zero(cleaner_result.data_quality_report):
            image_items = [
                item
                for item in image_items
                if item[1] != "MISSING DATA SUMMARY"
            ]

        for image_path, image_title, image_caption in image_items:
            self._add_image(
                story=story,
                styles=styles,
                image_path=image_path,
                title=image_title,
                caption=image_caption,
            )

        self._add_section(
            story,
            styles,
            "8. Biological Interpretation",
            "PCA and hierarchical clustering summarize sample-level structure in the cleaned "
            "expression matrix. The heatmap and variable gene ranking highlight genes with high "
            "expression variability across samples. These results are intended for exploratory "
            "interpretation and quality-oriented review, not for formal differential expression "
            "testing or pathway-level biological conclusions.",
        )

        self._add_section(
            story,
            styles,
            "9. Conclusions",
            f"The dataset readiness status is: {cleaner_result.final_status}. "
            "QC results, harmonization outputs and exploratory analysis summaries should be "
            "reviewed together before downstream biological interpretation. "
            "PCA, variable gene ranking, heatmap and hierarchical clustering provide an overview "
            "of sample structure and expression variability. These outputs are descriptive and "
            "do not represent formal differential expression analysis.",
        )

        doc.build(
            story,
            onFirstPage=self._add_page_number,
            onLaterPages=self._add_page_number,
        )

        return FinalAnalysisReportResult(
            pdf_path=str(pdf_path),
        )

    def _add_section(self, story, styles, title: str, text: str) -> None:
        section_block = KeepTogether(
            [
                Paragraph(title, styles["Heading1"]),
                Spacer(1, 8),
                Paragraph(text, styles["Normal"]),
                Spacer(1, 16),
            ]
        )
        story.append(section_block)

    def _add_dataframe_section(
        self,
        story,
        styles,
        title: str,
        dataframe: pd.DataFrame,
        max_rows: int = 12,
    ) -> None:

        table_data = self._dataframe_to_table_data(
            dataframe=dataframe,
            max_rows=max_rows,
        )

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        section_block = KeepTogether(
            [
                Paragraph(title, styles["Heading1"]),
                Spacer(1, 8),
                table,
                Spacer(1, 16),
            ]
        )

        story.append(section_block)

    def _format_table_value(self, value) -> str:
        if pd.isna(value):
            return ""

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)

    def _dataframe_to_table_data(
        self,
        dataframe: pd.DataFrame,
        max_rows: int,
    ) -> list[list[str]]:

        display_df = dataframe.head(max_rows).copy()
        display_df = display_df.fillna("")

        table_data = [list(display_df.columns)]

        for row in display_df.values.tolist():
            formatted_row = [
                self._format_table_value(value)
                for value in row
            ]
            table_data.append(formatted_row)
        return table_data

    def _get_qc_metric(
        self,
        data_quality_report: pd.DataFrame,
        check_name: str,
        default: str = "N/A",
    ) -> str:
        matching_rows = data_quality_report[
            data_quality_report["check"] == check_name
        ]

        if matching_rows.empty:
            return default

        return self._format_table_value(
            matching_rows.iloc[0]["metric"]
        )

    def _get_qc_status(
        self,
        data_quality_report: pd.DataFrame,
        check_name: str,
        default: str = "N/A",
    ) -> str:
        matching_rows = data_quality_report[
            data_quality_report["check"] == check_name
        ]

        if matching_rows.empty:
            return default

        return self._format_table_value(
            matching_rows.iloc[0]["status"]
        )

    def _get_qc_status_counts(
        self,
        data_quality_report: pd.DataFrame,
    ) -> dict[str, int]:
        statuses = (
            data_quality_report["status"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

        return {
            "PASS": int((statuses == "PASS").sum()),
            "WARNING": int((statuses == "WARNING").sum()),
            "FAIL": int((statuses == "FAIL").sum()),
            "REQUIRES REVIEW": int((statuses == "REQUIRES REVIEW").sum()),
        }

    def _add_qc_evidence_summary_box(
        self,
        story,
        styles,
        cleaner_result,
    ) -> None:
        data_quality_report = cleaner_result.data_quality_report
        status_counts = self._get_qc_status_counts(data_quality_report)

        missing_status = self._get_qc_status(
            data_quality_report,
            "Missing Data",
        )
        missing_count = self._get_qc_metric(
            data_quality_report,
            "Missing Data",
        )
        duplicate_gene_count = self._get_qc_metric(
            data_quality_report,
            "Duplicate Genes",
        )
        constant_gene_count = self._get_qc_metric(
            data_quality_report,
            "Constant Genes",
        )
        metadata_issue_count = self._get_qc_metric(
            data_quality_report,
            "Metadata Consistency",
        )

        if self._missing_data_count_is_zero(data_quality_report):
            missing_action = (
                "No imputation or removal was required because the missing "
                "value count was 0."
            )
        else:
            missing_action = (
                "Missing data rules were applied according to predefined "
                "thresholds and recorded in the QC outputs."
            )

        table_data = [
            ["QC EVIDENCE SUMMARY", ""],
            ["Overall readiness", cleaner_result.final_status],
            [
                "QC status counts",
                (
                    f"PASS: {status_counts['PASS']}; "
                    f"WARNING: {status_counts['WARNING']}; "
                    f"FAIL: {status_counts['FAIL']}; "
                    f"REQUIRES REVIEW: {status_counts['REQUIRES REVIEW']}"
                ),
            ],
            [
                "Missing data",
                f"Status: {missing_status}; detected missing values: {missing_count}",
            ],
            ["Rule-based action", missing_action],
            [
                "Cleaning / QC evidence",
                (
                    f"Duplicate genes: {duplicate_gene_count}; "
                    f"constant genes: {constant_gene_count}; "
                    f"metadata issues: {metadata_issue_count}"
                ),
            ],
        ]

        table = Table(
            table_data,
            colWidths=[150, 520],
        )
        table.setStyle(
            TableStyle(
                [
                    ("SPAN", (0, 0), (-1, 0)),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    table,
                    Spacer(1, 8),
                    Paragraph(
                        "This section summarizes rule-based QC evidence before "
                        "the exploratory transcriptomic visualizations. Diagnostic "
                        "plots are included when they add interpretive value.",
                        styles["Normal"],
                    ),
                    Spacer(1, 14),
                ]
            )
        )

    def _missing_data_count_is_zero(
        self,
        data_quality_report: pd.DataFrame,
    ) -> bool:
        missing_data_rows = data_quality_report[
            data_quality_report["check"] == "Missing Data"
        ]

        if missing_data_rows.empty:
            return False

        missing_value_count = missing_data_rows.iloc[0]["metric"]

        try:
            return float(missing_value_count) == 0
        except (TypeError, ValueError):
            return False

    def _add_missing_data_summary_box(
        self,
        story,
        styles,
    ) -> None:
        table_data = [
            ["MISSING DATA SUMMARY"],
            ["No missing values were detected in the expression matrix."],
            [
                "Rule-based action: no imputation or removal was required "
                "because the missing value count was 0."
            ],
        ]

        table = Table(
            table_data,
            colWidths=[520],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    table,
                    Spacer(1, 14),
                ]
            )
        )

    def _add_image(
        self,
        story,
        styles,
        image_path: str,
        title: str,
        caption: str,
    ) -> None:
        path = Path(image_path)

        if not path.exists():
            story.append(
                Paragraph(
                    f"Missing visualization: {title}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 12))
            return

        image = Image(str(path))
        image._restrictSize(700, 330)

        image_block = KeepTogether(
            [
                Paragraph(title, styles["Heading2"]),
                Spacer(1, 4),
                Paragraph(caption, styles["Normal"]),
                Spacer(1, 6),
                image,
                Spacer(1, 14),
            ]
        )

        story.append(image_block)

