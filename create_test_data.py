import csv

def process_data(input_file, output_file, num_rows):
    entry_count = 0
    isolated_data = []
    
    # Track the number of each class we've collected
    count_zero = 0
    count_other = 0
    
    # 1. Read the CSV file
    with open(input_file, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        
        # 2 & 3. Count entries and isolate exactly num_rows of each
        for row in reader:
            entry_count += 1
            
            # Get the class value and strip any accidental whitespace
            current_class = str(row['class']).strip()
            
            # If it's class 0 and we still need more of them
            if current_class == '0' and count_zero < num_rows:
                isolated_data.append({
                    'text': row['text'] + '.',
                    'class': current_class
                })
                count_zero += 1
                
            # If it's NOT class 0 and we still need more of them
            elif current_class != '0' and count_other < num_rows:
                isolated_data.append({
                    'text': row['text'] + '.',
                    'class': current_class
                })
                count_other += 1
                
            # Stop reading the file early if we have all 600 rows
            if count_zero == num_rows and count_other == num_rows:
                break
                
    print(f"Total lines read to find the subset: {entry_count}")
    print(f"Saved {count_zero} rows of class '0'.")
    print(f"Saved {count_other} rows of other classes.")
    
    # 4. Save the isolated data to a new CSV file
    with open(output_file, mode='w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=['text', 'class'])
        
        writer.writeheader()
        writer.writerows(isolated_data)
        
    print(f"Isolated data saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    process_data("./training_data.csv", "test1.csv", 150)

    count = 0
    word_count = 0

    with open('test1.csv', mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            count+=1
            
            text_content = row['text']
            word_count += len(text_content.split())


    
    print(f"Number of rows in test1.csv: {count}")
    print(f"Total words across all isolated rows: {word_count}")
