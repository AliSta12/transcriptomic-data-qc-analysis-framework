from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
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
        self._configure_report_styles(styles)
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
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
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

        self._add_readiness_assessment_section(
            story,
            styles,
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
                "Visualizes the top 20 genes by variance for readability; full top 50 and top 100 rankings are exported as CSV files.",
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

        story.append(PageBreak())

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

        self._add_generated_output_files_section(
            story=story,
            styles=styles,
        )

        self._add_section(
            story,
            styles,
            "9. Biological Interpretation",
            "PCA and hierarchical clustering summarize sample-level structure in the cleaned "
            "expression matrix. The heatmap and variable gene ranking highlight genes with high "
            "expression variability across samples. These results are intended for exploratory "
            "interpretation and quality-oriented review, not for formal differential expression "
            "testing or pathway-level biological conclusions.",
        )

        self._add_section(
            story,
            styles,
            "10. Conclusions",
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

    def _configure_report_styles(self, styles) -> None:
        """
        Defines table-specific PDF styles.

        The report uses three table sizes:
        - summary/title tables: handled locally,
        - standard report tables: 8 pt,
        - dense technical tables: 7.2 pt.
        """

        styles["Heading1"].fontSize = 16
        styles["Heading1"].leading = 19
        styles["Heading1"].spaceAfter = 6

        if "StandardTableCell" not in styles.byName:
            standard_cell = styles["Normal"].clone("StandardTableCell")
            standard_cell.fontName = "Helvetica"
            standard_cell.fontSize = 8
            standard_cell.leading = 9.4
            standard_cell.spaceBefore = 0
            standard_cell.spaceAfter = 0
            styles.add(standard_cell)

        if "CompactTableCell" not in styles.byName:
            compact_cell = styles["Normal"].clone("CompactTableCell")
            compact_cell.fontName = "Helvetica"
            compact_cell.fontSize = 7.2
            compact_cell.leading = 8.4
            compact_cell.spaceBefore = 0
            compact_cell.spaceAfter = 0
            styles.add(compact_cell)

        if "StandardTableHeader" not in styles.byName:
            standard_header = styles["Normal"].clone("StandardTableHeader")
            standard_header.fontName = "Helvetica-Bold"
            standard_header.fontSize = 8
            standard_header.leading = 9.4
            standard_header.spaceBefore = 0
            standard_header.spaceAfter = 0
            styles.add(standard_header)

        if "CompactTableHeader" not in styles.byName:
            compact_header = styles["Normal"].clone("CompactTableHeader")
            compact_header.fontName = "Helvetica-Bold"
            compact_header.fontSize = 7.2
            compact_header.leading = 8.4
            compact_header.spaceBefore = 0
            compact_header.spaceAfter = 0
            styles.add(compact_header)


    def _add_readiness_assessment_section(
        self,
        story,
        styles,
        dataframe: pd.DataFrame,
    ) -> None:

        def _value_from_row(row, candidate_columns: list[str]) -> str:
            for column in candidate_columns:
                if column in dataframe.columns:
                    return self._format_table_value(row[column])
            return "N/A"

        table_data = [
            [
                Paragraph("Field", styles["StandardTableHeader"]),
                Paragraph("Value", styles["StandardTableHeader"]),
            ]
        ]

        if dataframe.empty:
            table_data.append(
                [
                    Paragraph("Overall status", styles["StandardTableHeader"]),
                    Paragraph("N/A", styles["StandardTableCell"]),
                ]
            )
            table_data.append(
                [
                    Paragraph("Details", styles["StandardTableHeader"]),
                    Paragraph(
                        "Data readiness report is empty.",
                        styles["StandardTableCell"],
                    ),
                ]
            )
        else:
            row = dataframe.iloc[0]
            readiness_rows = [
                ("Overall status", ["overall_status", "readiness_status"]),
                ("Total QC checks", ["total_checks"]),
                ("PASS checks", ["pass_count"]),
                ("WARNING checks", ["warning_count"]),
                ("FAIL checks", ["fail_count"]),
                ("REQUIRES REVIEW checks", ["review_count"]),
                ("Recommendation", ["recommendation"]),
                ("Details", ["details"]),
            ]

            for label, candidate_columns in readiness_rows:
                value = _value_from_row(row, candidate_columns)
                if value != "N/A":
                    table_data.append(
                        [
                            Paragraph(
                                escape(label),
                                styles["StandardTableHeader"],
                            ),
                            Paragraph(
                                escape(value),
                                styles["StandardTableCell"],
                            ),
                        ]
                    )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[170, 540],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("BACKGROUND", (0, 1), (0, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    Paragraph("5. Data Readiness Assessment", styles["Heading1"]),
                    Spacer(1, 8),
                    table,
                    Spacer(1, 16),
                ]
            )
        )
    def _add_generated_output_files_section(self, story, styles) -> None:
        output_groups = [
            (
                "Data Cleaner & QC",
                (
                    "clean_expression_matrix.csv, clean_metadata.csv, audit_log.csv, "
                    "harmonization_report.csv, data_quality_report.csv, "
                    "data_readiness_report.csv"
                ),
                (
                    "Cleaned data, transparent audit trail, harmonization summary "
                    "and final readiness assessment."
                ),
            ),
            (
                "Analysis Engine",
                (
                    "top_50_variable_genes.csv, top_100_variable_genes.csv, "
                    "analysis_summary.csv, analysis_summary.md"
                ),
                "Exploratory analysis tables and human-readable summary files.",
            ),
            (
                "Visualizations",
                (
                    "class_distribution.png, pca_plot.png, "
                    "top_variable_genes_barplot.png, heatmap_top50_variable_genes.png, "
                    "sample_clustering_dendrogram.png"
                ),
                "Figures used for exploratory review and final report interpretation.",
            ),
            (
                "Reporting",
                "final_report.pdf",
                "Final PDF report summarizing QC, harmonization and exploratory analysis.",
            ),
        ]

        table_data = [
            [
                Paragraph("Module", styles["StandardTableHeader"]),
                Paragraph("Generated files", styles["StandardTableHeader"]),
                Paragraph("Purpose", styles["StandardTableHeader"]),
            ]
        ]

        for module, generated_files, purpose in output_groups:
            table_data.append(
                [
                    Paragraph(escape(module), styles["StandardTableCell"]),
                    Paragraph(escape(generated_files), styles["CompactTableCell"]),
                    Paragraph(escape(purpose), styles["StandardTableCell"]),
                ]
            )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=[130, 360, 240],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    Paragraph("8. Generated Output Files", styles["Heading1"]),
                    Spacer(1, 8),
                    Paragraph(
                        (
                            "The generated outputs support reproducibility, "
                            "transparent reporting and exploratory review."
                        ),
                        styles["Normal"],
                    ),
                    Spacer(1, 8),
                    table,
                    Spacer(1, 16),
                ]
            )
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

        compact_table_titles = {
            "3. Data Quality Assessment",
        }

        is_compact_table = title in compact_table_titles

        cell_style = (
            styles["CompactTableCell"]
            if is_compact_table
            else styles["StandardTableCell"]
        )
        header_style = (
            styles["CompactTableHeader"]
            if is_compact_table
            else styles["StandardTableHeader"]
        )

        table_data = self._dataframe_to_table_data(
            dataframe=dataframe,
            max_rows=max_rows,
            styles=styles,
            cell_style=cell_style,
            header_style=header_style,
        )

        table = Table(
            table_data,
            repeatRows=1,
            colWidths=self._get_dataframe_column_widths(
                dataframe=dataframe,
                title=title,
            ),
        )

        top_bottom_padding = 3 if is_compact_table else 4

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), top_bottom_padding),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), top_bottom_padding),
                ]
            )
        )

        story.append(
            KeepTogether(
                [
                    Paragraph(title, styles["Heading1"]),
                    Spacer(1, 8),
                    table,
                    Spacer(1, 16),
                ]
            )
        )
    def _format_table_value(self, value) -> str:
        if pd.isna(value):
            return ""

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)

    def _format_column_label(self, column_name: str) -> str:
        """
        Converts machine-oriented dataframe column names into report-friendly labels.

        Examples:
        - metric -> Metric
        - analysis_step -> Analysis step
        - original_element -> Original element
        """

        return str(column_name).replace("_", " ").strip().capitalize()


    def _dataframe_to_table_data(
        self,
        dataframe: pd.DataFrame,
        max_rows: int,
        styles,
        cell_style=None,
        header_style=None,
    ) -> list:

        cell_style = cell_style or styles["StandardTableCell"]
        header_style = header_style or styles["StandardTableHeader"]

        if dataframe.empty:
            return [
                [
                    Paragraph(
                        "No data available.",
                        cell_style,
                    )
                ]
            ]

        display_dataframe = dataframe.head(max_rows).copy()

        table_data = [
            [
                Paragraph(
                    escape(self._format_column_label(column)),
                    header_style,
                )
                for column in display_dataframe.columns
            ]
        ]

        for _, row in display_dataframe.iterrows():
            table_data.append(
                [
                    Paragraph(
                        escape(self._format_table_value(value)),
                        cell_style,
                    )
                    for value in row
                ]
            )

        if len(dataframe) > max_rows:
            table_data.append(
                [
                    Paragraph("...", cell_style)
                    for _ in display_dataframe.columns
                ]
            )

        return table_data
    def _get_dataframe_column_widths(
        self,
        dataframe: pd.DataFrame,
        title: str,
    ) -> list[float]:

        columns = list(dataframe.columns)
        column_count = len(columns)

        if column_count == 0:
            return []

        if title == "3. Data Quality Assessment" and column_count == 5:
            return [82, 62, 38, 112, 206]

        if title == "5. Data Readiness Assessment" and column_count == 5:
            return [95, 55, 55, 55, 240]

        if title == "4. Cleaning & Harmonization Summary" and column_count == 5:
            return [105, 105, 80, 75, 135]

        total_width = 500
        return [total_width / column_count] * column_count
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
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
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
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
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

