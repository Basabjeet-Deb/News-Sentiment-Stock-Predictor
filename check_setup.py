"""
Setup Verification Script
Checks if all dependencies are installed and ready
"""

import sys

print("="*60)
print("CHECKING SETUP FOR NEWS SENTIMENT STOCK PREDICTOR")
print("="*60)

errors = []
warnings = []

# Check Python version
print("\n1. Python Version:")
print(f"   ✓ Python {sys.version.split()[0]}")
if sys.version_info < (3, 11):
    warnings.append("Python 3.11+ recommended")

# Check PySpark
print("\n2. PySpark:")
try:
    import pyspark
    print(f"   ✓ PySpark {pyspark.__version__}")
except ImportError:
    print("   ✗ PySpark NOT installed")
    errors.append("pip install pyspark")

# Check VADER
print("\n3. VADER Sentiment:")
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    print("   ✓ vaderSentiment installed")
except ImportError:
    print("   ✗ vaderSentiment NOT installed")
    errors.append("pip install vaderSentiment")

# Check Pandas
print("\n4. Pandas:")
try:
    import pandas as pd
    print(f"   ✓ Pandas {pd.__version__}")
except ImportError:
    print("   ✗ Pandas NOT installed")
    errors.append("pip install pandas")

# Check NumPy
print("\n5. NumPy:")
try:
    import numpy as np
    print(f"   ✓ NumPy {np.__version__}")
except ImportError:
    print("   ✗ NumPy NOT installed")
    errors.append("pip install numpy")

# Check Spark ML
print("\n6. Spark ML:")
try:
    from pyspark.ml.feature import Tokenizer
    from pyspark.ml.classification import LogisticRegression
    print("   ✓ Spark ML available")
except ImportError:
    print("   ✗ Spark ML NOT available")
    errors.append("Reinstall PySpark")

# Check data file
print("\n7. Data File:")
import os
data_path = "data/gdelt_english_news.csv"
if os.path.exists(data_path):
    size = os.path.getsize(data_path) / (1024 * 1024)
    print(f"   ✓ Data file exists ({size:.2f} MB)")
else:
    print("   ✗ Data file NOT found")
    warnings.append("Run fetch_data.ipynb to download data")

# Check Spark installation
print("\n8. Spark Installation:")
spark_home = os.environ.get('SPARK_HOME')
if spark_home:
    print(f"   ⚠ SPARK_HOME: {spark_home}")
    if not os.path.exists(spark_home):
        warnings.append(f"SPARK_HOME path doesn't exist: {spark_home}")
else:
    print("   ⚠ SPARK_HOME not set (will be set in notebook)")

# Summary
print("\n" + "="*60)
if errors:
    print("❌ SETUP INCOMPLETE - Missing dependencies:")
    for err in errors:
        print(f"   • {err}")
elif warnings:
    print("⚠️  SETUP OK - With warnings:")
    for warn in warnings:
        print(f"   • {warn}")
else:
    print("✅ SETUP COMPLETE - Ready to run!")

print("="*60)

if not errors:
    print("\nNext steps:")
    print("1. Start master: cluster/start_master.bat")
    print("2. Connect workers: cluster/worker.ipynb")
    print("3. Run classification: notebooks/classification.ipynb")
