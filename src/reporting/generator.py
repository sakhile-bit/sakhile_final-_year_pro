"""
Report Generation Module
Handles HTML, JSON, CSV, and PDF report generation for assessments.

Supports the full 15-control Zambia Digital Hygiene framework with
framework references (NIST, CIS, ISO 27001), certification tiers,
and Zambia-specific compliance guidance.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class ReportGenerator:
    """Generate assessment reports in multiple formats"""

    def __init__(self, output_dir: str = "reports"):
        """Initialize report generator.

        Args:
            output_dir: Directory for report output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self, results: Any, business_info: Any, report_name: str
    ) -> str:
        """Generate HTML report.

        Args:
            results: Assessment results object
            business_info: Business information object
            report_name: Base name for the report file

        Returns:
            Path to generated HTML file
        """
        html_content = self._build_html(results, business_info)
        report_path = self.output_dir / f"{report_name}.html"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(report_path)

    def generate_json_report(self, results: Any, business_info: Any) -> Dict[str, Any]:
        """Generate JSON report data.

        Args:
            results: Assessment results object
            business_info: Business information object

        Returns:
            Dictionary ready for JSON serialization
        """
        controls_data = {}
        for control_id, control in results.controls.items():
            entry = {
                'name': getattr(control, 'name', ''),
                'score': getattr(control, 'score', 0),
                'weight': getattr(control, 'weight', 0),
                'status': getattr(control, 'status', ''),
                'details': getattr(control, 'details', ''),
            }
            # Include new fields if present
            if hasattr(control, 'control_id'):
                entry['control_id'] = control.control_id
            if hasattr(control, 'category'):
                entry['category'] = control.category
            if hasattr(control, 'verification'):
                entry['verification'] = control.verification
            controls_data[control_id] = entry

        return {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'program': 'Zambia Digital Hygiene Certification Program',
                'version': '2.0.0',
                'frameworks': ['NIST CSF v1.1', 'CIS Controls v8', 'ISO 27001:2022'],
                'business': {
                    'name': getattr(business_info, 'name', 'Unknown'),
                    'id': getattr(business_info, 'id', 'Unknown'),
                    'contact_person': getattr(business_info, 'contact_person', None),
                    'contact_email': getattr(business_info, 'contact_email', None),
                    'contact_phone': getattr(business_info, 'contact_phone', None),
                    'industry': getattr(business_info, 'industry', None),
                    'address': getattr(business_info, 'address', None),
                    'province': getattr(business_info, 'province', None),
                    'num_employees': getattr(business_info, 'num_employees', None),
                }
            },
            'summary': {
                'score': results.score,
                'total_possible': results.total_possible,
                'percentage': (
                    round(results.score / results.total_possible * 100, 1)
                    if results.total_possible > 0 else 0
                ),
                'certification_level': results.certification_level,
                'critical_failures': getattr(results, 'critical_failures', 0),
                'assessment_tier': getattr(results, 'assessment_tier', 'automated'),
            },
            'controls': controls_data,
            'recommendations': results.recommendations,
        }

    def generate_csv_report(self, results: Any, business_info: Any) -> List[List[str]]:
        """Generate CSV report data.

        Args:
            results: Assessment results object
            business_info: Business information object

        Returns:
            List of rows for CSV output
        """
        rows = [
            ['Zambia Digital Hygiene Certification – Assessment Report'],
            ['Frameworks: NIST CSF, CIS Controls v8, ISO 27001:2022'],
            [],
            ['Business Information'],
            ['Name', getattr(business_info, 'name', 'Unknown')],
            ['ID', getattr(business_info, 'id', 'Unknown')],
            ['Industry', getattr(business_info, 'industry', 'Unknown')],
            ['Contact Person', getattr(business_info, 'contact_person', 'Unknown')],
            ['Contact Email', getattr(business_info, 'contact_email', 'Unknown')],
            ['Contact Phone', getattr(business_info, 'contact_phone', 'Unknown')],
            ['Province', getattr(business_info, 'province', 'Unknown')],
            [],
            ['Assessment Summary'],
            ['Score', str(results.score)],
            ['Total Possible', str(results.total_possible)],
            ['Percentage',
             f"{round(results.score / results.total_possible * 100, 1)}%"
             if results.total_possible > 0 else "0%"],
            ['Certification Level', results.certification_level],
            ['Critical Failures', str(getattr(results, 'critical_failures', 0))],
            [],
            ['Control Results'],
            ['Control ID', 'Control Name', 'Score', 'Weight', 'Status', 'Category', 'Verification', 'Details']
        ]

        for control_id, control in results.controls.items():
            rows.append([
                getattr(control, 'control_id', control_id),
                getattr(control, 'name', ''),
                str(getattr(control, 'score', 0)),
                str(getattr(control, 'weight', 0)),
                getattr(control, 'status', ''),
                getattr(control, 'category', ''),
                getattr(control, 'verification', ''),
                getattr(control, 'details', ''),
            ])

        rows.extend([[], ['Recommendations']])
        for rec in results.recommendations:
            rows.append([rec])

        return rows

    def generate_pdf_report(
        self, results: Any, business_info: Any, report_name: str
    ) -> str:
        """Generate a professional PDF report using ReportLab.

        Falls back to HTML export if ReportLab is not installed.

        Returns:
            Path to the generated PDF (or HTML fallback).
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                HRFlowable,
            )
            from reportlab.lib.enums import TA_CENTER

            pdf_path = str(self.output_dir / f"{report_name}.pdf")
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                topMargin=1.5 * cm,
                bottomMargin=1.5 * cm,
                leftMargin=2 * cm,
                rightMargin=2 * cm,
                title=f"Digital Hygiene Report – {getattr(business_info, 'name', 'Unknown')}",
            )

            styles = getSampleStyleSheet()
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle', parent=styles['Title'],
                fontSize=18, textColor=colors.HexColor('#1a5276'),
                spaceAfter=6, alignment=TA_CENTER,
            )
            heading2 = ParagraphStyle(
                'H2', parent=styles['Heading2'],
                fontSize=12, textColor=colors.HexColor('#1a5276'),
                spaceBefore=12, spaceAfter=4,
            )
            normal = ParagraphStyle(
                'N', parent=styles['Normal'], fontSize=9, leading=13,
            )
            small = ParagraphStyle(
                'Small', parent=styles['Normal'], fontSize=8,
                textColor=colors.HexColor('#555555'),
            )
            percentage = round(results.score / results.total_possible * 100, 1) if results.total_possible > 0 else 0
            critical_failures = getattr(results, 'critical_failures', 0)
            level = results.certification_level
            level_hex = {
                'GOLD': '#b8860b', 'SILVER': '#555555',
                'BRONZE': '#8B4513', 'NOT CERTIFIED': '#c0392b',
            }.get(level, '#555555')

            status_hex = {
                'PASS': '#27ae60', 'WARNING': '#e67e22',
                'FAIL': '#e74c3c', 'ERROR': '#e74c3c', 'NOT_ASSESSED': '#7f8c8d',
            }

            story = []

            # ── Header banner ──────────────────────────────────────────
            story.append(Paragraph("Zambia Digital Hygiene Certification Program", title_style))
            story.append(Paragraph("Infrastructure Security Assessment Report", styles['Heading3']))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a5276')))
            story.append(Spacer(1, 6))

            # ── Business info table ────────────────────────────────────
            biz_data = [
                ['Business Name', getattr(business_info, 'name', 'N/A'),
                 'Registration', getattr(business_info, 'id', 'N/A')],
                ['Industry', getattr(business_info, 'industry', 'N/A'),
                 'Province', getattr(business_info, 'province', 'N/A')],
                ['Contact Person', getattr(business_info, 'contact_person', 'N/A'),
                 'Email', getattr(business_info, 'contact_email', 'N/A')],
                ['Phone', getattr(business_info, 'contact_phone', 'N/A'),
                 'Address', getattr(business_info, 'address', 'N/A')],
            ]
            biz_table = Table(biz_data, colWidths=[3.5 * cm, 6 * cm, 3 * cm, 4.5 * cm])
            biz_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d6e4f0')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#d6e4f0')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aaaaaa')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(Paragraph("Business Information", heading2))
            story.append(biz_table)
            story.append(Spacer(1, 10))

            # ── Score summary ──────────────────────────────────────────
            summary_data = [
                [Paragraph('<b>Overall Score</b>', normal),
                 Paragraph(
                     f'<font size="16" color="{level_hex}">'
                     f'<b>{results.score}/{results.total_possible} ({percentage}%)</b></font>',
                     normal,
                 ),
                 Paragraph('<b>Certification Level</b>', normal),
                 Paragraph(f'<font size="14" color="{level_hex}"><b>{level}</b></font>', normal)],
                [Paragraph('<b>Controls Assessed</b>', normal),
                 Paragraph(str(len(results.controls)), normal),
                 Paragraph('<b>Critical Failures</b>', normal),
                 Paragraph(
                     f'<font color="#e74c3c"><b>{critical_failures}</b></font>'
                     if critical_failures else '0', normal,
                 )],
            ]
            summary_table = Table(summary_data, colWidths=[4 * cm, 5.5 * cm, 4 * cm, 3.5 * cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(Paragraph("Assessment Summary", heading2))
            story.append(summary_table)
            story.append(Spacer(1, 10))

            # ── Controls table ─────────────────────────────────────────
            story.append(Paragraph("Control Assessment Results (15 Controls)", heading2))
            ctrl_header = [
                Paragraph('<font color="white"><b>ID</b></font>', normal),
                Paragraph('<font color="white"><b>Control Name</b></font>', normal),
                Paragraph('<font color="white"><b>Score</b></font>', normal),
                Paragraph('<font color="white"><b>Status</b></font>', normal),
                Paragraph('<font color="white"><b>Category</b></font>', normal),
                Paragraph('<font color="white"><b>Details</b></font>', small),
            ]
            ctrl_rows = [ctrl_header]
            for cid, ctrl in results.controls.items():
                s = getattr(ctrl, 'status', 'NOT_ASSESSED')
                shex = status_hex.get(s, '#7f8c8d')
                ctrl_rows.append([
                    Paragraph(getattr(ctrl, 'control_id', cid), small),
                    Paragraph(getattr(ctrl, 'name', ''), small),
                    Paragraph(f"{getattr(ctrl, 'score', 0)}/{getattr(ctrl, 'weight', 0)}", small),
                    Paragraph(f'<font color="{shex}"><b>{s}</b></font>', small),
                    Paragraph(getattr(ctrl, 'category', ''), small),
                    Paragraph((getattr(ctrl, 'details', '') or '')[:80], small),
                ])

            ctrl_table = Table(ctrl_rows, colWidths=[1.2 * cm, 4.5 * cm, 1.5 * cm, 2 * cm, 2.2 * cm, 5.6 * cm])
            ctrl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#dee2e6')),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(ctrl_table)
            story.append(Spacer(1, 10))

            # ── Recommendations ────────────────────────────────────────
            story.append(Paragraph("Recommendations", heading2))
            for rec in results.recommendations:
                bullet_color = '#c0392b' if rec.startswith('[CRITICAL]') else '#2c3e50'
                story.append(Paragraph(
                    f'<font color="{bullet_color}">• {rec}</font>', normal
                ))
                story.append(Spacer(1, 2))

            # ── Certification thresholds ───────────────────────────────
            story.append(Spacer(1, 8))
            story.append(Paragraph("Certification Thresholds", heading2))
            thresh_data = [
                ['Level', 'Min Score', 'Max Critical Failures', 'Validity'],
                ['GOLD',   '≥ 80% (≥96/120)', '0',    '12 months'],
                ['SILVER', '≥ 60% (≥72/120)', '≤ 1',  '12 months'],
                ['BRONZE', '≥ 40% (≥48/120)', '≤ 2',  '6 months'],
                ['NOT CERTIFIED', '< 40%',    '> 2',  'N/A'],
            ]
            thresh_bg = [
                colors.HexColor('#1a5276'),
                colors.HexColor('#b8860b'),
                colors.HexColor('#777777'),
                colors.HexColor('#8B4513'),
                colors.HexColor('#c0392b'),
            ]
            thresh_table = Table(thresh_data, colWidths=[4 * cm, 5 * cm, 5 * cm, 3 * cm])
            thresh_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#aaaaaa')),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ]
            for i, bg in enumerate(thresh_bg[1:], start=1):
                thresh_style.append(('BACKGROUND', (0, i), (0, i), bg))
                thresh_style.append(('TEXTCOLOR', (0, i), (0, i), colors.white))
            thresh_table.setStyle(TableStyle(thresh_style))
            story.append(thresh_table)

            # ── Footer ─────────────────────────────────────────────────
            story.append(Spacer(1, 14))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1a5276')))
            story.append(Paragraph(
                f"Zambia Digital Hygiene Certification Program | "
                f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')} | "
                f"Frameworks: NIST CSF v1.1 · CIS Controls v8 · ISO 27001:2022 · Cyber Essentials",
                small,
            ))

            doc.build(story)
            return pdf_path

        except ImportError:
            return self.generate_html_report(results, business_info, report_name)
        except Exception:
            return self.generate_html_report(results, business_info, report_name)

    def _build_html(self, results: Any, business_info: Any) -> str:
        """Build HTML report content with full 15-control detail."""
        percentage = round(results.score / results.total_possible * 100, 1) if results.total_possible > 0 else 0
        critical_failures = getattr(results, 'critical_failures', 0)
        level_colour = {
            'GOLD': '#FFD700', 'SILVER': '#C0C0C0',
            'BRONZE': '#CD7F32', 'NOT CERTIFIED': '#DC3545'
        }.get(results.certification_level, '#6c757d')

        # Separate automated and manual controls
        auto_rows = []
        manual_rows = []
        for cid, control in results.controls.items():
            ver = getattr(control, 'verification', 'automated')
            ctrl_id = getattr(control, 'control_id', cid)
            row = f'''
            <tr>
                <td>{ctrl_id}</td>
                <td>{getattr(control, 'name', '')}</td>
                <td>{getattr(control, 'score', 0)}/{getattr(control, 'weight', 0)}</td>
                <td><span class="badge bg-{self._status_color(getattr(control, 'status', ''))}">
                {getattr(control, 'status', '')}</span></td>
                <td>{getattr(control, 'details', '')}</td>
            </tr>'''
            if ver == 'automated':
                auto_rows.append(row)
            else:
                manual_rows.append(row)

        auto_html = ''.join(auto_rows)
        manual_html = ''.join(manual_rows)
        _no_manual = (
            '<tr><td colspan="5" style="text-align:center;color:#999">'
            'Awaiting manual verification</td></tr>'
        )

        recommendations_html = ''.join(
            f'<li class="{"text-danger fw-bold" if rec.startswith("[CRITICAL]") else ""}">{rec}</li>'
            for rec in results.recommendations
        )

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Hygiene Assessment Report – {getattr(business_info, 'name', 'Unknown')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; color: #333; line-height: 1.6; }}
        h1 {{ color: #1a5276; border-bottom: 3px solid #1a5276; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 25px; border-left: 4px solid #1a5276; padding-left: 10px; }}
        h3 {{ color: #34495e; }}
        .header {{ background: linear-gradient(135deg, #1a5276, #2980b9);
            color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .header h1 {{ color: white; border: none; margin: 0; }}
        .header p {{ margin: 5px 0; opacity: 0.9; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px;
            margin: 20px 0; border: 1px solid #dee2e6; }}
        .score {{ font-size: 2.2em; font-weight: bold; color: #1a5276; }}
        .cert-badge {{ display: inline-block; padding: 8px 20px; border-radius: 5px;
            color: white; font-weight: bold; font-size: 1.2em; background: {level_colour}; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #dee2e6; padding: 10px; text-align: left; }}
        th {{ background-color: #1a5276; color: white; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        .badge {{ padding: 4px 10px; border-radius: 3px; color: white; font-weight: bold; font-size: 0.85em; }}
        .bg-success {{ background-color: #28a745; }}
        .bg-warning {{ background-color: #ffc107; color: #333; }}
        .bg-danger {{ background-color: #dc3545; }}
        .bg-secondary {{ background-color: #6c757d; }}
        .text-danger {{ color: #dc3545; }}
        .fw-bold {{ font-weight: bold; }}
        ul {{ line-height: 2.0; }}
        .frameworks {{ background: #eaf2f8; padding: 10px 15px; border-radius: 5px; margin: 10px 0; font-size: 0.9em; }}
        .footer {{ margin-top: 30px; border-top: 2px solid #1a5276;
            padding-top: 15px; font-size: 0.9em; color: #666; text-align: center; }}
        @media print {{ body {{ margin: 0; }} .no-print {{ display: none; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Zambia Digital Hygiene Certification Program</h1>
        <p>Assessment Report – {getattr(business_info, 'name', 'Unknown')}</p>
        <p>Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}</p>
    </div>

    <div class="frameworks">
        <strong>Aligned Frameworks:</strong>
        NIST CSF v1.1 | CIS Controls v8 (IG1) | ISO/IEC 27001:2022 | UK Cyber Essentials
    </div>

    <h2>Business Information</h2>
    <table>
        <tr><td><strong>Name</strong></td><td>{getattr(business_info, 'name', 'Unknown')}</td>
            <td><strong>Registration</strong></td><td>{getattr(business_info, 'id', 'Unknown')}</td></tr>
        <tr><td><strong>Industry</strong></td><td>{getattr(business_info, 'industry', 'N/A')}</td>
            <td><strong>Contact</strong></td><td>{getattr(business_info, 'contact_person', 'N/A')}</td></tr>
        <tr><td><strong>Email</strong></td><td>{getattr(business_info, 'contact_email', 'N/A')}</td>
            <td><strong>Phone</strong></td><td>{getattr(business_info, 'contact_phone', 'N/A')}</td></tr>
        <tr><td><strong>Address</strong></td><td colspan="3">{getattr(business_info, 'address', 'N/A')}</td></tr>
    </table>

    <h2>Assessment Summary</h2>
    <div class="summary">
        <div><strong>Overall Score:</strong>
        <span class="score">{results.score}/{results.total_possible}</span> ({percentage}%)</div>
        <div style="margin-top:10px"><strong>Certification Level:</strong>
        <span class="cert-badge">{results.certification_level}</span></div>
        <div style="margin-top:10px"><strong>Controls Assessed:</strong> {len(results.controls)} of 15</div>
        <div><strong>Critical Failures:</strong> {critical_failures}</div>
    </div>

    <h2>Automated Technical Controls (C01–C05)</h2>
    <table>
        <thead><tr><th>ID</th><th>Control</th><th>Score</th><th>Status</th><th>Details</th></tr></thead>
        <tbody>{auto_html}</tbody>
    </table>

    <h2>Administrative &amp; Physical Controls (C06–C15)</h2>
    <table>
        <thead><tr><th>ID</th><th>Control</th><th>Score</th><th>Status</th><th>Details</th></tr></thead>
        <tbody>{manual_html if manual_html else _no_manual}</tbody>
    </table>

    <h2>Recommendations</h2>
    <ul>{recommendations_html}</ul>

    <h2>Certification Thresholds</h2>
    <table>
        <thead><tr><th>Level</th><th>Min Score</th><th>Max Critical Failures</th><th>Validity</th></tr></thead>
        <tbody>
            <tr><td style="background:#FFD700;color:#333;font-weight:bold">GOLD</td>
              <td>&ge; 80% (&ge;96/120)</td><td>0</td><td>12 months</td></tr>
            <tr><td style="background:#C0C0C0;color:#333;font-weight:bold">SILVER</td>
              <td>&ge; 60% (&ge;72/120)</td><td>&le; 1</td><td>12 months</td></tr>
            <tr><td style="background:#CD7F32;color:white;font-weight:bold">BRONZE</td>
              <td>&ge; 40% (&ge;48/120)</td><td>&le; 2</td><td>6 months</td></tr>
            <tr><td style="background:#DC3545;color:white;font-weight:bold">NOT CERTIFIED</td>
              <td>&lt; 40%</td><td>&gt; 2</td><td>N/A</td></tr>
        </tbody>
    </table>

    <div class="footer">
        <p><strong>Zambia Digital Hygiene Certification Program v2.0</strong></p>
        <p>Aligned with NIST CSF | CIS Controls | ISO 27001 | Cyber Essentials</p>
        <p>Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
        """

    @staticmethod
    def _status_color(status: str) -> str:
        """Map status to Bootstrap badge color."""
        return {
            'PASS': 'success',
            'WARNING': 'warning',
            'FAIL': 'danger',
            'ERROR': 'danger',
            'NOT_ASSESSED': 'secondary',
        }.get(status, 'secondary')
