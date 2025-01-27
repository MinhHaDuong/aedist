import os
import sys


def get_sections(lines):
    """Split lines into sections based on table boundaries."""
    sections = []
    current = [lines[0]]
    in_table = lines[0].strip() == '<table>'
    
    print("\nStep 1: Sectioning the file...")
    section_count = 1
    
    for line in lines[1:]:
        boundary = False
        
        if in_table and line.strip() == '</table>':
            current.append(line)
            boundary = True
            in_table = False
        elif not in_table and line.strip() == '<table>':
            boundary = True
            in_table = True
        
        if boundary:
            section_type = '(Table)' if current[0].strip() == '<table>' else '(Non-table)'
            if any(line.strip().startswith('<!--') for line in current):
                section_type += ' with comments'
            print(f"  Section {section_count} {section_type}")
            sections.append(current)
            current = []
            section_count += 1
            
        if not boundary:
            current.append(line)
        elif line.strip() == '<table>':
            current.append(line)
            
    if current:
        section_type = '(Table)' if current[0].strip() == '<table>' else '(Non-table)'
        if any(line.strip().startswith('<!--') for line in current):
            section_type += ' with comments'
        print(f"  Section {section_count} {section_type}")
        sections.append(current)
        
    return sections


def normalize_header(header):
    """Normalize header by removing extra spaces after <br> tags."""
    return (header.replace('<br> ', '<br>')
                  .replace('<br/> ', '<br>')
                  .replace('<br/>','<br>')
                  .strip())


def get_table_headers(table_lines):
    """Extract headers from table lines."""
    headers = []
    for line in table_lines:
        if '<th>' in line:
            headers.extend(extract_th_content(line))
            if '</tr>' in line:
                break
    return [normalize_header(h) for h in headers]


def extract_th_content(line):
    """Extract content from <th> tags in a line."""
    headers = []
    start = 0
    while True:
        start = line.find('<th>', start)
        if start == -1:
            break
        end = line.find('</th>', start)
        if end == -1:
            break
        content = line[start + 4:end].strip()
        headers.append(content)
        start = end + 5
    return headers


def is_empty_or_comment(section):
    """Return True if section only contains empty lines or HTML comments."""
    for line in section:
        line = line.strip()
        if line and not line.startswith('<!--') and not line.endswith('-->'):
            return False
    return True


def analyze_merge_candidates(sections):
    """Analyze which tables can be merged based on matching headers."""
    print("\nStep 2: Analyzing merge candidates...")
    
    current_headers = None
    merge_groups = []
    current_group = []
    
    for i, section in enumerate(sections):
        if section[0].strip() == '<table>':
            headers = get_table_headers(section)
            print(f"\n  Table in section {i+1}")
            print(f"    Headers (normalized): {headers}")
            
            if not current_headers:
                print("    Starting new merge group")
                current_headers = headers
                current_group = [i]
            elif headers == current_headers:
                print("    Headers match previous table - can be merged")
                current_group.append(i)
            else:
                print("    Headers differ - starting new merge group")
                print(f"    Current headers: {current_headers}")
                print(f"    New headers: {headers}")
                if len(current_group) > 1:
                    merge_groups.append(current_group)
                current_headers = headers
                current_group = [i]
        else:
            if not is_empty_or_comment(section):
                print(f"\n  Non-empty, non-table section {i+1} - breaks merge group")
                if len(current_group) > 1:
                    merge_groups.append(current_group)
                current_headers = None
                current_group = []
            else:
                print(f"\n  Empty/comment section {i+1} - doesn't break merge group")
    
    if len(current_group) > 1:
        merge_groups.append(current_group)
    
    return merge_groups


def strip_head(table_lines):
    """Remove the initial <table> and the header row (if any) from a table.
    Args:
        table_lines: List of strings containing a table
    Returns:
        List of strings with first one removed and header row removed if it existed
    """
    lines = table_lines[1:]
    
    # Check if first row is a header
    for i, line in enumerate(lines):
        if '<th>' in line:
            # Skip until end of row
            while i < len(lines) and '</tr>' not in lines[i]:
                i += 1
            # Return rest of table
            return lines[i + 1:]
            
    # No header found, return everything after <table>
    return lines


def merge_two_tables(table1, between, table2):
    """Merge two tables, skipping the header row of the second table if it exists.
    Args:
        table1: List of strings containing first table
        between: List of strings containing content between tables
        table2: List of strings containing second table
    Returns:
        List of strings with merged table content
    """
    # Assert table1, table2 list of lines, starting with <table> ending with </table>
    assert isinstance(table1, list) and isinstance(table2, list), "Tables must be lists of strings"
    assert len(table1) >= 2 and len(table2) >= 2, "Tables must have at least opening and closing tags"
    assert table1[0].strip() == '<table>' and table2[0].strip() == '<table>', "Tables must start with <table>"
    assert table1[-1].strip() == '</table>' and table2[-1].strip() == '</table>', "Tables must end with </table>"
    
    return table1[:-1] + between + strip_head(table2)


def merge_tables_content(tables, all_sections):
    # tables is a list of indices (e.g. [2,4]) to be merged
    # We also handle potential comment lines in between them
    base = all_sections[tables[0]]
    for i in range(len(tables)-1):
        idxA = tables[i]
        idxB = tables[i+1]
        # Collect any purely comment/empty sections between these two tables
        comment_lines = []
        for mid in range(idxA+1, idxB):
            if is_empty_or_comment(all_sections[mid]):
                comment_lines.extend(all_sections[mid])
        base = merge_two_tables(base, comment_lines, all_sections[idxB])
    return base


def OLDperform_merges(sections, merge_groups):
    """Step 3: Perform merges."""
    print("\nStep 3: Performing merges...")
    final = []
    merged = set()
    
    # Process sections in order
    for i, section in enumerate(sections):
        if i in merged:
            continue
            
        start_of_group = False
        for group in merge_groups:
            if i == group[0]:  # If this is the start of a merge group
                print(f"  Merging tables from sections: {[i+1 for i in group]}")
                merged_table = merge_tables_content(group, sections)
                merged.update(group)
                final.append(merged_table)
                start_of_group = True
                break
                
        if not start_of_group and i not in merged:
            final.append(section)
    
    return final


def perform_merges(sections, merge_groups):
    """Step 3: Perform merges."""
    print("\nStep 3: Performing merges...")
    final = []
    merged = set()
    
    # First, collect all sections involved in merges, including intermediates
    for group in merge_groups:
        if len(group) > 1:
            # Include all sections from first to last in group
            merged.update(range(group[0], group[-1] + 1))
    
    # Process sections in order
    for i, section in enumerate(sections):
        if i in merged:
            # If this starts a merge group, add merged result
            for group in merge_groups:
                if i == group[0]:
                    print(f"  Merging tables from sections: {[i+1 for i in group]}")
                    merged_table = merge_tables_content(group, sections)
                    final.append(merged_table)
                    break
        else:
            # Section not involved in any merge
            final.append(section)
    
    return final


def merge_tables(file_path):
    if not file_path.endswith('.md'):
        print("Error: Input file must be a .md file.")
        return

    print(f"\nProcessing file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    sections = get_sections(lines)
    merge_groups = analyze_merge_candidates(sections)
    final_sections = perform_merges(sections, merge_groups)
    
    base_name = os.path.splitext(file_path)[0]
    output_file = f"{base_name}tablesmerged.md"
    with open(output_file, 'w', encoding='utf-8') as file:
        for section in final_sections:
            file.write(''.join(section))

    print(f"\nMerged tables written to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_tables.py <filename.md>")
        sys.exit(1)

    input_file = sys.argv[1]
    merge_tables(input_file)
