import re

with open('app/services/advisory_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n').replace('\r', '\n')

lines = content.split('\n')
output = []
in_class = False
class_indent = 0

for i, line in enumerate(lines):
    stripped = line.lstrip()
    indent = len(line) - len(stripped)
    
    # Detect class definition
    if stripped.startswith('class AdvisoryService:'):
        in_class = True
        class_indent = indent  # Should be 0
        output.append(line)
        continue
    
    # Detect end of class (next module-level def or class)
    if in_class and stripped and indent == 0 and not stripped.startswith(' '):
        # We've left the class
        in_class = False
    
    # Fix indentation for class methods
    if in_class and stripped:
        # Method definitions should be at class_indent + 4
        if stripped.startswith('def ') or stripped.startswith('async def '):
            if indent != class_indent + 4:
                line = ' ' * (class_indent + 4) + stripped
        # Method body should be at class_indent + 8
        elif indent > 0 and indent < class_indent + 8:
            line = ' ' * (class_indent + 8) + stripped
    
    output.append(line)

with open('app/services/advisory_service.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('Fixed indentation')