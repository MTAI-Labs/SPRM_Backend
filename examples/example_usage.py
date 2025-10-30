"""
Example Usage of SPRM Classification System
============================================

This file demonstrates how to use the SPRM classifier directly from Python code.
"""

import sys
import os
# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import classify_text, train_model, get_classifier

# Example 1: Train the model (only need to do this once)
print("="*60)
print("EXAMPLE 1: Training the Model")
print("="*60)
print("Uncomment the lines below to train the model:")
print("# results = train_model()")
print("# print(f'Training completed with {results[\"accuracy\"]:.2f}% accuracy')")
print()

# Example 2: Load existing model and make predictions
print("="*60)
print("EXAMPLE 2: Making Predictions")
print("="*60)

# Test cases
test_cases = [
    "pegawai kerajaan menerima rasuah daripada syarikat swasta untuk meluluskan projek pembinaan",
    "permohonan permit ditolak kerana tidak lengkap dokumen",
    "ketua jabatan meminta wang untuk mempercepatkan kelulusan tender",
    "laporan aduan tentang perkhidmatan pelanggan yang lemah"
]

print("\nTesting corruption classification on sample cases:\n")

for i, case in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"Test Case {i}:")
    print(f"{'='*60}")
    print(f"Text: {case[:80]}...")

    try:
        result = classify_text(case)
        print(f"\n✅ Classification: {result['classification']}")
        print(f"✅ Confidence: {result['confidence']:.2f}%")
        print(f"✅ Corruption Probability: {result['corruption_probability']:.2f}%")
        print(f"✅ No Corruption Probability: {result['no_corruption_probability']:.2f}%")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("💡 Train the model first using: python main.py --mode train")
        break

print("\n" + "="*60)
print("EXAMPLE 3: Direct Classifier Access")
print("="*60)
print("\nYou can also access the classifier directly:")
print("""
# Get the classifier instance
clf = get_classifier()

# Make predictions
result = clf.predict("your text here")

# Train if needed
# results = clf.train()

# Save model
# clf.save("my_model.pkl")

# Load model
# clf.load_model()
# clf.load_classifier("my_model.pkl")
""")
