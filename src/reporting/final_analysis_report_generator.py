from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
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
            A4[0] - 40,
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
            pagesize=A4,
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
            "Data Readiness Assessment",
            cleaner_result.data_readiness_report,
        )

        self._add_dataframe_section(
            story,
            styles,
            "5. Exploratory Transcriptomic Analysis",
            analysis_result.analysis_summary.summary_dataframe,
        )

        story.append(PageBreak())
        story.append(Paragraph("6. Visualizations", styles["Heading1"]))
        story.append(Spacer(1, 12))

        image_paths = [
            cleaner_result.missing_data_plot_path,
            cleaner_result.qc_status_summary_plot_path,
            analysis_result.class_distribution.plot_path,
            analysis_result.pca_analysis.plot_path,
            analysis_result.variable_gene_analysis.barplot_path,
            analysis_result.heatmap.plot_path,
            analysis_result.sample_clustering.plot_path,
        ]

        for image_path in image_paths:
            self._add_image(story, styles, image_path)

        self._add_section(
            story,
            styles,
            "7. Conclusions",
            f"The dataset readiness status is: {cleaner_result.final_status}. "
            "The analysis should be interpreted as exploratory. PCA, variable gene ranking, "
            "heatmap and hierarchical clustering provide an overview of sample structure and "
            "expression variability, but they do not represent differential expression analysis.",
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
        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph(text, styles["Normal"]))
        story.append(Spacer(1, 16))

    def _add_dataframe_section(
        self,
        story,
        styles,
        title: str,
        dataframe: pd.DataFrame,
        max_rows: int = 12,
    ) -> None:

        story.append(Paragraph(title, styles["Heading1"]))
        story.append(Spacer(1, 8))

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

        story.append(table)
        story.append(Spacer(1, 16))

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

    def _add_image(self, story, styles, image_path: str) -> None:
        path = Path(image_path)

        if not path.exists():
            story.append(
                Paragraph(
                    f"Missing visualization: {image_path}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 12))
            return

        image = Image(str(path))
        image._restrictSize(460, 300)

        image_block = KeepTogether(
            [
                Paragraph(path.name, styles["Heading2"]),
                Spacer(1, 6),
                image,
                Spacer(1, 18),
            ]
        )

        story.append(image_block)

