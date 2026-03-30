"""
Results Parser: Converts testing .txt files into user-friendly CSV format

This script reads the raw test result .txt files and converts them into:
1. A summary CSV with model metrics (metrics_summary.csv)
2. An errors CSV with detailed error analysis (errors_detailed.csv)
"""

import os
import csv
import re
from pathlib import Path
from datetime import datetime


class ResultsParser:
    """Parse testing results from .txt files and export to CSV"""
    
    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.metrics_data = []
        self.errors_data = []
    
    def parse_results_file(self, filepath):
        """Parse a single results .txt file"""
        print(f"Parsing: {filepath.name}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by lines
            lines = content.strip().split('\n')
            if not lines:
                print(f"  ❌ Empty file")
                return
            
            # Parse first line with metrics
            metrics_line = lines[0]
            metrics = self._parse_metrics_line(metrics_line)
            
            if metrics:
                self.metrics_data.append(metrics)
                print(f"  ✓ Metrics extracted: {metrics['model']} | Accuracy: {metrics['accuracy']:.2%}")
            
            # Parse error entries (remaining lines)
            error_entries = self._parse_error_lines(lines[1:], metrics)
            self.errors_data.extend(error_entries)
            print(f"  ✓ Found {len(error_entries)} error entries")
        
        except Exception as e:
            print(f"  ❌ Error parsing file: {str(e)}")
    
    def _parse_metrics_line(self, line):
        """Extract metrics from the first line"""
        metrics = {}
        
        # Extract each metric using regex
        patterns = {
            'true_positives': r'TP:\s*(\d+)',
            'false_positives': r'FP:\s*(\d+)',
            'true_negatives': r'TN:\s*(\d+)',
            'false_negatives': r'FN:\s*(\d+)',
            'errors': r'ERROR:\s*(\d+)',
            'precision': r'Precision:\s*([\d.]+)',
            'recall': r'Recall:\s*([\d.]+)',
            'accuracy': r'Accuracy:\s*([\d.]+)',
            'f1_score': r'F1 Score:\s*([\d.]+)',
            'model': r'Model:\s*([^\s]+)',
            'prompt': r'Prompt:\s*(.+)$'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                value = match.group(1)
                # Convert to float for numeric values
                if key not in ['model', 'prompt']:
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
                else:
                    metrics[key] = value
        
        # Add timestamp from filename if available
        metrics['timestamp'] = datetime.now().isoformat()
        return metrics if metrics else None
    
    def _parse_error_lines(self, lines, metrics):
        """Extract individual error entries"""
        errors = []
        text_buffer = ""
        current_error = None
        
        for line in lines:
            # Check if this is a new error entry (starts with FP or FN)
            if line.strip().startswith(('FP', 'FN')):
                # Save previous error if exists
                if current_error:
                    current_error['text'] = text_buffer.strip()
                    errors.append(current_error)
                    text_buffer = ""
                
                # Parse new error entry
                match = re.match(r'(FP|FN)\s*:\s*Label:\s*(\d+)\s*\|\s*Predicted:\s*([^\|]+)\s*\|\s*Text:\s*(.*)$', line)
                if match:
                    error_type, label, predicted, text = match.groups()
                    current_error = {
                        'error_type': error_type,
                        'label': label,
                        'predicted': predicted.strip(),
                        'model': metrics.get('model', 'Unknown'),
                        'prompt': metrics.get('prompt', 'Unknown')
                    }
                    text_buffer = text.strip()
            elif current_error:
                # Continuation of previous text
                text_buffer += " " + line.strip()
        
        # Don't forget the last error
        if current_error:
            current_error['text'] = text_buffer.strip()
            errors.append(current_error)
        
        return errors
    
    def export_metrics_csv(self, output_path):
        """Export metrics summary to CSV"""
        if not self.metrics_data:
            print("No metrics data to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define field order for better readability
        fieldnames = [
            'model', 'prompt', 'accuracy', 'precision', 'recall', 'f1_score',
            'true_positives', 'true_negatives', 'false_positives', 'false_negatives',
            'errors', 'timestamp'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in self.metrics_data:
                writer.writerow(row)
        
        print(f"\n✓ Metrics exported to: {output_path}")
        print(f"  Rows: {len(self.metrics_data)}")
    
    def export_errors_csv(self, output_path):
        """Export detailed errors to CSV"""
        if not self.errors_data:
            print("No errors data to export")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = ['error_type', 'model', 'prompt', 'label', 'predicted', 'text']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in self.errors_data:
                writer.writerow(row)
        
        print(f"✓ Errors exported to: {output_path}")
        print(f"  Rows: {len(self.errors_data)}")
    
    def process_all_files(self):
        """Process all .txt files in the results directory"""
        txt_files = list(self.results_dir.glob('*.txt'))
        
        if not txt_files:
            print(f"No .txt files found in {self.results_dir}")
            return
        
        print(f"Found {len(txt_files)} test result files\n")
        
        for filepath in txt_files:
            self.parse_results_file(filepath)
        
        print(f"\n{'='*60}")
        print(f"Total files processed: {len(txt_files)}")
        print(f"Total metrics collected: {len(self.metrics_data)}")
        print(f"Total errors collected: {len(self.errors_data)}")
        print(f"{'='*60}\n")


def main():
    """Main entry point"""
    # Define paths
    script_dir = Path(__file__).parent
    results_dir = script_dir / 'results'
    output_dir = results_dir / 'parsed'
    
    # Check if results directory exists
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Parse all results
    parser = ResultsParser(results_dir)
    parser.process_all_files()
    
    # Export to CSV
    if parser.metrics_data or parser.errors_data:
        metrics_output = output_dir / 'metrics_summary.csv'
        errors_output = output_dir / 'errors_detailed.csv'
        
        parser.export_metrics_csv(metrics_output)
        parser.export_errors_csv(errors_output)
        
        print(f"All files exported to: {output_dir}")
    else:
        print("No data to export")


if __name__ == '__main__':
    main()
