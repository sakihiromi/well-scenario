
import app
import io
import csv
import json
import os

def test_csv_generation():
    app.app.testing = True
    client = app.app.test_client()
    
    # Use an existing file in data/outputs
    filename = "20251214_173247_トライアル_飲み会ズレ.json"
    
    print(f"Testing CSV download for {filename}...")
    response = client.get(f'/api/output/{filename}/csv')
    
    if response.status_code != 200:
        print(f"FAILED: Status code {response.status_code}")
        print(response.get_json())
        return

    content = response.data.decode('utf-8-sig')
    print("CSV Content Start:")
    print(content[:200])
    
    # Parse CSV to verify structure
    f = io.StringIO(content)
    reader = csv.reader(f)
    header = next(reader)
    
    expected_header = ['Speaker', 'Content', '威圧度', '逸脱度', '発言無効度', '偏り度']
    if header == expected_header:
        print("SUCCESS: Header matches.")
    else:
        print(f"FAILED: Header mismatch. Got {header}")
        
    # Check first row
    first_row = next(reader)
    print(f"First row: {first_row}")
    
    if len(first_row) == 6 and first_row[2] == '' and first_row[3] == '' and first_row[4] == '' and first_row[5] == '':
        print("SUCCESS: Metric columns are empty.")
    else:
        print("FAILED: Metric columns are not empty or row length is wrong.")

if __name__ == "__main__":
    test_csv_generation()
