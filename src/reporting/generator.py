"""
Report Generation Module
Handles HTML, JSON, and CSV report generation for assessments
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import os


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
        return {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'business': {
                    'name': getattr(business_info, 'name', 'Unknown'),
                    'id': getattr(business_info, 'id', 'Unknown'),
                    'contact_person': getattr(business_info, 'contact_person', None),
                    'contact_email': getattr(business_info, 'contact_email', None),
                    'contact_phone': getattr(business_info, 'contact_phone', None),
                    'industry': getattr(business_info, 'industry', None),
                    'address': getattr(business_info, 'address', None),
                }
            },
            'summary': {
                'score': results.score,
                'total_possible': results.total_possible,
                'percentage': round(results.score / results.total_possible * 100, 1) if results.total_possible > 0 else 0,
                'certification_level': results.certification_level
            },
            'controls': {
                control_id: {
                    'name': control.name,
                    'score': control.score,
                    'weight': control.weight,
                    'status': control.status,
                    'details': control.details
                }
                for control_id, control in results.controls.items()
            },
            'recommendations': results.recommendations
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
            ['Digital Hygiene Assessment Report'],
            [],
            ['Business Information'],
            ['Name', getattr(business_info, 'name', 'Unknown')],
            ['ID', getattr(business_info, 'id', 'Unknown')],
            ['Industry', getattr(business_info, 'industry', 'Unknown')],
            ['Contact Person', getattr(business_info, 'contact_person', 'Unknown')],
            ['Contact Email', getattr(business_info, 'contact_email', 'Unknown')],
            ['Contact Phone', getattr(business_info, 'contact_phone', 'Unknown')],
            [],
            ['Assessment Summary'],
            ['Score', str(results.score)],
            ['Total Possible', str(results.total_possible)],
            ['Percentage', f"{round(results.score / results.total_possible * 100, 1)}%"],
            ['Certification Level', results.certification_level],
            [],
            ['Control Results'],
            ['Control Name', 'Score', 'Weight', 'Status', 'Details']
        ]
        
        for control_id, control in results.controls.items():
            rows.append([
                control.name,
                str(control.score),
                str(control.weight),
                control.status,
                control.details
            ])
        
        rows.extend([
            [],
            ['Recommendations']
        ])
        
        for rec in results.recommendations:
            rows.append([rec])
        
        return rows

    def generate_pdf_report(
        self, results: Any, business_info: Any, report_name: str
    ) -> str:
        """Generate PDF report.
        
        Note: PDF generation requires pdfkit and wkhtmltopdf. Falls back to HTML.
        
        Args:
            results: Assessment results object
            business_info: Business information object
            report_name: Base name for the report file
            
        Returns:
            Path to generated PDF file (or HTML if PDF not available)
        """
        try:
            import pdfkit
            html_path = self.generate_html_report(results, business_info, report_name)
            pdf_path = str(self.output_dir / f"{report_name}.pdf")
            
            pdfkit.from_file(html_path, pdf_path)
            return pdf_path
        except ImportError:
            # Fall back to HTML if pdfkit not available
            return self.generate_html_report(results, business_info, report_name)
        except Exception:
            # Fall back to HTML on any PDF generation error
            return self.generate_html_report(results, business_info, report_name)

    def _build_html(self, results: Any, business_info: Any) -> str:
        """Build HTML report content."""
        percentage = round(results.score / results.total_possible * 100, 1) if results.total_possible > 0 else 0
        
        controls_html = ''.join([
            f'''
            <tr>
                <td>{control.name}</td>
                <td>{control.score}/{control.weight}</td>
                <td><span class="badge bg-{self._status_color(control.status)}">{control.status}</span></td>
                <td>{control.details}</td>
            </tr>
            '''
            for control in results.controls.values()
        ])
        
        recommendations_html = ''.join([
            f'<li>{rec}</li>'
            for rec in results.recommendations
        ])
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Digital Hygiene Assessment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        h1 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        h2 {{ color: #764ba2; margin-top: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .score {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #667eea; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .badge {{ padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }}
        .bg-success {{ background-color: #28a745; }}
        .bg-warning {{ background-color: #ffc107; color: #333; }}
        .bg-danger {{ background-color: #dc3545; }}
        ul {{ line-height: 1.8; }}
        .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>Digital Hygiene Assessment Report</h1>
    
    <h2>Business Information</h2>
    <p><strong>Name:</strong> {getattr(business_info, 'name', 'Unknown')}</p>
    <p><strong>ID:</strong> {getattr(business_info, 'id', 'Unknown')}</p>
    <p><strong>Industry:</strong> {getattr(business_info, 'industry', 'Unknown')}</p>
    <p><strong>Contact Person:</strong> {getattr(business_info, 'contact_person', 'Unknown')}</p>
    <p><strong>Contact Email:</strong> {getattr(business_info, 'contact_email', 'Unknown')}</p>
    
    <h2>Assessment Summary</h2>
    <div class="summary">
        <div><strong>Overall Score:</strong> <span class="score">{results.score}/{results.total_possible}</span></div>
        <div><strong>Percentage:</strong> {percentage}%</div>
        <div><strong>Certification Level:</strong> <span class="score">{results.certification_level}</span></div>
    </div>
    
    <h2>Control Assessment Details</h2>
    <table>
        <thead>
            <tr>
                <th>Control</th>
                <th>Score</th>
                <th>Status</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
            {controls_html}
        </tbody>
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        {recommendations_html}
    </ul>
    
    <div class="footer">
        <p>Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Zambia Digital Hygiene Assessment Tool v2.0</p>
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
            'ERROR': 'danger'
        }.get(status, 'secondary')
