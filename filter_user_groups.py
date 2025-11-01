import csv
import os
from pathlib import Path

def filter_production_groups(input_file, output_file):
    """
    Filter user groups to keep only production entries.
    Removes entries containing development/testing environment indicators.
    """
    # Environment indicators to exclude
    exclusion_strings = ['DV', 'DEV', 'UAT', 'SB', 'DIT', 'PT', 'SIT', 'Dev', 'UA','QA','Test','Sandbox','SANDBOX','SandBox']
    
    filtered_data = []
    excluded_count = 0
    total_count = 0
    
    try:
        # Read the input CSV file
        with open(input_file, 'r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            
            for row in reader:
                total_count += 1
                # Clean the Name field from any BOM characters
                name = row.get('Name', '').lstrip('\ufeff')
                
                # Check if any exclusion string is in the name
                should_exclude = any(exclude_str in name for exclude_str in exclusion_strings)
                
                if not should_exclude:
                    filtered_data.append(row)
                else:
                    excluded_count += 1
                    print(f"Excluded: {name}")
        
        # Write the filtered data to output file
        if filtered_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                fieldnames = ['Name', 'Id']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write filtered rows
                writer.writerows(filtered_data)
            
            print(f"\nFiltering completed successfully!")
            print(f"Total entries processed: {total_count}")
            print(f"Entries excluded: {excluded_count}")
            print(f"Production entries saved: {len(filtered_data)}")
            print(f"Output file: {output_file}")
        else:
            print("No production entries found to save.")
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False
    
    return True

def main():
    """
    Main function to orchestrate the filtering process.
    """
    # Define file paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    samples_dir = project_root / 'samples'
    
    input_file = samples_dir / 'user_groups.csv'
    output_file = samples_dir / 'user_groups_prod.csv'
    
    # Ensure samples directory exists
    samples_dir.mkdir(exist_ok=True)
    
    print("Filtering user groups for production environment...")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print("=" * 60)
    
    # Filter the groups
    success = filter_production_groups(input_file, output_file)
    
    if success:
        print("=" * 60)
        print("Production groups filtering completed successfully!")
    else:
        print("Failed to filter production groups.")

if __name__ == "__main__":
    main()