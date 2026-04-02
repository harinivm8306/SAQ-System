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
            continue
        elif line.startswith('>>>>>>> '):
            if in_other:
                in_other = False
            continue
        
        if in_head:
            pass # ignore HEAD side
        elif in_other:
            new_lines.append(line) # pick Milestone 3 side
        else:
            new_lines.append(line)
            
    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Resolved {filepath}")

for root, _, files in os.walk('.'):
    if 'venv' in root or '.git' in root:
        continue
    for f in files:
        if f.endswith(('.py', '.html', '.css', '.js', '.txt')):
            path = os.path.join(root, f)
            resolve_file(path)
