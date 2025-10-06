"""
Script to prepare and ingest clause library into Bedrock Knowledge Base
"""

import json
import boto3
from pathlib import Path


def prepare_clauses_for_kb():
    """
    Prepare clause data for Bedrock Knowledge Base ingestion.
    Converts JSON to text format optimized for RAG.
    """
    
    clauses_dir = Path(__file__).parent.parent / 'clauses'
    output_dir = Path(__file__).parent.parent / 'processed'
    output_dir.mkdir(exist_ok=True)
    
    for clause_type_dir in clauses_dir.iterdir():
        if not clause_type_dir.is_dir():
            continue
        
        clause_type = clause_type_dir.name
        
        for json_file in clause_type_dir.glob('*.json'):
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            for clause in data.get('clauses', []):
                # Create text document optimized for semantic search
                text_content = f"""
Clause Type: {clause_type.upper()}
Industry: {clause.get('industry', 'General')}
Risk Level: {clause.get('risk_level', 'UNKNOWN')}

Clause Text:
{clause['text']}

Tags: {', '.join(clause.get('tags', []))}
Acceptance Rate: {clause.get('acceptance_rate', 'N/A')}%

Notes: {clause.get('notes', 'Standard clause')}
"""
                
                # Save as individual text file
                output_file = output_dir / f"{clause['id']}.txt"
                with open(output_file, 'w') as f:
                    f.write(text_content)
    
    print(f"✅ Processed clauses saved to {output_dir}")


if __name__ == '__main__':
    prepare_clauses_for_kb()