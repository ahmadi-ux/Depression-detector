import csv
import json

def process_llm_data():
    # ---------------------------------------------------------
    # 1. Process the Labelled Data CSV files (Keep only: text, subreddit -> text, label)
    # ---------------------------------------------------------
    csv_input_files = ['Old/Labelled Data/file1.csv', 'Old/Labelled Data/file2.csv', 'Old/Labelled Data/file3.csv', 'Old/Labelled Data/file4.csv']
    
    for i, file_path in enumerate(csv_input_files):
        output_file = f'labelled_file{i+1}.csv'
        with open(file_path, mode='r', encoding='utf-8') as infile, \
             open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=['text', 'label'])
            writer.writeheader()
            
            for row in reader:
                if row.get('subreddit', '') == 'depression':
                    writer.writerow({
                        'text': row.get('selftext', ''), 
                        'label': row.get('subreddit', '')
                    })

    # ---------------------------------------------------------
    # 2. Process the DepressedEmo JSON file (Concatenate post + text, keep label)
    # ---------------------------------------------------------
    with open('Old/DepressedEmo.json', mode='r', encoding='utf-8') as infile, \
         open('depressed_emo_data.csv', mode='w', encoding='utf-8', newline='') as outfile:
        
        writer = csv.writer(outfile)
        writer.writerow(['text', 'label']) # Write the header
        
        # Read the file line-by-line to prevent "End of file expected" errors
        for line in infile:
            line = line.strip()
            if not line:
                continue # Skip empty lines
                
            item = json.loads(line) # Parse the individual line
            post_content = str(item.get('post', ''))
            text_content = str(item.get('text', ''))
            concatenated_text = f"{post_content} {text_content}".strip()
            
            writer.writerow([concatenated_text, 'depression'])

    # ---------------------------------------------------------
    # 3. Process the single CSV file (Filter by judgement > 0.97)
    # ---------------------------------------------------------
    with open('Old/Sentiments analysis.csv', mode='r', encoding='utf-8') as infile, \
         open('sentiment_filtered.csv', mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=['text', 'label'])
        writer.writeheader()
        
        for row in reader:
            try:
                judgement_val = float(row.get('judgment_confidence', 0.0))
                if judgement_val > 0.97:
                    original_class = str(row.get('class', '')).strip()
                    
                    # Remap the class values
                    if original_class == '0':
                        label = 'depression'
                    elif original_class in ['1', '2', '3', '4']:
                        label = 'not depression'
                    else:
                        continue # Skips rows if the class value is missing or unexpected
                        
                    writer.writerow({
                        'text': row.get('text', ''), 
                        'label': label
                    })
            except ValueError:
                # Silently skip rows where the judgement column is missing or not a number
                pass

if __name__ == "__main__":
    process_llm_data()