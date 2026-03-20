import os

def resolve_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return
        
    in_head = False
    in_other = False
    new_lines = []
    changed = False
    
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_head = True
            changed = True
            continue
        elif line.startswith('======='):
            if in_head:
                in_head = False
                in_other = True
            else:
                # Might be a regular line containing ======= ? rare, but let's be careful
                if in_other:
                    pass
                else:
                    new_lines.append(line)
            continue
        elif line.startswith('>>>>>>> '):
            if in_other:
                in_other = False
            else:
                new_lines.append(line)
            continue
        
        if in_head:
            new_lines.append(line)
        elif in_other:
            pass # ignore other side
        else:
            new_lines.append(line)
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Resolved {filepath}")

for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith(('.py', '.html', '.css', '.js', '.txt')):
            path = os.path.join(root, f)
            resolve_file(path)
