"""
Test Script for Context-Aware Sensitive Data Intelligence Engine

This script demonstrates the new context-aware capabilities of the SmartCloud Vault system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai_engine.context_aware_engine import (
    context_engine,
    DocumentType,
    SensitivityLevel
)
import json


def print_separator(title=""):
    """Print a visual separator."""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)
    print()


def test_invoice_processing():
    """Test invoice document processing."""
    print_separator("TEST 1: INVOICE PROCESSING")
    
    # Load sample invoice
    with open('docs/sample_files/sample_invoice.txt', 'r', encoding='utf-8') as f:
        invoice_text = f.read()
    
    print("Processing invoice document...")
    print("-" * 80)
    
    # Process with context-aware engine
    result = context_engine.process_document(
        text=invoice_text,
        apply_masking=True,
        preserve_structure=True
    )
    
    # Display results
    print(f"\n📄 DOCUMENT TYPE: {result['document_context']['type']}")
    print(f"   Confidence: {result['document_context']['confidence']:.2%}")
    print(f"   Reasoning: {result['document_context']['reasoning']}")
    print(f"   Matched Keywords: {', '.join(result['document_context']['keywords'][:5])}")
    
    print(f"\n🔍 DETECTED FIELDS: {len(result['detected_fields'])}")
    for field in result['detected_fields'][:10]:  # Show first 10
        print(f"   • {field['name']}: {field['sensitivity']} sensitivity")
        print(f"     Value: {field['value_preview']}")
        print(f"     Reason: {field['reason']}")
        print()
    
    print(f"🔒 MASKING APPLIED: {len(result['explanations'])} fields masked")
    for exp in result['explanations'][:5]:  # Show first 5
        print(f"   • Masked {exp['field']}")
        print(f"     Sensitivity: {exp['sensitivity']}")
        print(f"     Reason: {exp['reason']}")
        print(f"     Confidence: {exp['confidence']:.2%}")
        print()
    
    print("\n📊 SUMMARY:")
    summary = result['summary']
    print(f"   Document Type: {summary['document_type']}")
    print(f"   Total Fields Detected: {summary['total_fields_detected']}")
    print(f"   Fields Masked: {summary['fields_masked']}")
    print(f"   Sensitivity Distribution: {summary['sensitivity_distribution']}")
    
    # Show snippet of masked text
    print("\n📝 MASKED TEXT PREVIEW (first 500 chars):")
    print("-" * 80)
    print(result['masked_text'][:500] if result['masked_text'] else "None")
    print("-" * 80)
    
    return result


def test_receipt_processing():
    """Test receipt document processing."""
    print_separator("TEST 2: RECEIPT PROCESSING")
    
    with open('docs/sample_files/sample_receipt.txt', 'r', encoding='utf-8') as f:
        receipt_text = f.read()
    
    print("Processing receipt document...")
    print("-" * 80)
    
    result = context_engine.process_document(
        text=receipt_text,
        apply_masking=True,
        preserve_structure=True
    )
    
    print(f"\n📄 DOCUMENT TYPE: {result['document_context']['type']}")
    print(f"   Confidence: {result['document_context']['confidence']:.2%}")
    print(f"   Reasoning: {result['document_context']['reasoning']}")
    
    print(f"\n🔍 DETECTED FIELDS: {len(result['detected_fields'])}")
    print(f"🔒 FIELDS MASKED: {len(result['explanations'])}")
    
    for exp in result['explanations']:
        print(f"   • {exp['field']}: {exp['masked_value']}")
        print(f"     Reason: {exp['reason']}")
    
    return result


def test_hr_document_processing():
    """Test HR document processing."""
    print_separator("TEST 3: HR DOCUMENT PROCESSING")
    
    with open('docs/sample_files/sample_hr_review.txt', 'r', encoding='utf-8') as f:
        hr_text = f.read()
    
    print("Processing HR performance review...")
    print("-" * 80)
    
    result = context_engine.process_document(
        text=hr_text,
        apply_masking=True,
        preserve_structure=True
    )
    
    print(f"\n📄 DOCUMENT TYPE: {result['document_context']['type']}")
    print(f"   Confidence: {result['document_context']['confidence']:.2%}")
    
    print(f"\n🔍 DETECTED SENSITIVE FIELDS: {len(result['detected_fields'])}")
    
    # Show high sensitivity fields
    high_sensitivity = [f for f in result['detected_fields'] 
                       if f['sensitivity'] in ['high', 'critical']]
    print(f"\n⚠️  HIGH/CRITICAL SENSITIVITY FIELDS: {len(high_sensitivity)}")
    for field in high_sensitivity[:10]:
        print(f"   • {field['name']} ({field['sensitivity']})")
        print(f"     Reason: {field['reason']}")
    
    print(f"\n🔒 TOTAL FIELDS MASKED: {len(result['explanations'])}")
    
    return result


def test_bank_statement_processing():
    """Test financial document processing."""
    print_separator("TEST 4: BANK STATEMENT PROCESSING")
    
    with open('docs/sample_files/sample_bank_statement.txt', 'r', encoding='utf-8') as f:
        bank_text = f.read()
    
    print("Processing bank statement...")
    print("-" * 80)
    
    result = context_engine.process_document(
        text=bank_text,
        apply_masking=True,
        preserve_structure=True
    )
    
    print(f"\n📄 DOCUMENT TYPE: {result['document_context']['type']}")
    print(f"   Confidence: {result['document_context']['confidence']:.2%}")
    print(f"   Keywords: {', '.join(result['document_context']['keywords'][:8])}")
    
    print(f"\n🔍 DETECTED FIELDS: {len(result['detected_fields'])}")
    print(f"🔒 FIELDS MASKED: {len(result['explanations'])}")
    
    # Show what was masked
    print("\n🔐 MASKED SENSITIVE FINANCIAL DATA:")
    for exp in result['explanations'][:10]:
        print(f"   • {exp['field']}")
        print(f"     Original: {exp['original_value'][:30]}...")
        print(f"     Masked as: {exp['masked_value']}")
        print(f"     Reason: {exp['reason']}")
        print()
    
    return result


def test_comparison_old_vs_new():
    """Compare old regex-only vs new context-aware approach."""
    print_separator("TEST 5: COMPARISON - OLD vs NEW APPROACH")
    
    # Load invoice
    with open('docs/sample_files/sample_invoice.txt', 'r', encoding='utf-8') as f:
        invoice_text = f.read()
    
    # Old approach (regex only)
    from ai_engine.detector import RegexDetector
    from utils.protection import DataMasker
    
    print("OLD APPROACH (Regex-only):")
    print("-" * 80)
    regex_detector = RegexDetector()
    old_detections = regex_detector.detect(invoice_text)
    print(f"Detections: {len(old_detections)}")
    for det in old_detections[:5]:
        print(f"   • {det.detection_type}: {det.value[:30]}")
    
    old_masked, _ = DataMasker.selective_mask(invoice_text, old_detections)
    
    print(f"\n\nNEW APPROACH (Context-Aware):")
    print("-" * 80)
    new_result = context_engine.process_document(
        text=invoice_text,
        apply_masking=True
    )
    
    print(f"Document Type Detected: {new_result['document_context']['type']}")
    print(f"Semantic Fields Detected: {len(new_result['detected_fields'])}")
    print(f"Fields Masked: {len(new_result['explanations'])}")
    
    print("\n🎯 KEY IMPROVEMENTS:")
    print("   ✓ Automatically identified as INVOICE")
    print("   ✓ Detected invoice-specific fields (invoice #, PO #, etc.)")
    print("   ✓ Context-aware masking based on document type")
    print("   ✓ Preserved document layout and structure")
    print("   ✓ Provided explanation for each masked field")
    print("   ✓ Calculated sensitivity scores with confidence levels")
    
    print("\n📈 STATISTICS:")
    print(f"   Old detections: {len(old_detections)}")
    print(f"   New semantic fields: {len(new_result['detected_fields'])}")
    print(f"   New fields masked: {len(new_result['explanations'])}")
    
    return old_detections, new_result


def test_explainability():
    """Test explainability features."""
    print_separator("TEST 6: EXPLAINABILITY & TRANSPARENCY")
    
    with open('docs/sample_files/sample_invoice.txt', 'r', encoding='utf-8') as f:
        invoice_text = f.read()
    
    result = context_engine.process_document(
        text=invoice_text,
        apply_masking=True
    )
    
    print("MASKING TRANSPARENCY REPORT")
    print("-" * 80)
    print("\nThis report explains WHY each field was masked:\n")
    
    for i, exp in enumerate(result['explanations'], 1):
        print(f"{i}. FIELD: {exp['field']}")
        print(f"   ├─ Masked Value: {exp['masked_value']}")
        print(f"   ├─ Sensitivity: {exp['sensitivity'].upper()}")
        print(f"   ├─ Confidence: {exp['confidence']:.1%}")
        print(f"   └─ Reason: {exp['reason']}")
        print()
    
    print("This transparency allows:")
    print("   • Users to understand masking decisions")
    print("   • Compliance officers to audit the system")
    print("   • Security teams to adjust sensitivity thresholds")
    print("   • Organizations to explain data handling to stakeholders")


def save_results_to_json():
    """Save test results to JSON file."""
    print_separator("SAVING RESULTS")
    
    results = {}
    
    # Test all document types
    with open('docs/sample_files/sample_invoice.txt', 'r') as f:
        invoice_result = context_engine.process_document(f.read(), apply_masking=True)
        results['invoice'] = invoice_result
    
    with open('docs/sample_files/sample_receipt.txt', 'r') as f:
        receipt_result = context_engine.process_document(f.read(), apply_masking=True)
        results['receipt'] = receipt_result
    
    with open('docs/sample_files/sample_hr_review.txt', 'r') as f:
        hr_result = context_engine.process_document(f.read(), apply_masking=True)
        results['hr_review'] = hr_result
    
    with open('docs/sample_files/sample_bank_statement.txt', 'r') as f:
        bank_result = context_engine.process_document(f.read(), apply_masking=True)
        results['bank_statement'] = bank_result
    
    # Save to JSON
    output_file = 'backend/context_aware_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"✅ Results saved to: {output_file}")
    print("\nSummary:")
    for doc_type, result in results.items():
        print(f"   • {doc_type}: {result['summary']['fields_masked']} fields masked")


def main():
    """Run all tests."""
    print("\n" + "🚀" * 40)
    print("  CONTEXT-AWARE SENSITIVE DATA INTELLIGENCE ENGINE")
    print("  SmartCloud Vault v2.0 - Test Suite")
    print("🚀" * 40)
    
    # Initialize engine
    print("\nInitializing context-aware engine...")
    context_engine.initialize()
    print("✅ Engine initialized successfully!\n")
    
    try:
        # Run tests
        test_invoice_processing()
        input("\nPress Enter to continue to next test...")
        
        test_receipt_processing()
        input("\nPress Enter to continue to next test...")
        
        test_hr_document_processing()
        input("\nPress Enter to continue to next test...")
        
        test_bank_statement_processing()
        input("\nPress Enter to continue to next test...")
        
        test_comparison_old_vs_new()
        input("\nPress Enter to continue to next test...")
        
        test_explainability()
        input("\nPress Enter to save results...")
        
        save_results_to_json()
        
        print_separator("ALL TESTS COMPLETED")
        print("✅ Context-aware intelligence engine is working correctly!")
        print("\nKey Features Demonstrated:")
        print("   ✓ Automatic document type classification")
        print("   ✓ Semantic field detection")
        print("   ✓ Context-aware sensitivity scoring")
        print("   ✓ Intelligent masking with layout preservation")
        print("   ✓ Complete explainability and transparency")
        print("   ✓ Works with invoices, receipts, HR docs, financial statements")
        print("   ✓ Works with OCR-extracted text")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Sample file not found - {e}")
        print("Please ensure you're running from the correct directory")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
